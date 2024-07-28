from __future__ import annotations

import ast
import collections
import pkgutil
from collections.abc import Iterable
from typing import Callable
from typing import NamedTuple
from typing import Protocol
from typing import TypeVar

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma import _plugins


class State(NamedTuple):
    in_fstring: bool = False


AST_T = TypeVar('AST_T', bound=ast.AST)
TokenFunc = Callable[[int, list[Token]], None]
ASTFunc = Callable[[State, AST_T], Iterable[tuple[Offset, TokenFunc]]]

FUNCS: ASTCallbackMapping  # python/mypy#17566
FUNCS = collections.defaultdict(list)  # type: ignore[assignment]


def register(tp: type[AST_T]) -> Callable[[ASTFunc[AST_T]], ASTFunc[AST_T]]:
    def register_decorator(func: ASTFunc[AST_T]) -> ASTFunc[AST_T]:
        FUNCS[tp].append(func)
        return func
    return register_decorator


class ASTCallbackMapping(Protocol):
    def __getitem__(self, tp: type[AST_T]) -> list[ASTFunc[AST_T]]: ...


def visit(
        funcs: ASTCallbackMapping,
        tree: ast.AST,
) -> dict[Offset, list[TokenFunc]]:
    nodes = [(tree, State())]

    ret = collections.defaultdict(list)
    while nodes:
        node, state = nodes.pop()

        tp = type(node)
        for ast_func in funcs[tp]:
            for offset, token_func in ast_func(state, node):
                ret[offset].append(token_func)

        if tp is ast.FormattedValue:
            state = state._replace(in_fstring=True)

        for name in reversed(node._fields):
            value = getattr(node, name)
            if isinstance(value, ast.AST):
                nodes.append((value, state))
            elif isinstance(value, list):
                for value in reversed(value):
                    if isinstance(value, ast.AST):
                        nodes.append((value, state))
    return ret


def _import_plugins() -> None:
    # trigger an import of all of the plugins
    plugins_path = _plugins.__path__
    mod_infos = pkgutil.walk_packages(plugins_path, f'{_plugins.__name__}.')
    for _, name, _ in mod_infos:
        __import__(name, fromlist=['_trash'])


_import_plugins()
