from __future__ import annotations

import ast
import sys
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import register
from add_trailing_comma._data import State
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_simple
from add_trailing_comma._token_helpers import fix_brace


if sys.version_info >= (3, 9):  # pragma: >=3.9 cover
    def _fix_with(i: int, tokens: list[Token]) -> None:
        i += 1
        if tokens[i].name == 'UNIMPORTANT_WS':
            i += 1
        if tokens[i].src == '(':
            fix = find_simple(i, tokens)
            # only fix if outer parens are for the with items (next is ':')
            if fix is not None and tokens[fix.braces[-1] + 1].src == ':':
                fix_brace(tokens, fix, add_comma=True, remove_comma=True)

    @register(ast.With)
    def visit_With(
        state: State,
        node: ast.With,
    ) -> Iterable[tuple[Offset, TokenFunc]]:
        yield ast_to_offset(node), _fix_with
