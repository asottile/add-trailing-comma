from __future__ import annotations

import ast
import warnings

from tokenize_rt import Offset


def ast_parse(contents_text: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents_text.encode())


def ast_to_offset(node: ast.AST) -> Offset:
    return Offset(node.lineno, node.col_offset)
