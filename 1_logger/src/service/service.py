import re
import gzip
from collections import namedtuple
import os
from datetime import datetime as dt
import logging


def search_last_file(file_pattern, path):
    """
    The function returns named tuple (date, extension, path)
    last log file by date that defines in name of that file
    and satisfies the regular expression "file_pattern"
    and situtates in "path" folder
    """
    SelectedFile = namedtuple("SelectedFile", "date ext path")

    pat = re.compile(file_pattern)
    filtered_files = []

    sel_file = SelectedFile(None, None, None)

    files_list = (os.listdir(path))

    for file in files_list:
        if re.fullmatch(pat, file):
            filtered_files.append(file)

    for file in filtered_files:
        temp_list = file.split("-")[-1].split(".")
        temp_file = SelectedFile(dt.strptime(temp_list[0], '%Y%m%d'),
                                 temp_list[1], os.path.join(path, file))

        if sel_file.date is None or temp_file.date > sel_file.date:
            sel_file = temp_file

    return sel_file


def parser(path, ext, errors_counter):
    """
    The function-generator is parsing a report file ("path"
    with extension "ext") and yields tuple (url, reauest_time)
    for every line of report file.
    The function counts number of Exception that stored in list with one item
    errors_counter. This parametr should passed into function by link.
    """

    opener = gzip.open if ext == 'gz' else open
    with opener(path) as file:
        for line in file:
            try:
                line = line.decode("utf-8").strip()
                parse = line.split(" ")
                yield parse[7], float(parse[-1])
            except Exception:
                logging.exception("Got exception")
                errors_counter[0] += 1


def analyze(parser):
    """
    The function is working with generator function and forming
    list of values for log-file.
    The list is sorted in ascending order.
    """

    analyze = {}
    all_request_count = 0
    all_request_time_count = 0
    analyze_list = []

    for url, request_time in parser:
        all_request_count += 1
        all_request_time_count += request_time
        if url not in analyze:
            analyze[url] = []
        analyze[url].append(request_time)

    for url, time_list in analyze.items():
        count = len(time_list)
        count_perc = (count / all_request_count) * 100
        time_sum = sum(time_list)
        time_perc = (time_sum / all_request_time_count) * 100
        time_avg = time_sum / count
        time_max = max(time_list)
        time_med = time_list[count // 2]
        dict_ = {"count": count, "count_perc": count_perc,
                 "time_sum": time_sum,
                 "time_perc": time_perc,
                 "time_avg": time_avg,
                 "time_max": time_max, "time_med": time_med,
                 "url": url}
        analyze_list.append(dict_)

    analyze_list.sort(key=lambda item: item["time_sum"], reverse=True)

    return analyze_list


def analyze_formater(report_size, parser):
    """
    The function is formating input of "analyze" function
    and returns list of formated values
    with lenght of "report_size" parametr
    """

    list_out = analyze(parser)[0:report_size]
    for item in list_out:
        item["count_perc"] = f"{item['count_perc']:.3f}"
        item["time_sum"] = f"{item['time_sum']:.3f}"
        item["time_perc"] = f"{item['time_perc']:.3f}"
        item["time_avg"] = f"{item['time_avg']:.3f}"
    return list_out
