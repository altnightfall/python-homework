"""
Module for log parser and report generator.
"""

import argparse
import datetime
import gzip
import json
import os
import pathlib
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from statistics import mean, median
from typing import Any

import structlog

init_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": None,
    "ERROR_THRESHOLD": 10,
}


def configure_logger(log_file: str | None = None) -> Any:
    """
    Configure structlog file
    :param log_file: path to log file to save
    :return: Logger
    """
    structlog.configure(
        context_class=dict,
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
    if log_file:
        structlog.configure(
            logger_factory=structlog.WriteLoggerFactory(
                file=pathlib.Path(log_file).open(  # pylint: disable=consider-using-with
                    "wt", encoding="UTF-8"
                )
            ),
        )
    else:
        structlog.configure(
            logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        )
    return structlog.get_logger()


logger = configure_logger()


def parse_args():
    """
    Parse script arguments
    :return: dict with parsed arguments
    """
    parser = argparse.ArgumentParser(description="Parameters for log_analyzer")
    parser.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        required=False,
        help="Path to JSON configuration file",
    )
    return parser.parse_args()


def parse_config(default_config: dict, config_path: pathlib.Path) -> dict:
    """
    Parse script config from file
    :param default_config: Default configuration
    :param config_path: Path to the JSON file with update for config
    :return: Updated config
    """
    if config_path is None:
        return default_config

    updated_config = default_config
    try:
        with open(config_path, encoding="UTF-8") as config_file:
            config_update = json.load(config_file)
            updated_config.update(config_update)
    except FileNotFoundError as e:
        logger.error(
            f"Failed to load config file {str(config_path)}, exception: {str(e)}"
        )
    except json.decoder.JSONDecodeError as e:
        logger.error(
            f"Failed to decode config file {str(config_path)}, exception: {str(e)}"
        )
    return updated_config


@dataclass
class Log:
    """Class to store information about nginx access logs"""

    path: pathlib.Path
    date: date
    extension: str


def get_last_logfile(log_dir: pathlib.Path) -> Log | None:
    """Get the last nginx access log file in a given directory."""
    if not log_dir.exists() or not log_dir.is_dir():
        raise FileNotFoundError("Log directory does not exist")

    logfile = None
    pattern = re.compile(r"nginx-access-ui\.log-(\d{8})(\.gz)?$")
    for path in log_dir.iterdir():
        try:
            [(_date, extension)] = re.findall(pattern, str(path))
            ld = datetime.datetime.strptime(_date, "%Y%m%d")
            log_date = ld.date()
            if not logfile or log_date > logfile.date:
                logfile = Log(path, log_date, extension)
        except ValueError:
            continue
    return logfile


def check_report_exist(report_dir: pathlib.Path, _date: date) -> bool:
    """Check if a report file exists for the given date."""
    report_path = report_dir / f"{_date}.html"
    return report_path.exists()


def parse_log_line(line: str = ""):
    """
    Parse logical information from a single line of the log file.
    :param line: line of log file
    :return: Extracted URL and request time.
    """
    re_result = re.search("(?:GET|POST|HEAD|OPTIONS|PUT)(.+?)HTTP", line)
    url = None
    if re_result:
        url = re_result.group(1).strip()
    else:
        logger.error(f"Couldn't find parse line {line}")

    request_time = float(re.findall(r"\d+\.\d+", line.split(" ")[-1].strip())[0])
    return url, request_time


def get_data_from_log(log_file: Log, threshold: Any) -> dict:
    """Get data from log file."""
    errors = 0
    lines_count = 0
    data = (
        gzip.open(log_file.path.absolute(), mode="rt")
        if log_file.extension == ".gz"
        else log_file.path.open()
    )
    parsed_data : dict = {}
    with data:
        for line in data:
            lines_count += 1
            url, request_time = parse_log_line(line)
            if not url:
                errors += 1
                continue
            if url not in parsed_data:
                parsed_data[url] = []
            parsed_data[url].append(request_time)

    logger.warning(f"{errors} errors found while parsing log")

    if errors / lines_count > threshold / 100:
        raise ValueError("Too many errors found while parsing log")

    return parsed_data


def process_data(parsed_data: dict, limit: Any) -> list[dict]:
    """Process data for report."""
    sorted_data = sorted(parsed_data.items(), key=lambda x: -sum(x[1]))[:limit]
    report_data = []
    total_time = 0
    total_count = 0
    for _, request_times in sorted_data:
        total_time += sum(request_times)
        total_count += len(request_times)

    for url, request_times in sorted_data:
        report_data.append(
            {
                "url": url,
                "count": len(request_times),
                "count_perc": f"{100*len(sorted_data) / total_count:.5f}",
                "time_avg": f"{mean(request_times):.5f}",
                "time_max": f"{max(request_times):.5f}",
                "time_med": f"{median(request_times):.5f}",
                "time_perc": f"{100*sum(request_times) / total_time:.5f}",
                "time_sum": f"{sum(request_times):.5f}",
            }
        )

    return report_data


def generate_report(report_data, report_date, report_dir):
    """Generate a report for data"""
    if not report_data or not report_date:
        logger.warning("No report data or date found. Skipping report generation.")
        return
    if not pathlib.Path(report_dir).exists():
        logger.warning("No report directory found. Generating.")
        os.makedirs(report_dir, exist_ok=True)

    scrip_dir = pathlib.Path(os.path.dirname(os.path.relpath(__file__)))
    report_fname = pathlib.Path(report_dir) / f"report-{report_date}.html.tmp"
    shutil.copyfile(scrip_dir / "report.html", report_fname)
    with open(report_fname, encoding="UTF-8") as file:
        data = file.read()
        data = data.replace("var table = $table_json;", f"var table = {report_data!r};")
    with open(report_fname, "w", encoding="UTF-8") as file:
        file.write(data)

    final_report_fname = report_fname.parent / report_fname.stem
    os.rename(report_fname, final_report_fname)
    logger.info(f"Generated report: {final_report_fname}")


def main(configuration: dict):
    """Main function to execute"""
    log_dir_path = configuration.get("LOG_DIR")
    if not isinstance(log_dir_path, str | pathlib.Path):
        raise TypeError("Invalid log directory path")

    log_file = get_last_logfile(pathlib.Path(log_dir_path))
    if not log_file:
        raise FileNotFoundError("No log file exist")

    if not pathlib.Path(log_file.path).exists():
        raise FileNotFoundError("No log file exist")
    logger.info(f"Log file found: {log_file.path}")

    report_dir_path = configuration.get("REPORT_DIR")
    if not isinstance(report_dir_path, str | pathlib.Path):
        raise TypeError("Invalid report directory path")

    report_dir= pathlib.Path(report_dir_path)

    if not pathlib.Path(report_dir).exists():
        raise FileNotFoundError("Report dir does not exist")
    logger.info(f"Report dir found: {report_dir}")

    if check_report_exist(report_dir, log_file.date):
        logger.info("Report file already exists for the given date, skipped.")
        return

    logger.info(f"Parsing log file for date: {log_file.date}")

    data = get_data_from_log(log_file, configuration.get("ERROR_THRESHOLD"))

    if not data:
        raise ValueError("No data found in the log file")

    report_data = process_data(data, configuration.get("REPORT_SIZE"))

    generate_report(report_data, log_file.date, configuration.get("REPORT_DIR"))


if __name__ == "__main__":
    args = parse_args()
    config = parse_config(init_config, args.config)
    logger = configure_logger(config.get("LOG_FILE"))

    try:
        logger.info(f"Starting log analyzer with config {str(config)}")
        main(config)
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Failed to execute with config {config}, exception: {e}")
