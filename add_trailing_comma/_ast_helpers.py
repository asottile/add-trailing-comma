from __future__ import annotations

import ast
import warnings

from tokenize_rt import Offset


def ast_parse(contents_text: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents_text.encode())


def ast_to_offset(node: ast.AST) -> Offset:
    candidates = [node]
    while candidates:
        candidate = candidates.pop()
        if hasattr(candidate, 'lineno'):
            return Offset(candidate.lineno, candidate.col_offset)
        elif hasattr(candidate, '_fields'):  # pragma: <3.9 cover
            for field in reversed(candidate._fields):
                candidates.append(getattr(candidate, field))
    else:
        raise AssertionError(node)
