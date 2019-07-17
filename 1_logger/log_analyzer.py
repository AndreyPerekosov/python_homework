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
import os
import argparse


FILE_PATTERN = r'nginx-access-ui\.log-[0-9]{8}\.(gz|plain)'


config = {
    "REPORT_SIZE": 10,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log", "FILE_PATTERN": FILE_PATTERN,
    "LOG_FILE": None, "DEFAULT_CONFIG": "settings.cfg",
    "THRESHOLD_OF_ERRORS": 10, "TEMPLATE": "report.html",
}


def main(config):
    """
    This is main function. The functions is designed
    for working with .plain or .gz log files
    The result of working that function is html log file.
    """
    try:
        active_config = dict(config)

        # set command line params
        parser = argparse.ArgumentParser(description="Analyzer log file")
        parser.add_argument('--config',
                            type=str,
                            default=active_config["DEFAULT_CONFIG"],
                            help='sets path to active_config file')

        # set logging params
        logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s',
                            level=logging.DEBUG,
                            datefmt=time.strftime('%Y.%m.%d %H:%M:%S'),
                            filename=active_config["LOG_FILE"], filemode="w")

        # read config file
        args = parser.parse_args()
        sr.set_config(args.config, active_config)

        searched_file = sr.search_last_file(file_pattern=active_config["FILE_PATTERN"],
                                            path=active_config["LOG_DIR"])
        if searched_file.path is None:
            logging.info("There are no files for analize")
            sys.exit()

        if not os.path.exists(active_config["REPORT_DIR"]):
            os.makedirs(active_config["REPORT_DIR"])

        new_file = f"report-{searched_file.date.strftime('%Y.%m.%d')}.html"

        # search all ready exists log file
        if os.path.exists(os.path.join(active_config["REPORT_DIR"], new_file)):
            logging.info(f"File with name {new_file} already exists")
            sys.exit()

        logging.info("Please wait. Analyze in progress... ")

        # parsing data from log file
        errors_counter = [0]
        logs = (sr.parser(searched_file.path, searched_file.ext, errors_counter))
        data = sr.analyze_formater(active_config["REPORT_SIZE"], logs)
        if errors_counter[0] / active_config["REPORT_SIZE"] * 100 > active_config["THRESHOLD_OF_ERRORS"]:
            logging.info("Analysis has faild. Could not parse most of the log. Error threshold exceeded")
            sys.exit()

        # creating path for log file

        path = os.path.join(active_config["REPORT_DIR"], new_file)

        # creating log file
        sr.write_log_file(template=active_config["TEMPLATE"], path=path,
                          data=data)

        logging.info("Analysis was completed successfully")

    except Exception:
        logging.exception("Got exception")


if __name__ == "__main__":
    main(config)
