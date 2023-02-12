from enum import IntEnum
import threading
import psutil
import file_manager
import datetime
import os
from stat import S_ISREG, ST_CTIME, ST_MODE


class BuildResult(IntEnum):
    UNKNOWN = 0
    SUCCESSFUL = 1
    FAILED = 2
    INTERRUPTED = 3
    POSTPROCESSING = 4
    CANCELLED = 5


class PerpetualTimer(threading.Thread):
    def __init__(self, event, hFunction):
        threading.Thread.__init__(self)
        self.stopped = event
        self.hFunction = hFunction

    def run(self):
        while not self.stopped.wait(20):
            print("Thread task started")
            self.hFunction()
            print("Thread task completed")


def get_unity_path(version: str) -> str:
    if os.name is 'posix':
        return '/Applications/Unity/Hub/Editor/' + version + '/Unity.app/Contents/MacOS/Unity'
    else:
        return 'C:/Program Files/Unity/Hub/Editor/' + version + '/Editor/Unity.exe'


def get_progress_color(progress: int, is_builder_active: bool) -> str:
    if progress >= 100:
        return "cyan"
    if is_builder_active:
        return "yellow"
    return "red"


def get_log(build_name):
    try:
        log = file_manager.read_file("logs/" + build_name + ".log")
        return log
    except OSError as e:
        return ""


def get_raw_project_config(project_id):
    return file_manager.raw_project_local_overrides(project_id)


def get_progress_strings():
    return file_manager.parse_progress_strings()


def get_build_failed_conditions():
    return file_manager.parse_build_failed_conditions()


def clear_cache():
    file_manager.clear_cache()


def read_configs(project_id):
    projects = file_manager.parse_projects_config()

    project_base_config = next((x for x in projects if x["project"] == project_id), None)

    if project_base_config is None:
        print("Could not find project " + project_id + " in the projects.cfg file")
        return None

    configs = file_manager.parse_project_local_overrides(project_id)

    for config in configs:
        for setting in project_base_config:
            if setting not in config:
                config[setting] = project_base_config[setting]

        if "projectPath" not in config:
            print("projectPath key not found in configs in project: " + project_id)
            continue

        build_settings = file_manager.parse_project_remote_override(config["projectPath"])
        override_config(config, build_settings)

    return configs


def try_overwrite_project_config_file(project_id, content) -> bool:
    return file_manager.try_overwrite_project_config_file(project_id, content)


def get_project_names() -> list:
    projects = file_manager.parse_projects_config()
    elements = []
    for project in projects:
        elements.append(project["project"])
    return list(set(elements))


def get_unique_project_paths() -> list:
    result = []
    projects = get_project_names()
    for project in projects:
        project_configs = read_configs(project)
        for config in project_configs:
            result.append(config["projectPath"])

    return list(set(result))


def get_config(project_id, name):
    configs = read_configs(project_id)
    for config in configs:
        if config['name'] == name:
            return config


def get_args_by_config(config):
    args = []
    for key, val in config.items():
        args.append("-" + key)
        args.append(val)
    return args


def add_on_finish_listener_to_process(target_process, on_finish):
    def run_in_thread(on_finish, target_process):
        print('New waiter thread created for Unity process')
        target_process.wait()
        print('Unity process has been terminated. Calling postBuildScript')
        on_finish()
        return

    thread = threading.Thread(target=run_in_thread, args=(on_finish, target_process))
    thread.start()
    # returns immediately after the thread starts
    return thread


def is_pid_unity_process(pid):
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False

    return process.name().startswith('Unity')


def kill_unity_process(pid):
    try:
        process = psutil.Process(pid)
        if process.name().startswith('Unity'):
            print('Process ' + str(pid) + ' has been successfully terminated')
            process.terminate()
            return True
        print('Process ' + str(pid) + ' is not a Unity executable. Will not kill')
    except psutil.NoSuchProcess:
        print('Tried to kill ' + str(pid) + ' but not such process has been found')
        return False


def get_system_info():
    result = {
        'CPU': int(psutil.cpu_percent()),
        'RAM': int(psutil.virtual_memory()[2]),
        'HDD': int(psutil.disk_usage('/')[3])}
    return result


def override_config(config, override_args):
    if override_args is not None:
        for x in override_args:
            config[x] = override_args[x]


def assemble_build_name(config, build_number):
    full_version = config['projectVersion'] + "." + str(build_number)
    return config['project'] + "_" + config['name'].replace(" ", "_") + "_" + full_version


def evaluate_build_result(build_name):
    fail_conditions = get_build_failed_conditions()
    success_condition = "Build Report"
    log = get_log(build_name)

    if success_condition in log:
        return BuildResult.SUCCESSFUL
    for fail_condition in fail_conditions:
        if fail_condition in log:
            return BuildResult.FAILED
    return BuildResult.UNKNOWN


def process_build_data(data):
    date_format = '%Y-%m-%d %H:%M:%S.%f'
    builds = []

    for columns in data:
        interrupted = columns[8] is None
        start_time = datetime.datetime.strptime(columns[4], date_format)
        end_time = datetime.datetime.strptime(columns[8], date_format) if not interrupted else datetime.datetime.now()
        length = end_time - start_time

        build = list(columns)
        build[8] = str(length) if not interrupted else ''
        build[9] = BuildResult(BuildResult.UNKNOWN if columns[9] is None else columns[9]).name.lower()
        builds.append(build)
    return builds


def list_directory(dirpath):
    result = []

    entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
    entries = ((os.stat(path), path) for path in entries)

    entries = ((stat[ST_CTIME], path)
               for stat, path in entries if S_ISREG(stat[ST_MODE]))

    count = 0
    for cdate, path in sorted(entries, reverse=True):
        result.append(os.path.basename(path))
        count += 1
        if count > 20:
            break

    return result
