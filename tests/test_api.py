import contextlib
import pathlib
import unittest

import httpbin
import httpx
from flask import json

import uncurlx
from tests.constants import (
    ENDPOINT,
    LOCAL_ENDPOINT,
    OLD_ENDPOINT,
    TESTS,
    ExpectedConversion,
    ParametrizedConversion,
)


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
        self.app = httpbin.app
        self.endpoint = LOCAL_ENDPOINT
        super().setUp()

    def tearDown(self):
        self.stack.close()
        return super().tearDown()

    def assertEquivalentHttpBinResponse(
        self, *, httpx_response: dict, example_curl_response: dict, message: str | None = None
    ):
        """
        Compare two httpbin responses to see if they are equivalent.
        """
        httpx_headers: dict[str, str] = httpx_response.get("headers", {})
        example_curl_headers: dict[str, str] = example_curl_response.get("headers", {})
        # Remove the headers that are not relevant to the test
        if "Accept-Encoding" in httpx_headers and "Accept-Encoding" not in example_curl_headers:
            del httpx_headers["Accept-Encoding"]
        if httpx_headers.get("Connection") == "keep-alive" and "Connection" not in example_curl_headers:
            # Remove the connection header if it is not in the example curl response
            del httpx_headers["Connection"]
        if httpx_headers.get("User-Agent", "").startswith("python-httpx/") and example_curl_headers.get(
            "User-Agent", ""
        ).startswith("curl/"):
            # Remove the user agent header if it is not in the example curl response
            del httpx_headers["User-Agent"]
            del example_curl_headers["User-Agent"]
        self.assertDictEqual(httpx_response, example_curl_response, message)

    def test_parse(self):
        # output_path = self.tempdir_path / "output.json"
        # curl_cmd = f"curl -X GET '{self.endpoint}' -o {output_path.resolve()}"
        # curl_result = subprocess.check_output(['sh','-c', curl_cmd])
        name = "basic_get"
        curl_json = json.loads(pathlib.Path(__file__).parent.joinpath("data", f"{name}.json").read_text())
        wsgi_transport = httpx.WSGITransport(app=self.app)
        httpx_client = httpx.Client(transport=wsgi_transport)

        # httpx_result = uncurlx.parse(curl_cmd).
        httpx_result = httpx_client.get(self.endpoint)
        self.assertEquivalentHttpBinResponse(
            httpx_response=httpx_result.json(),
            example_curl_response=curl_json,
        )
    def test_parse_compatability(self):
        for test in TESTS:
            with self.subTest(test.name):
                self.run_compatability_case(test)

    # def run_compatability_case(self, expectation: ExpectedConversion, message: str | None = None):
    def _get_precomputed_curl_data(self, param: ParametrizedConversion) -> dict|None:
        json_file = pathlib.Path(__file__).parent.joinpath("data", f"{param.name}.json")
        if json_file.exists():
            return json.loads(json_file.read_text())
        else:
            return None

    def run_compatability_case(self, parametrization: ParametrizedConversion, message: str | None = None):
        expectation = parametrization.with_endpoint(self.endpoint)
        if isinstance(expectation.curl_cmd, tuple):
            self.skipTest("Not implemented")
        if not (curl_json := self._get_precomputed_curl_data(parametrization)):
            self.skipTest(f"Missing data for {parametrization.name}")
        output = uncurlx.parse(expectation.curl_cmd)
        httpbin.app
        wsgi_transport = httpx.WSGITransport(app=httpbin.app)
        # TODO: Convert this to a test of the response via curl vs the response via httpx
        with httpx.Client(transport=wsgi_transport) as client:
            httpx_result: httpx.Response = httpx.Response(999)
            try:
                temp_locals = {**locals(), "httpx": client, }
                exec(f'httpx_result = ({output})', globals(), temp_locals)
                httpx_result = temp_locals["httpx_result"]
            except SyntaxError as e:
                raise RuntimeError("invalid output", output) from e
            if httpx_result.status_code != 200:
                raise RuntimeError("Failed to fetch", output, httpx_result)
        self.assertEquivalentHttpBinResponse(
            httpx_response=httpx_result.json(),
            example_curl_response=curl_json,
        )

    def run_curl(self, curl_cmd: str) -> str:
        # subprocess.
        # httpbin.app.run(host=self.socket)

        return curl_cmd
