import ast
import functools
from typing import Iterable
from typing import List
from typing import Set
from typing import Tuple

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma._ast_helpers import ast_to_offset
from add_trailing_comma._data import ParseState
from add_trailing_comma._data import register
from add_trailing_comma._data import TokenFunc
from add_trailing_comma._token_helpers import find_call
from add_trailing_comma._token_helpers import fix_brace


def _fix_class(
        i: int,
        tokens: List[Token],
        version: Tuple[int, ...],
        *,
        arg_offsets: Set[Offset],
) -> None:
    fix_brace(
        tokens,
        find_call(arg_offsets, i, tokens),
        add_comma=True,
        remove_comma=True,
    )


@register(ast.ClassDef)
def visit_ClassDef(
        parse_state: ParseState,
        node: ast.ClassDef,
) -> Iterable[Tuple[Offset, TokenFunc]]:
    # starargs are allowed in py3 class definitions, py35+ allows trailing
    # commas.  py34 does not, but adding an option for this very obscure
    # case seems not worth it.
    args = [*node.bases, *node.keywords]
    arg_offsets = {ast_to_offset(arg) for arg in args}

    if arg_offsets:
        func = functools.partial(_fix_class, arg_offsets=arg_offsets)
        yield ast_to_offset(node), func
