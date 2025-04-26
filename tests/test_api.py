import contextlib
import pathlib
import tempfile
import unittest
import subprocess

import os

from flask import json
import httpbin
import httpx

import uncurlx
from tests.constants import ENDPOINT, OLD_ENDPOINT, TESTS, ExpectedConversion,ParametrizedConversion

class TestUncurlx(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.endpoint = ENDPOINT
        self.old_endpoint = OLD_ENDPOINT

    def test_parse(self):
        for test in TESTS:
            with self.subTest(test.name):
                expectation = test.with_endpoint(self.endpoint)
                self.run_conversion_case(expectation)

    def run_conversion_case(self, expectation: ExpectedConversion, message: str | None = None):
        if isinstance(expectation.curl_cmd, tuple):
            curl_cmd, kwargs = expectation.curl_cmd
            output = uncurlx.parse(curl_cmd, **kwargs)
        else:
            output = uncurlx.parse(expectation.curl_cmd)
        self.assertMultiLineEqual(output, expectation.expected, message)


class TestUncurlxAgainstCurlWithHttpbin(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.tempdir_path = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.socket = self.tempdir_path / "uncurlx-httpbin.sock"
        self.endpoint = f"unix:/{self.socket.resolve()}"
        # Start the httpbin server
        self.stack.enter_context(subprocess.Popen(
            [
                "python3",
                "-m",
                "httpbin.core",
                "--host",
                str(self.endpoint),
            ],
        ))
        super().setUp()

    def tearDown(self):
        self.stack.close()
        return super().tearDown()

    def test_parse(self):
        output_path = self.tempdir_path / "output.json"
        curl_cmd = f"curl -X GET '{self.endpoint}' -o {output_path.resolve()}"
        curl_result = subprocess.check_output(['sh','-c', curl_cmd], shell=True)
        curl_json = json.loads(output_path.read_text())
        # httpx_result = uncurlx.parse(curl_cmd).
        httpx_result = httpx.get(self.endpoint)
        httpx_json = httpx_result.json()
        self.assertDictEqual(httpx_json, curl_json)
        
    # def run_compatability_case(self, expectation: ExpectedConversion, message: str | None = None):

    # def _run_python_compatability_case(self, expectation: ExpectedConversion, message: str | None = None):
    #     output = uncurlx.parse(expectation.curl_cmd, endpoint=ENDPOINT)
    #     httpbin.app
    #     wsgi_transport = httpx.WSGITransport(app=httpbin.app)
    #     # TODO: Convert this to a test of the response via curl vs the response via httpx
    #     with httpx.Client(transport=wsgi_transport) as client:
    #         response = client.get(self.endpoint)
    #         if response.status_code != 200:
    #             raise RuntimeError("Failed to fetch", output)

    def run_curl(self, curl_cmd: str) -> str:
        # subprocess.
        # httpbin.app.run(host=self.socket)

        return curl_cmd
