from __future__ import annotations

import ast
import warnings
from typing import Protocol

from tokenize_rt import Offset


def ast_parse(contents_text: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents_text.encode())


class _HasOffsetInfo(Protocol):
    @property
    def lineno(self) -> int: ...
    @property
    def col_offset(self) -> int: ...


def ast_to_offset(node: _HasOffsetInfo) -> Offset:
    return Offset(node.lineno, node.col_offset)
