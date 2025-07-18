import ast
from typing import List, Union

import httpx

from .api import parse_context


def parse(curl_command: Union[str, List[str]], **kargs) -> str:
    parsed_context = parse_context(curl_command)
    tree = ast.Interactive()
    func_call_id = ast.Name(id="httpx", ctx=ast.Load())
    if parsed_context.unix_socket:
        tree.body.append(
            ast.Assign(
                targets=[ast.Name(id="client", ctx=ast.Store())],
                value=_make_client_constructor(parsed_context.unix_socket),
            )
        )
        func_call_id = ast.Name(id="client", ctx=ast.Load())

    # Create the base function call node
    func_call = ast.Call(
        func=ast.Attribute(
            value=func_call_id,
            attr=parsed_context.method,
            ctx=ast.Load(),
        ),
        args=[
            ast.Constant(value=parsed_context.url),
        ],
        keywords=[],
    )
    # Add httpx keyword arguments from kargs
    for k, v in kargs.items():
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

    # Add dictionary values
    dict_values: dict[str, dict[str, str] | None] = {
        "headers": parsed_context.headers or {},
        "cookies": parsed_context.cookies or {},
        "proxy": parsed_context.proxy or None,
    }
    for key, value in dict_values.items():
        if value is not None:
            func_call.keywords.append(
                ast.keyword(
                    arg=key,
                    value=ast.Constant(value=dict(value))
                    # ast.Dict(
                    #     keys=[ast.Constant(k) for k in value.keys()],
                    #     values=[ast.Constant(v) for v in value.values()],
                    # ),
                )
            )

    # Add tuple values
    if parsed_context.auth:
        func_call.keywords.append(
            ast.keyword(
                arg="auth",
                value=ast.Tuple(
                    elts=[ast.Constant(v) for v in parsed_context.auth],
                    ctx=ast.Load(),
                ),
            )
        )
    # add  auth line
    if not parsed_context.verify:
        func_call.keywords.append(ast.keyword(arg="verify", value=ast.Constant(False)))
    # Convert the AST to Python code
    return ast.unparse(func_call)  # Python 3.9+


def _make_client_constructor(uds: str) -> ast.Call:
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="httpx", ctx=ast.Load()),
            attr="Client",
            ctx=ast.Load(),
        ),
        keywords=[
            ast.keyword(
                arg="transport",
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="httpx", ctx=ast.Load()), attr="HttpTransport", ctx=ast.Load()
                    ),
                    keywords=[ast.keyword(arg="uds", value=ast.Constant(value=uds))],
                ),
            ),
        ],
    )
