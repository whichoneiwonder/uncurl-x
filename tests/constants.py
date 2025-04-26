from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


OLD_ENDPOINT = "https://pypi.python.org/pypi/uncurlx"
ENDPOINT = "https://httpbin.org/anything"


@dataclass
class ExpectedConversion:
    curl_cmd: str | tuple[str, dict[str, str]]
    expected: str


@dataclass
class ParametrizedConversion:
    name: str
    curl_cmd: Callable[[str], str | tuple[str, dict[str, str]]]
    expected: Callable[[str], str]

    def with_endpoint(self, endpoint: str) -> ExpectedConversion:
        return ExpectedConversion(
            curl_cmd=self.curl_cmd(endpoint),
            expected=self.expected(endpoint),
        )


TESTS = [
    ParametrizedConversion(
        name="basic_get",
        curl_cmd=lambda endpoint: f"curl '{endpoint}'",
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={},
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="colons_in_headers",
        curl_cmd=lambda endpoint: f"curl '{endpoint}' -H 'authority:mobile.twitter.com'",
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={
        "authority": "mobile.twitter.com"
    },
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="basic_headers",
        curl_cmd=lambda endpoint: f"curl '{endpoint}' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'Accept-Language: en-US,en;q=0.8'",
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "en-US,en;q=0.8"
    },
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="cookies",
        curl_cmd=lambda endpoint: f"curl '{endpoint}' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'Cookie: foo=bar; baz=baz2'",
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={
        "Accept-Encoding": "gzip,deflate,sdch"
    },
    cookies={
        "baz": "baz2",
        "foo": "bar"
    },
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="test_cookies_lowercase",
        curl_cmd=lambda endpoint: f"curl '{endpoint}' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'cookie: foo=bar; baz=baz2'",
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={
        "Accept-Encoding": "gzip,deflate,sdch"
    },
    cookies={
        "baz": "baz2",
        "foo": "bar"
    },
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="cookies_with_dollar_sign",
        curl_cmd=lambda endpoint: f"curl '{endpoint}' -H 'Accept-Encoding: gzip,deflate,sdch' -H $'Cookie: somereallyreallylongcookie=true'",
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={
        "Accept-Encoding": "gzip,deflate,sdch"
    },
    cookies={
        "somereallyreallylongcookie": "true"
    },
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="simple_post",
        curl_cmd=lambda endpoint: f"""curl '{endpoint}' -X POST""",
        expected=lambda endpoint: (
            """httpx.post("{}",""".format(endpoint)
            + """
    headers={},
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="post_with_data",
        curl_cmd=lambda endpoint: (
            f"""curl '{endpoint}'"""
            """ --data '[{"evt":"newsletter.show","properties":{"newsletter_type":"userprofile"},"now":1396219192277,"ab":{"welcome_email":{"v":"2","g":2}}}]' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'Cookie: foo=bar; baz=baz2'"""
        ),
        expected=lambda endpoint: (
            f"""httpx.post("{endpoint}","""
            + """
    data='[{"evt":"newsletter.show","properties":{"newsletter_type":"userprofile"},"now":1396219192277,"ab":{"welcome_email":{"v":"2","g":2}}}]',
    headers={
        "Accept-Encoding": "gzip,deflate,sdch",
        "Content-Type": "application/x-www-form-urlencoded"
    },
    cookies={
        "baz": "baz2",
        "foo": "bar"
    },
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="post_with_dict_data",
        curl_cmd=lambda endpoint: (
            f"""curl '{endpoint}'"""
            """ --data '{"evt":"newsletter.show","properties":{"newsletter_type":"userprofile"}}' -H 'Accept-Encoding: gzip,deflate,sdch' -H 'Cookie: foo=bar; baz=baz2'"""
        ),
        expected=lambda endpoint: (
            f"""httpx.post("{endpoint}","""
            + """
    data='{"evt":"newsletter.show","properties":{"newsletter_type":"userprofile"}}',
    headers={
        "Accept-Encoding": "gzip,deflate,sdch",
        "Content-Type": "application/x-www-form-urlencoded"
    },
    cookies={
        "baz": "baz2",
        "foo": "bar"
    },
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="string post",
        curl_cmd=lambda endpoint: (
            f"""curl '{endpoint}' """
            """--data 'this is just some data'"""
        ),
        expected=lambda endpoint: (
            """httpx.post("{}",""".format(endpoint)
            + """
    data='this is just some data',
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    },
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_binary_data",
        curl_cmd=lambda endpoint: (
            f"""curl '{endpoint}'"""
            """ --data-binary 'this is just some data'"""
        ),
        expected=lambda endpoint: (
            """httpx.post("{}",""".format(endpoint)
            + """
    data='this is just some data',
    headers={},
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_raw_data",
        curl_cmd=lambda endpoint: (
            f"""curl '{endpoint}'"""
            """ --data-raw 'this is just some data'"""
        ),
        expected=lambda endpoint: (
            """httpx.post("{}",""".format(endpoint)
            + """
    data='this is just some data',
    headers={},
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_another_binary_data",
        curl_cmd=lambda endpoint: (
            r"""curl -H 'PID: 20000079' -H 'MT: 4' -H 'DivideVersion: 1.0' -H 'SupPhone: Redmi Note 3' -H 'SupFirm: 5.0.2' -H 'IMEI: wx_app' -H 'IMSI: wx_app' -H 'SessionId: ' -H 'CUID: wx_app' -H 'ProtocolVersion: 1.0' -H 'Sign: 7876480679c3cfe9ec0f82da290f0e0e' -H 'Accept: /' -H 'BodyEncryptType: 0' -H 'User-Agent: Mozilla/5.0 (Linux; Android 6.0.1; OPPO R9s Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36 hap/1.0/oppo com.nearme.instant.platform/2.1.0beta1 com.felink.quickapp.reader/1.0.3 ({"packageName":"com.oppo.market","type":"other","extra":{}})' -H 'Content-Type: text/plain; charset=utf-8' -H 'Host: pandahomeios.ifjing.com' --data-binary '{"CateID":"508","PageIndex":1,"PageSize":30}' --compressed"""
            f""" '{endpoint} /action.ashx/otheraction/9028'"""
        ),
        expected=lambda endpoint: (
            f"""httpx.post("{endpoint} /action.ashx/otheraction/9028","""
            r"""
    data='{"CateID":"508","PageIndex":1,"PageSize":30}',
    headers={
        "Accept": "/",
        "BodyEncryptType": "0",
        "CUID": "wx_app",
        "Content-Type": "text/plain; charset=utf-8",
        "DivideVersion": "1.0",
        "Host": "pandahomeios.ifjing.com",
        "IMEI": "wx_app",
        "IMSI": "wx_app",
        "MT": "4",
        "PID": "20000079",
        "ProtocolVersion": "1.0",
        "SessionId": "",
        "Sign": "7876480679c3cfe9ec0f82da290f0e0e",
        "SupFirm": "5.0.2",
        "SupPhone": "Redmi Note 3",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; OPPO R9s Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36 hap/1.0/oppo com.nearme.instant.platform/2.1.0beta1 com.felink.quickapp.reader/1.0.3 ({\"packageName\":\"com.oppo.market\",\"type\":\"other\",\"extra\":{}})"
    },
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_insecure_flag",
        curl_cmd=lambda endpoint: (f"""curl '{endpoint}' --insecure"""),
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={},
    cookies={},
    auth=(),
    proxy={},
    verify=False
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_request_kargs",
        curl_cmd=lambda endpoint: (
            f"curl '{endpoint}' -H 'Accept-Encoding: gzip,deflate,sdch'",
            dict(timeout=0.1, allow_redirects=True),
        ),
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    allow_redirects=True,
    timeout=0.1,
    headers={
        "Accept-Encoding": "gzip,deflate,sdch"
    },
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_request_kargs2",
        curl_cmd=lambda endpoint: (
            f"curl '{endpoint}' -H 'Accept-Encoding: gzip,deflate,sdch'",
            dict(
                timeout=0.1,
            ),
        ),
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    timeout=0.1,
    headers={
        "Accept-Encoding": "gzip,deflate,sdch"
    },
    cookies={},
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_escaped_newlines",
        curl_cmd=lambda endpoint: (f"""curl '{endpoint}' \\\n -H 'Accept-Encoding: gzip,deflate' \\\n --insecure"""),
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={
        "Accept-Encoding": "gzip,deflate"
    },
    cookies={},
    auth=(),
    proxy={},
    verify=False
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_escaped_unicode_in_cookie",
        curl_cmd=lambda endpoint: (f"""curl '{endpoint}' -H $'cookie: sid=00Dt00000004XYz\\u0021ARg' """),
        expected=lambda endpoint: (
            f"""httpx.get("{endpoint}","""
            """
    headers={},
    cookies={
        "sid": "00Dt00000004XYz!ARg"
    },
    auth=(),
    proxy={},
)"""
        ),
    ),
    ParametrizedConversion(
        name="parse_curl_with_proxy_and_proxy_auth",
        curl_cmd=lambda endpoint: (f"curl '{endpoint}' -U user: -x proxy.python.org:8080"),
        expected=lambda endpoint: (
            """httpx.get("{}",""".format(endpoint)
            + """
    headers={},
    cookies={},
    auth=(),
    proxy={'http': 'http://user:@proxy.python.org:8080/', 'https': 'http://user:@proxy.python.org:8080/'},
)"""
        ),
    ),
]
