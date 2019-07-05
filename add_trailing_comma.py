from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import ast
import collections
import io
import sys
import warnings
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union

from tokenize_rt import ESCAPED_NL
from tokenize_rt import NON_CODING_TOKENS
from tokenize_rt import Offset
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src
from tokenize_rt import UNIMPORTANT_WS


Call = collections.namedtuple('Call', ('node', 'star_args', 'arg_offsets'))
Func = collections.namedtuple('Func', ('node', 'star_args', 'arg_offsets'))
Class = collections.namedtuple('Class', ('node', 'star_args', 'arg_offsets'))
Fix = collections.namedtuple(
    'Fix', ('braces', 'multi_arg', 'remove_comma', 'initial_indent'),
)

NEWLINES = frozenset((ESCAPED_NL, 'NEWLINE', 'NL'))
INDENT_TOKENS = frozenset(('INDENT', UNIMPORTANT_WS))
START_BRACES = frozenset(('(', '{', '['))
END_BRACES = frozenset((')', '}', ']'))


def ast_parse(contents_text):
    # type: (str) -> ast.Module
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents_text.encode('UTF-8'))


def _to_offset(node):
    # type: (ast.AST) -> Offset
    candidates = [node]
    while candidates:
        candidate = candidates.pop()
        if hasattr(candidate, 'lineno'):
            return Offset(candidate.lineno, candidate.col_offset)
        elif hasattr(candidate, '_fields'):  # pragma: no cover (PY35+)
            for field in reversed(candidate._fields):
                candidates.append(getattr(candidate, field))
    else:
        raise AssertionError(node)


if sys.version_info < (3, 5):  # pragma: no cover (<PY35)
    def _is_star_arg(node):
        # type: (ast.AST) -> bool
        return False
else:  # pragma: no cover (PY35+)
    def _is_star_arg(node):
        # type: (ast.AST) -> bool
        return isinstance(node, ast.Starred)


def _is_star_star_kwarg(node):
    # type: (ast.AST) -> bool
    return isinstance(node, ast.keyword) and node.arg is None


class FindNodes(ast.NodeVisitor):
    def __init__(self):
        # type: () -> None
        # multiple calls can report their starting position as the same
        self.calls = collections.defaultdict(
            list,
        )  # type: Dict[Offset, List[Call]]
        self.funcs = {}  # type: Dict[Offset, Func]
        self.literals = {}  # type: Dict[Offset, ast.expr]
        self.tuples = {}  # type: Dict[Offset, ast.Tuple]
        self.imports = set()  # type: Set[Offset]
        self.classes = {}  # type: Dict[Offset, Class]

    def _visit_literal(self, node, key='elts'):
        # type: (ast.expr, str) -> None
        if getattr(node, key):
            self.literals[_to_offset(node)] = node
        self.generic_visit(node)

    visit_Set = visit_List = _visit_literal

    def visit_Dict(self, node):
        # type: (ast.Dict) -> None
        self._visit_literal(node, key='values')

    def visit_Tuple(self, node):
        # type: (ast.Tuple) -> None
        if node.elts:
            # in < py38 tuples lie about offset -- later we must backtrack
            if sys.version_info < (3, 8):  # pragma: no cover (<py38)
                self.tuples[_to_offset(node)] = node
            else:  # pragma: no cover (py38+)
                self.literals[_to_offset(node)] = node
        self.generic_visit(node)

    def visit_Call(self, node):
        # type: (ast.Call) -> None
        argnodes = []  # type: List[ast.AST]
        argnodes.extend(node.args)
        argnodes.extend(node.keywords)
        py2_starargs = getattr(node, 'starargs', None)
        if py2_starargs:  # pragma: no cover (<PY35)
            argnodes.append(py2_starargs)
        py2_kwargs = getattr(node, 'kwargs', None)
        if py2_kwargs:  # pragma: no cover (<PY35)
            argnodes.append(py2_kwargs)

        arg_offsets = set()
        has_starargs = bool(py2_starargs or py2_kwargs)
        for argnode in argnodes:
            if (
                    _is_star_arg(argnode) or
                    _is_star_star_kwarg(argnode)
            ):  # pragma: no cover (PY35+)
                has_starargs = True

            offset = _to_offset(argnode)
            # multiline strings have invalid position, ignore them
            if offset.utf8_byte_offset != -1:  # pragma: no branch (cpy bug)
                arg_offsets.add(offset)

        # If the sole argument is a generator, don't add a trailing comma as
        # this breaks lib2to3 based tools
        only_a_generator = (
            len(argnodes) == 1 and isinstance(argnodes[0], ast.GeneratorExp)
        )

        if arg_offsets and not only_a_generator:
            key = _to_offset(node)
            self.calls[key].append(Call(node, has_starargs, arg_offsets))

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> None
        has_starargs = False
        args = list(node.args.args)

        if node.args.vararg:
            if isinstance(node.args.vararg, ast.AST):  # pragma: no cover (py3)
                args.append(node.args.vararg)
            has_starargs = True
        if node.args.kwarg:
            if isinstance(node.args.kwarg, ast.AST):  # pragma: no cover (py3)
                args.append(node.args.kwarg)
            has_starargs = True
        py3_kwonlyargs = getattr(node.args, 'kwonlyargs', None)
        if py3_kwonlyargs:  # pragma: no cover (py3)
            args.extend(py3_kwonlyargs)
            has_starargs = True

        arg_offsets = {_to_offset(arg) for arg in args}

        if arg_offsets:
            key = _to_offset(node)
            self.funcs[key] = Func(node, has_starargs, arg_offsets)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # type: (ast.ImportFrom) -> None
        self.imports.add(_to_offset(node))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # type: (ast.ClassDef) -> None
        # starargs are allowed in py3 class definitions, py35+ allows trailing
        # commas.  py34 does not, but adding an option for this very obscure
        # case seems not worth it.
        has_starargs = False
        args = list(node.bases)
        args.extend(getattr(node, 'keywords', ()))  # py3 only
        arg_offsets = {_to_offset(arg) for arg in args}

        if arg_offsets:
            key = _to_offset(node)
            self.classes[key] = Class(node, has_starargs, arg_offsets)

        self.generic_visit(node)


def _find_simple(first_brace, tokens):
    # type: (int, Sequence[Token]) -> Optional[Fix]
    brace_stack = [first_brace]
    multi_arg = False

    for i in range(first_brace + 1, len(tokens)):
        token = tokens[i]
        if token.src in START_BRACES:
            brace_stack.append(i)
        elif token.src in END_BRACES:
            brace_stack.pop()

        if len(brace_stack) == 1 and token.src == ',':
            multi_arg = True

        if not brace_stack:
            break
    else:
        raise AssertionError('Past end?')

    last_brace = i

    # Check if we're actually multi-line
    if (
            # we were single line, but with an extra comma and or whitespace
            tokens[first_brace].line == tokens[last_brace].line and (
                tokens[last_brace - 1].name == UNIMPORTANT_WS or
                tokens[last_brace - 1].src == ','
            )
    ):
        remove_comma = True
    elif tokens[first_brace].line == tokens[last_brace].line:
        return None
    else:
        remove_comma = False

    # determine the initial indentation
    i = first_brace
    while i >= 0 and tokens[i].name not in NEWLINES:
        i -= 1

    if i >= 0 and tokens[i + 1].name in INDENT_TOKENS:
        initial_indent = len(tokens[i + 1].src)
    else:
        initial_indent = 0

    return Fix(
        (first_brace, last_brace),
        multi_arg=multi_arg,
        remove_comma=remove_comma,
        initial_indent=initial_indent,
    )


def _find_call(call, i, tokens):
    # type: (Union[Call, Class, Func], int, Sequence[Token]) -> Optional[Fix]
    # When we get a `call` object, the ast refers to it as this:
    #
    #     func_name(arg, arg, arg)
    #     ^ where ast points
    #
    # We care about the closing paren, in order to find it, we first walk
    # until we find an argument.  When we find an argument, we know the outer
    # paren we find is the function call paren
    #
    #     func_name(arg, arg, arg)
    #              ^ outer paren
    first_brace = None
    paren_stack = []
    for i in range(i, len(tokens)):
        token = tokens[i]
        if token.src == '(':
            paren_stack.append(i)
        # the ast lies to us about the beginning of parenthesized functions.
        # See #3. (why we make sure there's something to pop here)
        elif token.src == ')' and paren_stack:
            paren_stack.pop()

        if (token.line, token.utf8_byte_offset) in call.arg_offsets:
            first_brace = paren_stack[0]
            break
    else:
        raise AssertionError('Past end?')

    return _find_simple(first_brace, tokens)


def _find_tuple(i, tokens):  # pragma: no cover (<py38)
    # type: (int, Sequence[Token]) -> Optional[Fix]
    # tuples are evil, we need to backtrack to find the opening paren
    i -= 1
    while tokens[i].name in NON_CODING_TOKENS:
        i -= 1
    # Sometimes tuples don't even have a paren!
    # x = 1, 2, 3
    if tokens[i].src != '(':
        return None

    return _find_simple(i, tokens)


def _find_import(i, tokens):
    # type: (int, List[Token]) -> Optional[Fix]
    # progress forwards until we find either a `(` or a newline
    for i in range(i, len(tokens)):
        token = tokens[i]
        if token.name == 'NEWLINE':
            return None
        elif token.name == 'OP' and token.src == '(':
            return _find_simple(i, tokens)
    else:
        raise AssertionError('Past end?')


def _fix_brace(tokens, fix_data, add_comma, remove_comma):
    # type: (List[Token], Optional[Fix], bool, bool) -> None
    if fix_data is None:
        return
    first_brace, last_brace = fix_data.braces

    # Figure out if either of the braces are "hugging"
    hug_open = tokens[first_brace + 1].name not in NON_CODING_TOKENS
    hug_close = tokens[last_brace - 1].name not in NON_CODING_TOKENS
    if (
            # Don't unhug single element things with a multi-line component
            # inside.
            not fix_data.multi_arg and
            tokens[first_brace + 1].src in START_BRACES and
            tokens[last_brace - 1].src in END_BRACES or
            # Don't unhug when containing a single token (such as a triple
            # quoted string).
            first_brace + 2 == last_brace or
            # don't unhug if it is a single line
            fix_data.remove_comma
    ):
        hug_open = hug_close = False

    # fix open hugging
    if hug_open:
        new_indent = fix_data.initial_indent + 4

        tokens[first_brace + 1:first_brace + 1] = [
            Token('NL', '\n'), Token(UNIMPORTANT_WS, ' ' * new_indent),
        ]
        last_brace += 2

        # Adust indentation for the rest of the things
        min_indent = None
        indents = []
        insert_indents = []
        for i in range(first_brace + 3, last_brace):
            if tokens[i - 1].name == 'NL' and tokens[i].name != 'NL':
                if tokens[i].name != UNIMPORTANT_WS:
                    min_indent = 0
                    insert_indents.append(i)
                else:
                    if min_indent is None:
                        min_indent = len(tokens[i].src)
                    elif len(tokens[i].src) < min_indent:
                        min_indent = len(tokens[i].src)
                    indents.append(i)

        assert min_indent is not None
        for i in indents:
            oldlen = len(tokens[i].src)
            newlen = oldlen - min_indent + new_indent
            tokens[i] = tokens[i]._replace(src=' ' * newlen)
        for i in reversed(insert_indents):
            tokens.insert(i, Token(UNIMPORTANT_WS, ' ' * new_indent))
            last_brace += 1

    # fix close hugging
    if hug_close:
        tokens[last_brace:last_brace] = [
            Token('NL', '\n'),
            Token(UNIMPORTANT_WS, ' ' * fix_data.initial_indent),
        ]
        last_brace += 2

    # From there, we can walk backwards and decide whether a comma is needed
    i = last_brace - 1
    while tokens[i].name in NON_CODING_TOKENS:
        i -= 1

    # If we're not a hugging paren, we can insert a comma
    if add_comma and tokens[i].src != ',' and i + 1 != last_brace:
        tokens.insert(i + 1, Token('OP', ','))

    # Fix trailing brace to match leading indentation
    back_1 = tokens[last_brace - 1]
    back_2 = tokens[last_brace - 2]
    if (
            back_1.name == UNIMPORTANT_WS and
            back_2.name == 'NL' and
            len(back_1.src) != fix_data.initial_indent
    ):
        new_indent = fix_data.initial_indent * ' '
        tokens[last_brace - 1] = back_1._replace(src=new_indent)

    if fix_data.remove_comma:
        start = last_brace
        if tokens[start - 1].name == UNIMPORTANT_WS:
            start -= 1
        if remove_comma and tokens[start - 1].src == ',':
            start -= 1
        del tokens[start:last_brace]


def _one_el_tuple(node):
    # type: (ast.expr) -> bool
    return isinstance(node, ast.Tuple) and len(node.elts) == 1


def _changing_list(lst):
    # type: (Sequence[Token]) -> Generator[Tuple[int, Token], None, None]
    i = 0
    while i < len(lst):
        yield i, lst[i]
        i += 1


def _fix_src(contents_text, py35_plus, py36_plus):
    # type: (str, bool, bool) -> str
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    visitor = FindNodes()
    visitor.visit(ast_obj)

    tokens = src_to_tokens(contents_text)
    for i, token in _changing_list(tokens):
        # DEDENT is a zero length token
        if not token.src:
            continue

        if token.offset in visitor.calls:
            for call in visitor.calls[token.offset]:
                # Only fix stararg calls if asked to
                add_comma = not call.star_args or py35_plus
                _fix_brace(
                    tokens, _find_call(call, i, tokens),
                    add_comma=add_comma,
                    remove_comma=True,
                )
        elif token.offset in visitor.funcs:
            func = visitor.funcs[token.offset]
            add_comma = not func.star_args or py36_plus
            # functions can be treated as calls
            _fix_brace(
                tokens, _find_call(func, i, tokens),
                add_comma=add_comma,
                remove_comma=True,
            )
        elif token.offset in visitor.classes:
            # classes can be treated as calls
            cls = visitor.classes[token.offset]
            _fix_brace(
                tokens, _find_call(cls, i, tokens),
                add_comma=True,
                remove_comma=True,
            )
        elif token.offset in visitor.literals and token.src in START_BRACES:
            _fix_brace(
                tokens, _find_simple(i, tokens),
                add_comma=True,
                remove_comma=not _one_el_tuple(visitor.literals[token.offset]),
            )
        elif token.offset in visitor.imports:
            # some imports do not have parens
            _fix_brace(
                tokens, _find_import(i, tokens),
                add_comma=True,
                remove_comma=True,
            )
        # Handle parenthesized things, unhug of tuples, and comprehensions
        elif token.src in START_BRACES:
            _fix_brace(
                tokens, _find_simple(i, tokens),
                add_comma=False,
                remove_comma=False,
            )

        # need to handle tuples afterwards as tuples report their starting
        # starting index as the first element, which may be one of the above
        # things.
        if token.offset in visitor.tuples:  # pragma: no cover (<py38)
            _fix_brace(
                tokens, _find_tuple(i, tokens),
                add_comma=True,
                remove_comma=not _one_el_tuple(visitor.tuples[token.offset]),
            )

    return tokens_to_src(tokens)


def fix_file(filename, args):
    # type: (str, argparse.Namespace) -> int
    if filename == '-':
        contents_bytes = getattr(sys.stdin, 'buffer', sys.stdin).read()
    else:
        with open(filename, 'rb') as fb:
            contents_bytes = fb.read()

    try:
        contents_text_orig = contents_text = contents_bytes.decode('UTF-8')
    except UnicodeDecodeError:
        msg = '{} is non-utf-8 (not supported)'.format(filename)
        print(msg, file=sys.stderr)
        return 1

    contents_text = _fix_src(contents_text, args.py35_plus, args.py36_plus)

    if filename == '-':
        print(contents_text, end='')
    elif contents_text != contents_text_orig:
        print('Rewriting {}'.format(filename), file=sys.stderr)
        with io.open(filename, 'w', newline='', encoding='UTF-8') as f:
            f.write(contents_text)

    if args.exit_zero_even_if_changed:
        return 0
    else:
        return contents_text != contents_text_orig


def main(argv=None):
    # type: (Optional[Sequence[str]]) -> int
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    parser.add_argument('--exit-zero-even-if-changed', action='store_true')
    parser.add_argument('--py35-plus', action='store_true')
    parser.add_argument('--py36-plus', action='store_true')
    args = parser.parse_args(argv)

    if args.py36_plus:
        args.py35_plus = True

    ret = 0
    for filename in args.filenames:
        ret |= fix_file(filename, args)
    return ret


if __name__ == '__main__':
    exit(main())
