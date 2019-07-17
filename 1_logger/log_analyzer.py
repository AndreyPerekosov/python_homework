#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
from src.service import service as sr
import logging
import time
from string import Template
import sys
import json
import os


FILE_PATTERN = r'nginx-access-ui\.log-[0-9]{8}\.(gz|plain)'


config = {
    "REPORT_SIZE": 10,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log", "FILE_PATTERN": FILE_PATTERN,
    "LOG_FILE": None, "DEFAULT_CONFIG": "setting.txt",
    "THRESHOLD_OF_ERRORS": 10,
}


def main(config):
    """
    This is main function. The functions is designed
    for working with .plain or .gz log files
    The result of working that function is html log file.
    """

    try:
        # read config file which set up from command line if exists one
        sys_argv = sys.argv
        if '--config' in sys_argv:
            config["DEFAULT_CONFIG"] = sys_argv[-1]

        with open(config["DEFAULT_CONFIG"]) as file:
            content = file.read()
            js = json.loads(content)

        for key, value in js.items():
            config[key] = value

        logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s',
                            level=logging.DEBUG,
                            datefmt=time.strftime('%Y.%m.%d %H:%M:%S'),
                            filename=config["LOG_FILE"], filemode="w")

        searched_file = sr.search_last_file(file_pattern=config["FILE_PATTERN"],
                                            path=config["LOG_DIR"])
        if searched_file.path is None:
            logging.info("There are no files for analize")
            sys.exit()

        if not os.path.exists(config["REPORT_DIR"]):
            os.makedirs(config["REPORT_DIR"])

        new_file = f"report-{searched_file.date.strftime('%Y.%m.%d')}.html"

        # search all ready exists log file
        if os.path.exists(os.path.join(config["REPORT_DIR"], new_file)):
            logging.info(f"File with name {new_file} already exists")
            sys.exit()

        logging.info("Please wait. Analyze in progress... ")
        errors_counter = [0]
        logs = (sr.parser(searched_file.path, searched_file.ext, errors_counter))

        # creating path for log file

        path = os.path.join(config["REPORT_DIR"], new_file)

        with open("report.html", "r") as file:
            file_content = file.readlines()
        for index in range(len(file_content)):
            if "$table_json" in file_content[index]:
                templ = Template(file_content[index])
                line = templ.safe_substitute(table_json=sr.analyze_formater(config["REPORT_SIZE"], logs))
                file_content[index] = line
                break

        if errors_counter[0] / config["REPORT_SIZE"] * 100 > config["THRESHOLD_OF_ERRORS"]:
            logging.info("Analysis has faild. Could not parse most of the log. Error threshold exceeded")
            sys.exit()

        with open(path, "w") as file:
            for line in file_content:
                file.write(line)

        logging.info("Analysis was completed successfully")

    except Exception:
        logging.exception("Got exception")


if __name__ == "__main__":
    main(config)
