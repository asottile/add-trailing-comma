from __future__ import annotations

import ast
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import register
from add_trailing_comma._data import State
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_simple
from add_trailing_comma._token_helpers import Fix
from add_trailing_comma._token_helpers import fix_brace


def _find_import(i: int, tokens: list[Token]) -> Fix | None:
    # progress forwards until we find either a `(` or a newline
    for i in range(i, len(tokens)):
        token = tokens[i]
        if token.name == 'NEWLINE':
            return None
        elif token.name == 'OP' and token.src == '(':
            return find_simple(i, tokens)
    else:
        raise AssertionError('Past end?')


def _fix_import(i: int, tokens: list[Token]) -> None:
    fix_brace(
        tokens,
        _find_import(i, tokens),
        add_comma=True,
        remove_comma=True,
    )


@register(ast.ImportFrom)
def visit_ImportFrom(
        state: State,
        node: ast.ImportFrom,
) -> Iterable[tuple[Offset, TokenFunc]]:
    yield ast_to_offset(node), _fix_import
