import ast
import pathlib
import warnings
from http.cookies import SimpleCookie

import httpx
import pytest
from flask import json

import uncurlx
from tests.constants import (
    ENDPOINT,
    LOCAL_ENDPOINT,
    TESTS,
    ParametrizedConversion,
)


@pytest.fixture(scope="module")
def httpbin_app():
    try:
        import httpbin
    except ImportError:
        pytest.skip("httpbin not installed")
    return httpbin.app


@pytest.fixture
def httpx_client(httpbin_app):
    wsgi_transport = httpx.WSGITransport(app=httpbin_app)
    return httpx.Client(transport=wsgi_transport)


@pytest.fixture
def endpoint():
    return LOCAL_ENDPOINT


def assert_equivalent_httpbin_response(httpx_response, example_curl_response, message=None):
    """
    Compare two httpbin responses to see if they are equivalent.
    """
    httpx_headers = httpx_response.get("headers", {})
    example_curl_headers = example_curl_response.get("headers", {})
    # Remove the headers that are not relevant to the test
    if "Accept-Encoding" in httpx_headers and "Accept-Encoding" not in example_curl_headers:
        del httpx_headers["Accept-Encoding"]
    if httpx_headers.get("Connection") == "keep-alive" and "Connection" not in example_curl_headers:
        del httpx_headers["Connection"]
    if httpx_headers.get("User-Agent", "").startswith("python-httpx/") and example_curl_headers.get(
        "User-Agent", ""
    ).startswith("curl/"):
        del httpx_headers["User-Agent"]
        del example_curl_headers["User-Agent"]
    if "Content-Length" in httpx_headers and "Content-Length" not in example_curl_headers:
        if httpx_headers["Content-Length"] == "0":
            del httpx_headers["Content-Length"]
    if cookies := httpx_headers.get("Cookie"):
        httpx_headers["Cookie"] = dict(sorted(SimpleCookie(cookies).items()))
    if curl_cookies := example_curl_headers.get("Cookie"):
        example_curl_headers["Cookie"] = dict(sorted(SimpleCookie(curl_cookies).items()))
    assert httpx_response == example_curl_response, message


@pytest.mark.parametrize("test", TESTS)
def test_parse(test: ParametrizedConversion):
    expectation = test.with_endpoint(ENDPOINT)
    if isinstance(expectation.curl_cmd, tuple):
        curl_cmd, kwargs = expectation.curl_cmd
        output = uncurlx.parse(curl_cmd, **kwargs)
    else:
        output = uncurlx.parse(expectation.curl_cmd)
    assert output == expectation.expected, f"failed to parse test: {test.name}"


@pytest.mark.parametrize("test", TESTS)
def test_parse_local(test: ParametrizedConversion):
    expectation = test.with_endpoint(LOCAL_ENDPOINT)
    if isinstance(expectation.curl_cmd, tuple):
        curl_cmd, kwargs = expectation.curl_cmd
        output = uncurlx.parse(curl_cmd, **kwargs)
    else:
        output = uncurlx.parse(expectation.curl_cmd)
    assert output == expectation.expected, f"failed to parse test: {test.name}"


@pytest.mark.parametrize("test", TESTS)
def test_parse_compatibility(test: ParametrizedConversion, httpx_client, endpoint):
    expectation = test.with_endpoint(endpoint)
    if isinstance(expectation.curl_cmd, tuple):
        pytest.skip("Not implemented")
    curl_json = _get_precomputed_curl_data(test)
    if not curl_json:
        pytest.skip(f"Missing data for {test.name}")
    output = uncurlx.parse(expectation.curl_cmd)
    with httpx_client as client:
        httpx_result = httpx.Response(999)
        try:
            temp_locals = {
                **locals(),
                "httpx": client,
            }
            with warnings.catch_warnings(action="ignore", category=DeprecationWarning):
                exec(f"httpx_result = ({output})", globals(), temp_locals)
            httpx_result = temp_locals["httpx_result"]
        except SyntaxError as e:
            raise RuntimeError("invalid output", output) from e
        if httpx_result.status_code != 200:
            raise RuntimeError("Failed to fetch", output, httpx_result)
    assert_equivalent_httpbin_response(
        httpx_response=httpx_result.json(),
        example_curl_response=curl_json,
        message=f"Failed comparison for testcase: {test.name}",
    )


@pytest.mark.parametrize("test", TESTS)
def test_parse_ast_compare(test: ParametrizedConversion, httpx_client, endpoint):
    print(f"Testing AST comparison for {test.name}:\n> {test.curl_cmd(endpoint=endpoint)}")
    expectation = test.with_endpoint(endpoint)
    original_output = None
    if isinstance(expectation.curl_cmd, tuple):
        curl_cmd, kwargs = expectation.curl_cmd
        original_output = uncurlx.parse(curl_cmd, **kwargs)
        ast_output = uncurlx.ast_api.parse(curl_cmd, **kwargs)

    elif isinstance(expectation.curl_cmd, str):
        original_output = uncurlx.parse(expectation.curl_cmd)
        ast_output = uncurlx.ast_api.parse(expectation.curl_cmd)
    else:
        pytest.fail(f"Failed to parse {test.name} with uncurlx", True)
    _tree = ast.parse(original_output)
    standardised_original = ast.unparse(_tree)

    assert ast_output == standardised_original, f"AST output does not match manual output for {test.name}"


def _check_index_of_str(target_str: str, ast_str: str, og_str: str) -> tuple[int, int]:
    """
    Check the index of a target string in an AST string representation.
    used for debugging certain tests
    """
    target_index = ast_str.find(target_str)
    if target_index == -1:
        raise ValueError(f"Target string '{target_str}' not found in AST string.")
    og_index = og_str.find(target_str)
    if og_index == -1:
        raise ValueError(f"Original string '{og_str}' does not contain the target string '{target_str}'.")
    if target_index > og_index:
        print(
            f"Warning: AST-produced output contains target string at column {target_index} which is greater than original index {og_index}. for string {target_str!r}"
        )
    elif target_index < og_index:
        print(
            f"Warning: AST-produced output contains target string at column {target_index} which is less than original index {og_index}. for string {target_str!r}"
        )
    return target_index, og_index


def _get_precomputed_curl_data(param):
    json_file = pathlib.Path(__file__).parent.joinpath("data", f"{param.name}.json")
    if json_file.exists():
        return json.loads(json_file.read_text())
    return None
