import json
import threading
import copy

cached_json_files = {}
lock = threading.RLock()
print("file_manager initialized.")


def clear_cache():
    lock.acquire()
    cached_json_files.clear()
    lock.release()


def read_file(path):
    file = open(path, "r")
    content_raw = file.read()
    file.close()
    return content_raw


def overwrite_file(path, content):
    file = open(path, "w")
    file.write(content)
    file.close()
    if path in cached_json_files:
        cached_json_files.pop(path)


def parse_json_file(path):
    if path in cached_json_files:
        result = copy.copy(cached_json_files[path])
        return result

    result = json.loads(read_file(path))

    lock.acquire()
    cached_json_files[path] = result
    lock.release()
    return result


def parse_progress_strings():
    return parse_json_file("config/build_milestones.cfg")


def parse_build_failed_conditions():
    return parse_json_file("config/build_fail_conditions.cfg")


def parse_projects_config():
    return parse_json_file("config/projects.cfg")


def parse_project_local_overrides(project_id):
    return parse_json_file("config/" + project_id + ".project")


def raw_project_local_overrides(project_id):
    return read_file("config/" + project_id + ".project")


def parse_project_remote_override(path):
    b_settings_path = (path + "/" + "BuildSettings.txt")
    try:
        return parse_json_file(b_settings_path)
    except IOError:
        # print('Project specific build settings file does not exist in path=' + b_settings_path)
        return None


def try_overwrite_project_config_file(project_id, content) -> bool:
    try:
        result = json.loads(content)
    except:
        return False
    finally:
        overwrite_file("config/" + project_id + ".project", json.dumps(result, indent=4, sort_keys=True))
        return True
