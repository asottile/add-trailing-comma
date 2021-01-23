import ast
import collections
import pkgutil
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

from tokenize_rt import Offset
from tokenize_rt import Token

from add_trailing_comma import _plugins

if TYPE_CHECKING:
    from typing import Protocol
else:
    Protocol = object


class ParseState(NamedTuple):
    in_fstring: bool = False


AST_T = TypeVar('AST_T', bound=ast.AST)
TokenFunc = Callable[[int, List[Token], Tuple[int, ...]], None]
ASTFunc = Callable[[ParseState, AST_T], Iterable[Tuple[Offset, TokenFunc]]]

FUNCS = collections.defaultdict(list)


def register(tp: Type[AST_T]) -> Callable[[ASTFunc[AST_T]], ASTFunc[AST_T]]:
    def register_decorator(func: ASTFunc[AST_T]) -> ASTFunc[AST_T]:
        FUNCS[tp].append(func)
        return func
    return register_decorator


class ASTCallbackMapping(Protocol):
    def __getitem__(self, tp: Type[AST_T]) -> List[ASTFunc[AST_T]]: ...


def visit(
        funcs: ASTCallbackMapping,
        tree: ast.AST,
) -> Dict[Offset, List[TokenFunc]]:
    nodes = [(tree, ParseState())]

    ret = collections.defaultdict(list)
    while nodes:
        node, parse_state = nodes.pop()

        tp = type(node)
        for ast_func in funcs[tp]:
            for offset, token_func in ast_func(parse_state, node):
                ret[offset].append(token_func)

        if tp is ast.FormattedValue:
            parse_state = parse_state._replace(in_fstring=True)

        for name in reversed(node._fields):
            value = getattr(node, name)
            if isinstance(value, ast.AST):
                nodes.append((value, parse_state))
            elif isinstance(value, list):
                for value in reversed(value):
                    if isinstance(value, ast.AST):
                        nodes.append((value, parse_state))
    return ret


# trigger an import of all of the plugins
# https://github.com/python/mypy/issues/1422
plugins_path: str = _plugins.__path__  # type: ignore
mod_infos = pkgutil.walk_packages(plugins_path, f'{_plugins.__name__}.')
for _, name, _ in mod_infos:
    __import__(name, fromlist=['_trash'])
