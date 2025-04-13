"""
Module for log parser and report generator.
"""

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for"
# "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import argparse
import json
import pathlib
import sys
from logging import Logger

import structlog

init_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": None,
    "ERROR_THRESHOLD": 10,
}


def configure_logger(log_file: str| None = None) -> Logger:
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
        ]
    )
    if log_file:
        with pathlib.Path(log_file).open("wt", encoding="UTF-8") as f:
            structlog.configure(
                logger_factory=structlog.PrintLoggerFactory(f),
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
        help="Path to configuration file (JSON formatted)",
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





def main():
    """Main function to execute"""
    args = parse_args()
    new_config = parse_config(init_config, args.config)

    global logger #  pylint: disable=global-statement
    logger = configure_logger(new_config.get("LOG_FILE"))

    logger.info(f"Starting log analyzer with config {str(new_config)}")


if __name__ == "__main__":
    main()
