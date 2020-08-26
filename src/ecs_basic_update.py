"""
A python script to pull the latest data from centralized ECS to the local file database ECS.
"""

import os
import time
import sqlite3
from sqlite3 import OperationalError
import requests
import pandas as pd


class BColors:
    """
    Simple class to print text in color on terminal
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def update_db():
    """
    Primary update method that calls an API to get JSON data and populates a local
    database using sqlite3.
    """
    # call API to get data
    ecs_basic_uri = "https://ert.cognicept.systems/update/basic"
    try:
        # Get data. Retry a few (5) times if it fails
        total_retries = 3
        while True:
            total_retries -= 1
            try:
                resp = requests.get(ecs_basic_uri, timeout=0.5)
                break
            except Exception:
                if total_retries == 0:
                    raise
                else:
                    print(f"{BColors.WARNING}Retrying...{BColors.ENDC}")
                    time.sleep(0.5)

        if resp.status_code != 200:
            print(f"{BColors.FAIL}REST API error{BColors.ENDC}")
        else:
            # Get JSON data
            ecs_db_dump = pd.DataFrame(resp.json()["error_classification"])
            ert_db_dump = pd.DataFrame(resp.json()["error_report"])
            ri_db_dump = pd.DataFrame(resp.json()["robot_info"])
            ecs_db_dump["error_type"] = ecs_db_dump["error_type"].astype(str)
            ecs_db_dump["error_resolution"] = ecs_db_dump["error_resolution"].astype(
                str)

            try:
                # Connect to database
                conn = sqlite3.connect(db_path)
                # Create a cursor
                cur = conn.cursor()
            except OperationalError:
                print(f"{BColors.FAIL}CONNECTION ERROR: \
Unable to connect to database.{BColors.ENDC}")
                raise OperationalError

            # Drop existing tables if any
            try:
                cur.execute('''DROP TABLE error_classification''')
            except OperationalError:
                print("error_classification table doesn't exist, will create.")
                raise OperationalError

            try:
                cur.execute('''DROP TABLE error_report''')
            except OperationalError:
                print("error_report table doesn't exist, will create.")
                raise OperationalError

            try:
                cur.execute('''DROP TABLE robot_info''')
            except OperationalError:
                print("robot_info table doesn't exist, will create.")
                raise OperationalError

            # Create tables
            try:
                cur.execute('''CREATE TABLE error_classification
                (classification_id integer,
                    client_error_code text,
                    cognicept_error_code text,
                    compounding_flag booleantext,
                    error_id integer,
                    error_module text,
                    error_resolution json,
                    error_source text,
                    error_text text,
                    error_type json,
                    error_uuid text,
                    robot_type integer,
                    severity text)''')
            except OperationalError:
                print(f"{BColors.FAIL}CREATE TABLE ERROR: \
error_classification table.{BColors.ENDC}")
                raise OperationalError

            try:
                cur.execute('''CREATE TABLE error_report
                (compounding_flag booleantext,
                    error_code text,
                    error_description text,
                    error_id integer,
                    error_level text,
                    error_module text,
                    error_resolution text,
                    error_source text,
                    error_text text,
                    robot_make text,
                    robot_model text,
                    robot_site text)''')
            except OperationalError:
                print(f"{BColors.FAIL}CREATE TABLE ERROR: error_report table.{BColors.ENDC}")
                raise OperationalError

            try:
                cur.execute('''CREATE TABLE robot_info
                (robot_id integer,
                    robot_make text,
                    robot_model text,
                    robot_site text)''')
            except OperationalError:
                print(f"{BColors.FAIL}CREATE TABLE ERROR: robot_info table.{BColors.ENDC}")
                raise OperationalError

            # Insert rows
            try:
                ecs_db_dump = pd.DataFrame(
                    ecs_db_dump, columns=['classification_id', 'client_error_code',
                                          'cognicept_error_code', 'compounding_flag',
                                          'error_id', 'error_module', 'error_resolution',
                                          'error_source', 'error_text', 'error_type',
                                          'error_uuid', 'robot_type', 'severity'])
                cur.executemany(
                    'INSERT INTO error_classification VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    ecs_db_dump.values.tolist())
            except OperationalError:
                print(f"{BColors.FAIL}INSERT ERROR: error_classification table.{BColors.ENDC}")
                raise OperationalError

            try:
                ert_db_dump = pd.DataFrame(
                    ert_db_dump, columns=['compounding_flag', 'error_code', 'error_description',
                                          'error_id', 'error_level', 'error_module',
                                          'error_resolution', 'error_source', 'error_text',
                                          'robot_make', 'robot_model', 'robot_site'])
                cur.executemany(
                    'INSERT INTO error_report VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    ert_db_dump.values.tolist())
            except OperationalError:
                print(f"{BColors.FAIL}INSERT ERROR: error_report table.{BColors.ENDC}")
                raise OperationalError

            try:
                ri_db_dump = pd.DataFrame(
                    ri_db_dump, columns=['robot_id', 'robot_make', 'robot_model', 'robot_site'])
                cur.executemany(
                    'INSERT INTO robot_info VALUES (?,?,?,?)', ri_db_dump.values.tolist())
            except OperationalError:
                print(f"{BColors.FAIL}INSERT ERROR: robot_info table.{BColors.ENDC}")
                raise OperationalError

            # Save (commit) the changes
            try:
                conn.commit()
            except OperationalError:
                print(f"{BColors.FAIL}SAVE ERROR: Unable to save update changes.{BColors.ENDC}")
                raise OperationalError

            # Close connection
            try:
                conn.close()
            except OperationalError:
                print(f"{BColors.FAIL}CONNECTION ERROR: \
Unable to disconnect from database.{BColors.ENDC}")
                raise OperationalError

        print(f"{BColors.OKGREEN}ECS basic update successful.{BColors.ENDC}")

    except requests.exceptions.Timeout:
        print(f"{BColors.FAIL}REST API error: time out.{BColors.ENDC}")
    except requests.exceptions.TooManyRedirects:
        print(f"{BColors.FAIL}REST API error: Wrong endpoint.{BColors.ENDC}")
    except OperationalError:
        print(f"{BColors.FAIL}Could not update ECS because of Database error.{BColors.ENDC}")
    except:
        print(f"{BColors.FAIL}REST API error.{BColors.ENDC}")


if __name__ == "__main__":

    # pull ECS basic version
    db_path = os.path.expanduser(os.environ['ECS_DB_LOC'])
    if os.path.exists(db_path):
        print(f"{BColors.WARNING}ECS db already exists here: {BColors.ENDC}")
        print(db_path)
        user_choice = input(
            "Are you sure you want to overwrite the existing db? \
You will lose any local changes: (Y/N) ")

        if user_choice in ["Y", 'y']:
            update_db()
        else:
            print(
                f"{BColors.OKBLUE}Exiting. \
                    Please rename existing db to keep local changes \
and retry update.{BColors.ENDC}")
    else:
        print(
            f"{BColors.WARNING}ECS db does not exist. Creating one here: {BColors.ENDC}")
        print(db_path)
        update_db()
