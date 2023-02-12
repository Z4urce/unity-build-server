import subprocess
import threading

cached_project_changes = {}
lock = threading.Lock()
terminal_app = 'powershell'
print("cs_manager initialized.")


def get_cached_project_changes(project_path):
    if project_path not in cached_project_changes:
        query_project_changes(project_path)

    return cached_project_changes[project_path]


def query_project_changes(project_path: str, forced: bool = False):
    lock.acquire()

    if not forced and project_path in cached_project_changes:
        if len(cached_project_changes[project_path]) > 100:
            cached_project_changes[project_path] = ['There are more than 100 commits since the last build']

    try:
        output = subprocess.run([terminal_app, 'scripts/get_changes.ps1', project_path],
                                capture_output=True, text=True, encoding="utf8").stdout
        cached_project_changes[project_path] = [x for x in output.split("\n") if x]
    except UnicodeDecodeError:
        cached_project_changes[project_path] = ['Error: Can not decode one or more characters in commit data']
    except:
        cached_project_changes[project_path] = ['Can not read commit data']
    finally:
        lock.release()
