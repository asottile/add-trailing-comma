import ast
import functools
import sys
from typing import Iterable
from typing import List
from typing import Set
from typing import Tuple

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import register
from add_trailing_comma._data import State
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_call
from add_trailing_comma._token_helpers import find_simple
from add_trailing_comma._token_helpers import fix_brace


if sys.version_info >= (3, 10):  # pragma: no cover (py310+)
    def _fix_match_class(
            i: int,
            tokens: List[Token],
            *,
            arg_offsets: Set[Offset],
    ) -> None:
        return fix_brace(
            tokens,
            find_call(arg_offsets, i, tokens),
            add_comma=True,
            remove_comma=True,
        )

    @register(ast.MatchClass)
    def visit_MatchClass(
            state: State,
            node: ast.MatchClass,
    ) -> Iterable[Tuple[Offset, TokenFunc]]:
        arg_offsets = {ast_to_offset(pat) for pat in node.patterns}
        arg_offsets |= {ast_to_offset(pat) for pat in node.kwd_patterns}
        func = functools.partial(_fix_match_class, arg_offsets=arg_offsets)
        yield ast_to_offset(node), func

    def _fix_mapping(i: int, tokens: List[Token]) -> None:
        fix_brace(
            tokens,
            find_simple(i, tokens),
            add_comma=True,
            remove_comma=True,
        )

    def _fix_sequence(i: int, tokens: List[Token], *, n: int) -> None:
        remove_comma = tokens[i].src == '[' or n > 1
        fix_brace(
            tokens,
            find_simple(i, tokens),
            add_comma=True,
            remove_comma=remove_comma,
        )

    @register(ast.MatchMapping)
    def visit_MatchMapping(
            state: State,
            node: ast.MatchClass,
    ) -> Iterable[Tuple[Offset, TokenFunc]]:
        yield ast_to_offset(node), _fix_mapping

    @register(ast.MatchSequence)
    def visit_MatchSequence(
            state: State,
            node: ast.MatchClass,
    ) -> Iterable[Tuple[Offset, TokenFunc]]:
        func = functools.partial(_fix_sequence, n=len(node.patterns))
        yield ast_to_offset(node), func
