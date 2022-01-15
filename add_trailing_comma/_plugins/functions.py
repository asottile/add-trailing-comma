from __future__ import annotations

import ast
import functools
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import register
from add_trailing_comma._data import State
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_call
from add_trailing_comma._token_helpers import fix_brace


def _fix_func(
        i: int,
        tokens: list[Token],
        *,
        add_comma: bool,
        arg_offsets: set[Offset],
) -> None:
    fix_brace(
        tokens,
        find_call(arg_offsets, i, tokens),
        add_comma=add_comma,
        remove_comma=True,
    )


def visit_FunctionDef(
        state: State,
        node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> Iterable[tuple[Offset, TokenFunc]]:
    has_starargs = False
    args = [*getattr(node.args, 'posonlyargs', ()), *node.args.args]

    if node.args.vararg:
        args.append(node.args.vararg)
        has_starargs = True
    if node.args.kwarg:
        args.append(node.args.kwarg)
        has_starargs = True
    if node.args.kwonlyargs:
        args.extend(node.args.kwonlyargs)
        has_starargs = True

    arg_offsets = {ast_to_offset(arg) for arg in args}

    if arg_offsets:
        func = functools.partial(
            _fix_func,
            add_comma=not has_starargs or state.min_version >= (3, 6),
            arg_offsets=arg_offsets,
        )
        yield ast_to_offset(node), func


register(ast.AsyncFunctionDef)(visit_FunctionDef)
register(ast.FunctionDef)(visit_FunctionDef)
