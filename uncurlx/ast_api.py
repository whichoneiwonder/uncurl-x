import ast
from typing import List, Union

from .api import parse_context


def parse(curl_command: Union[str, List[str]], **kargs) -> str:
    parsed_context = parse_context(curl_command)

    tree = ast.Interactive()
    func_call_id = ast.Name(id="httpx")
    if parsed_context.unix_socket:
        tree.body.append(
            ast.Assign(
                targets=[ast.Name(id="client")],
                value=_make_client_constructor(parsed_context.unix_socket),
            )
        )
        func_call_id = ast.Name(id="client")

    # Create the base function call node
    func_call = ast.Call(
        func=ast.Attribute(
            value=func_call_id,
            attr=parsed_context.method,
        ),
        args=[
            ast.Constant(value=parsed_context.url),
        ],
        keywords=[],
    )
    # Add httpx keyword arguments from kargs
    for k, v in sorted(kargs.items()):
        func_call.keywords.append(ast.keyword(arg=k, value=ast.Constant(value=v)))

    # Add constant values
    constant_values = {
        "content": parsed_context.content,
        "data": parsed_context.form_data,
        "json": parsed_context.json,
        "params": parsed_context.params,
    }
    for key, value in constant_values.items():
        if value:
            func_call.keywords.append(ast.keyword(arg=key, value=ast.Constant(value=value)))
    # headers
    func_call.keywords.append(_handle_headers(parsed_context.headers, tuple_as_list=True))

    # Add dictionary values
    dict_values: dict[str, dict[str, str] | None] = {
        "cookies": parsed_context.cookies or {},
        "proxy": parsed_context.proxy or None,
    }
    for key, value in dict_values.items():
        if value is not None:
            func_call.keywords.append(
                ast.keyword(
                    arg=key,
                    value=ast.Constant(value=dict(value)),
                )
            )

    # Add tuple values
    if parsed_context.auth:
        func_call.keywords.append(
            ast.keyword(
                arg="auth",
                value=ast.Tuple(elts=[ast.Constant(v) for v in parsed_context.auth]),
            )
        )
    # add auth line
    if not parsed_context.verify:
        func_call.keywords.append(ast.keyword(arg="verify", value=ast.Constant(False)))
    # Convert the AST to Python code
    return ast.unparse(func_call)  # Python 3.9+


def _handle_headers(headers: Union[dict, list[tuple[str, str]]], tuple_as_list: bool = False) -> ast.keyword:
    if not headers:
        return ast.keyword(arg="headers", value=ast.Constant(dict()))
    headers = _maybe_sort_headers(headers, skip=True)
    if isinstance(headers, dict):
        return ast.keyword(
            arg="headers",
            value=ast.Constant(dict(headers)),
        )
    elif isinstance(headers, list):
        _inner_type = ast.List if tuple_as_list else ast.Tuple
        return ast.keyword(
            arg="headers",
            value=ast.List(
                elts=[_inner_type(elts=[ast.Constant(k), ast.Constant(v)]) for k, v in headers],
            ),
        )


def _maybe_sort_headers(
    headers: dict | list[tuple[str, str]], skip: bool = False
) -> Union[dict, list[tuple[str, str]]]:
    if skip:
        return type(headers)(headers)  # Return copy in place, preserving type, but not sorting
    if isinstance(headers, dict):
        return dict(sorted(headers.items(), key=lambda item: item[0].lower()))
    elif isinstance(headers, list):
        return sorted(headers, key=lambda item: item[0].lower())
    else:
        raise ValueError("Headers must be a dictionary or a list of tuples.")


def _make_client_constructor(uds: str) -> ast.Call:
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="httpx"),
            attr="Client",
        ),
        keywords=[
            ast.keyword(
                arg="transport",
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id="httpx"), attr="HTTPTransport"),
                    keywords=[ast.keyword(arg="uds", value=ast.Constant(value=uds))],
                ),
            ),
        ],
    )
