"""
Tests for log_analyzer.py
"""

from src.log_analyzer import parse_config, parse_log_line


def test_update_config():
    """
    Test config update
    :return:
    """
    # default config
    expected_config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
    }

    assert expected_config == parse_config(expected_config, None)


def test_parse_log_line():
    """
    Test log line parsing
    :return:
    """
    log_line = (
        "1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "
        '"GET /api/v2/banner/24987703 HTTP/1.1" 200 883 '
        '"-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5"'
        ' "-" "1498697422-2190034393-4708-9752753"'
        '"dc7161be3" 0.726'
    )

    url, request_time = parse_log_line(log_line)
    expected_url = (
        "/api/v2/banner/24987703"
    )
    expected_request_time = 0.726
    assert expected_url == url
    assert expected_request_time == request_time
