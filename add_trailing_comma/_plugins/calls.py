from __future__ import annotations

import ast
import functools
from collections.abc import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import register
from add_trailing_comma._data import State
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_call
from add_trailing_comma._token_helpers import fix_brace


def _fix_call(
        i: int,
        tokens: list[Token],
        *,
        arg_offsets: set[Offset],
) -> None:
    return fix_brace(
        tokens,
        find_call(arg_offsets, i, tokens),
        add_comma=True,
        remove_comma=True,
    )


@register(ast.Call)
def visit_Call(
        state: State,
        node: ast.Call,
) -> Iterable[tuple[Offset, TokenFunc]]:
    argnodes: list[ast.expr | ast.keyword] = [*node.args, *node.keywords]
    arg_offsets = set()
    for argnode in argnodes:
        offset = ast_to_offset(argnode)
        # multiline strings have invalid position, ignore them
        if offset.utf8_byte_offset != -1:  # pragma: no branch (cpy bug)
            arg_offsets.add(offset)

    # If the sole argument is a generator, don't add a trailing comma as
    # this breaks lib2to3 based tools
    only_a_generator = (
        len(argnodes) == 1 and isinstance(argnodes[0], ast.GeneratorExp)
    )

    if arg_offsets and not only_a_generator and not state.in_fstring:
        func = functools.partial(
            _fix_call,
            arg_offsets=arg_offsets,
        )
        yield ast_to_offset(node), func
