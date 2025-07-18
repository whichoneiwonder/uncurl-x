import shlex
from unittest.mock import patch

import pytest

from uncurlx.__main__ import main

print_module = "uncurlx.__main__.print"
sys_module = "uncurlx.__main__.sys"


@pytest.fixture
def fake_sys():
    with patch(sys_module) as mock_sys:
        yield mock_sys


@pytest.fixture
def printer():
    with patch(print_module) as mock_printer:
        yield mock_printer


def test_main_method(printer, fake_sys):
    fake_sys.argv = [
        "uncurlx",
        *shlex.split(
            "curl 'https://pypi.python.org/pypi/uncurlx' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'Accept-Language: en-US,en;q=0.8'"
        ),
    ]
    main()

    printer.assert_called_once_with(
        """
httpx.get("https://pypi.python.org/pypi/uncurlx",
    headers={
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "en-US,en;q=0.8"
    },
    cookies={},
)"""
    )
