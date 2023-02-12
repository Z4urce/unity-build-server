from flask import Flask, render_template, send_file, send_from_directory, request
import subprocess
import math
import datetime
import threading
import os
import utils
import db_manager
import cs_manager
import webhook_manager

app = Flask(__name__)
terminal_app = 'pwsh' if os.name is 'posix' else 'powershell'
cs_manager.terminal_app = terminal_app


@app.route('/')
def main():
    projects = utils.get_project_names()
    sys_info = utils.get_system_info()
    return render_template('dashboard.html', projects=projects, sys_info=sys_info)


@app.route('/project/<project_id>')
def project_home(project_id):
    configs = utils.read_configs(project_id)
    build_data = db_manager.sql_fetch_last_builds_by_project_with_results(project_id, 6)
    calculate_progress_per_config(configs)
    builds = utils.process_build_data(build_data)
    return render_template('index.html', configs=configs, builds=builds)


@app.route('/debug_project_view')
def debug_project_view():
    configs = utils.read_configs('SimpleUnityProject')
    build_data = db_manager.sql_fetch_last_builds_by_project_with_results('SimpleUnityProject', 6)
    calculate_progress_per_config(configs)
    builds = utils.process_build_data(build_data)
    configs[0]['progress'] = 56
    configs[0]['buildInProgress'] = True
    configs[0]['progressColor'] = 'yellow'
    configs[0]['lastBuildId'] = builds[0][0]
    return render_template('index.html', configs=configs, builds=builds)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/init')
def clear_cache():
    utils.clear_cache()
    return "Cache cleared"


@app.route('/log/<build_name>')
def log_page(build_name):
    log = utils.get_log(build_name)
    return render_template('log_layout.html', text=log)


@app.route('/changelog/<project_id_raw>/<build_number>')
def change_log_page(project_id_raw, build_number):
    project_id = project_id_raw.replace("_", " ")
    log = db_manager.sql_fetch_build_change_log(build_number, project_id)
    result = "Changes in build " + project_id + " " + build_number + "\n\n" + log
    return render_template('log_layout.html', text=result)


@app.route('/config/<project_id_raw>')
def config_page(project_id_raw):
    project_id = project_id_raw.replace("_", " ")
    text = utils.get_raw_project_config(project_id)
    return render_template('config_editor.html', text=text, project=project_id)


@app.route('/config/<project_id_raw>/save')
def save_config_page(project_id_raw):
    project_id = project_id_raw.replace("_", " ")
    if utils.try_overwrite_project_config_file(project_id, request.args['configs']):
        return "SUCCESS: Configuration file has been updated."
    return "FAILED: The specified input was not in valid JSON format"


@app.route('/stop/<project_id_raw>/<config_id_raw>')
def stop_build(project_id_raw, config_id_raw):
    project_id = project_id_raw.replace("_", " ")
    config_id = config_id_raw.replace("_", " ")

    terminate_build_process(project_id, config_id)
    return '', 204


@app.route('/build/<project_id_raw>/<config_id_raw>')
def run_build(project_id_raw, config_id_raw):
    project_id = project_id_raw.replace("_", " ")
    config_id = config_id_raw.replace("_", " ")
    utils.clear_cache()
    config = utils.get_config(project_id, config_id)

    if config is None:
        return "Error: No such config as " + config_id + " in " + project_id

    if not is_config_build_in_progress(project_id, config_id):
        execute_build(config, request.args)

    return '', 204


def execute_build(config, override_args):
    change_log = cs_manager.get_cached_project_changes(config['projectPath'])
    update_project_workspace(config)
    utils.clear_cache()

    config = utils.get_config(config['project'], config['name'])
    utils.override_config(config, override_args)

    print(config)

    build_number = db_manager.sql_get_next_build_number(config['project'])
    build_name = utils.assemble_build_name(config, build_number)
    build_path = config['buildDirectory'] + '/' + build_name
    log_path = "logs/" + build_name + ".log"

    args = utils.get_args_by_config(config)
    unity_args = [utils.get_unity_path(config['engineVersion']), '-batchmode', '-logFile', log_path, '-buildPath',
                  build_path, '-buildNumber', str(build_number), *args]
    unity_process = subprocess.Popen(unity_args)

    def on_finish():
        result = db_manager.sql_fetch_result(config['project'], build_number)
        if result is not None and result[3] == utils.BuildResult.CANCELLED:
            print("Build " + build_number + " has been cancelled. Aborting execution of post build scripts")
            return

        db_manager.sql_update_result(
            build_number, config['project'], datetime.datetime.now(), utils.BuildResult.POSTPROCESSING)
        run_post_build_script(config)
        result_code = utils.evaluate_build_result(build_name)
        send_build_status_web_message(config, '>Build ' + result_code.name.lower() + ': ' + build_name)
        db_manager.sql_update_result(build_number, config['project'], datetime.datetime.now(), result_code)
        process_xcode(config, result_code, build_name, build_number)

    utils.add_on_finish_listener_to_process(unity_process, on_finish)
    db_manager.sql_insert_build(build_number, config['project'], config['name'], build_name, datetime.datetime.now(),
                                unity_process.pid)

    # Change log handling
    db_manager.sql_insert_change_log(build_number, config['project'], '\n'.join(change_log))
    send_change_log_web_message(config, '>' + build_name + '\n' + '\n'.join(change_log))

    cs_manager.query_project_changes(config['projectPath'], forced=True)
    send_build_status_web_message(config, '>Build started: ' + build_name)


def run_post_build_script(config):
    if 'postBuildScript' in config and config['postBuildScript']:
        subprocess.run([terminal_app, config['postBuildScript']])


def send_build_status_web_message(config, text):
    print('Web message: ' + text)
    try_send_web_message('webhookUrl', config, text)


def send_change_log_web_message(config, log):
    print('Sending change log')
    try_send_web_message('changelogUrl', config, log)


def try_send_web_message(key, config, text):
    if key in config and config[key]:
        webhook_manager.send_message(config[key], text)


def process_xcode(config, result_code, build_name, build_number):
    if result_code == result_code.SUCCESSFUL and 'xcodeScript' in config and config['buildTarget'] == 'iOS':
        send_build_status_web_message(config, '>Build' + build_name + " was sent to xcode for further processing")
        db_manager.sql_update_result(build_number, config['project'], datetime.datetime.now(),
                                     utils.BuildResult.POSTPROCESSING)

        try:
            log_file = open("logs/" + build_name + ".log", "a")
        except:
            log_file = None

        try:
            subprocess.run([terminal_app, config['xcodeScript'], config['buildDirectory'] + '/' + build_name],
                           stdout=log_file, check=True)
        except subprocess.CalledProcessError:
            send_build_status_web_message(config, '>Build ' + build_name + " xcode post process *FAILED*")
            db_manager.sql_update_result(build_number, config['project'], datetime.datetime.now(),
                                         utils.BuildResult.FAILED)
        else:
            send_build_status_web_message(config, '>Build' + build_name + " xcode post process finished")
            db_manager.sql_update_result(build_number, config['project'], datetime.datetime.now(),
                                         utils.BuildResult.SUCCESSFUL)

        if log_file is not None:
            log_file.close()


def update_project_workspace(config):
    subprocess.run([terminal_app, config['updateProjectScript'], config['projectPath']])


def query_project_changes_all():
    paths = utils.get_unique_project_paths()
    for path in paths:
        cs_manager.query_project_changes(path)


def calculate_progress_per_config(configs):
    progress_strings = utils.get_progress_strings()
    word_value = 100 / len(progress_strings)
    for config in configs:
        config['progress'] = 0
        last_build = db_manager.sql_fetch_last_build_by_config(config['project'], config['name'])

        if last_build is None:
            continue
        log = utils.get_log(last_build[3])
        for word in progress_strings:
            if word in log:
                config['progress'] = 100 - (word_value * progress_strings.index(word))
                break

        config['lastBuildId'] = last_build[0]
        config['progress'] = math.ceil(config['progress'])
        config['buildInProgress'] = is_config_build_in_progress(config['project'], config['name'])
        config['progressColor'] = utils.get_progress_color(config['progress'], config['buildInProgress'])
        config['newChanges'] = cs_manager.get_cached_project_changes(config['projectPath'])


def is_config_build_in_progress(project_id, config_name: str) -> bool:
    last_build = db_manager.sql_fetch_last_build_by_config(project_id, config_name)
    if last_build is None:
        return False
    pid = last_build[5]
    return utils.is_pid_unity_process(pid)


def terminate_build_process(project_id, config_name: str):
    last_build = db_manager.sql_fetch_last_build_by_config(project_id, config_name)
    if last_build is None:
        return
    pid = last_build[5]
    if utils.kill_unity_process(pid):
        db_manager.sql_update_result(last_build[0], last_build[1], datetime.datetime.now(), utils.BuildResult.CANCELLED)
        return True
    return False


stopFlag = threading.Event()
thread = utils.PerpetualTimer(stopFlag, query_project_changes_all)
thread.daemon = True
thread.start()

db_manager.sql_create_builds_table()
print("build_server initialized.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
    stopFlag.set()
