from __future__ import annotations

import ast
import sys
from collections.abc import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import register
from add_trailing_comma._data import State
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_simple
from add_trailing_comma._token_helpers import fix_brace


if sys.version_info >= (3, 12):  # pragma: >=3.12 cover
    def _fix_pep695(
        i: int,
        tokens: list[Token],
    ) -> None:
        for n in range(i, len(tokens)):
            token = tokens[n]
            if token.name == 'OP' and token.src == '[':
                return fix_brace(
                    tokens,
                    find_simple(n, tokens),
                    add_comma=True,
                    remove_comma=True,
                )
        else:
            raise AssertionError('Past end?')

    def visit_pep695(
        state: State,
        node: ast.TypeAlias | ast.ClassDef | ast.FunctionDef,
    ) -> Iterable[tuple[Offset, TokenFunc]]:
        if node.type_params:
            yield ast_to_offset(node), _fix_pep695

    register(ast.TypeAlias)(visit_pep695)
    register(ast.ClassDef)(visit_pep695)
    register(ast.FunctionDef)(visit_pep695)
