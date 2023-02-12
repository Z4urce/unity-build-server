import threading
import sqlite3
from sqlite3.dbapi2 import Connection

db: Connection = sqlite3.connect('builds.db', check_same_thread=False)
write_lock = threading.RLock()
print("db_manager initialized.")


def sql_create_builds_table():
    db.execute(
        "CREATE TABLE IF NOT EXISTS builds (buildNumber int, project text, configName text, buildName text, "
        "startDate text, processId int, PRIMARY KEY(buildNumber, project))")
    db.execute(
        "CREATE TABLE IF NOT EXISTS results (buildNumber int, project text, endDate text, resultCode int, "
        "PRIMARY KEY(buildNumber, project))")
    db.execute(
        "CREATE TABLE IF NOT EXISTS build_change_logs (buildNumber int, project text, log text, "
        "PRIMARY KEY(buildNumber, project))")


def sql_fetch_last_builds_by_project_with_results(project, limit):
    return db.execute("SELECT * FROM builds "
                      "LEFT JOIN results ON results.buildNumber = builds.buildNumber "
                      "AND results.project = builds.project "
                      "WHERE builds.project=? "
                      "ORDER BY builds.buildNumber DESC LIMIT ? ", (project, str(limit)))


def sql_fetch_last_builds_by_project(project, limit):
    return db.execute("SELECT * FROM builds WHERE project=? ORDER BY buildNumber DESC LIMIT ?", (project, str(limit)))


def sql_fetch_last_build_by_config(project_id, config_name):
    return db.execute("SELECT * FROM builds WHERE project=? AND configName=? ORDER BY buildNumber DESC LIMIT 1",
                      (project_id, config_name)).fetchone()


def sql_fetch_result(project_id, build_number):
    return db.execute("SELECT * FROM results WHERE project=? AND buildNumber=? LIMIT 1",
                      (project_id, build_number)).fetchone()


def sql_fetch_build_change_log(build_number: int, project: str) -> str:
    result = "No database entry exists for this build: " + build_number
    try:
        result = db.execute("SELECT * FROM build_change_logs WHERE buildNumber=? AND project=? LIMIT 1",
                            (build_number, project)).fetchone()[2]
    finally:
        return result


def sql_get_next_build_number(project) -> int:
    last_build = sql_fetch_last_builds_by_project(project, 1).fetchone()
    if last_build is None:
        return 1

    return last_build[0] + 1


def sql_insert_build(build_number, project, config_name, build_name, start_date, process_id):
    write_lock.acquire()
    db.execute("INSERT INTO builds values (?,?,?,?,?,?)",
               (build_number, project, config_name, build_name, start_date, process_id))
    db.commit()
    write_lock.release()


def sql_insert_change_log(build_number: int, project: str, change_log: str):
    write_lock.acquire()
    db.execute("INSERT INTO build_change_logs values (?,?,?)", (build_number, project, change_log))
    db.commit()
    write_lock.release()


def sql_update_result(build_number: int, project: str, end_date, result_code: int):
    write_lock.acquire()
    db.execute("INSERT OR REPLACE INTO results values (?,?,?,?)", (build_number, project, end_date, result_code))
    db.commit()
    write_lock.release()
