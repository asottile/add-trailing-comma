from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import ast
import collections
import io
import sys

from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src
from tokenize_rt import UNIMPORTANT_WS


Offset = collections.namedtuple('Offset', ('line', 'utf8_byte_offset'))
Node = collections.namedtuple('Node', ('node', 'star_args', 'arg_offsets'))

NON_CODING_TOKENS = frozenset(('COMMENT', 'NL', UNIMPORTANT_WS))


def ast_parse(contents_text):
    return ast.parse(contents_text.encode('UTF-8'))


def _to_offset(node):
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
        return False
else:  # pragma: no cover (PY35+)
    def _is_star_arg(node):
        return isinstance(node, ast.Starred)


def _is_star_star_kwarg(node):
    return isinstance(node, ast.keyword) and node.arg is None


class FindCalls(ast.NodeVisitor):
    def __init__(self):
        self.calls = {}
        self.has_new_syntax = False

    def visit_Call(self, node):
        orig = node.lineno

        argnodes = node.args + node.keywords
        py2_starargs = getattr(node, 'starargs', None)
        if py2_starargs:  # pragma: no cover (<PY35)
            argnodes.append(py2_starargs)
        py2_kwargs = getattr(node, 'kwargs', None)
        if py2_kwargs:  # pragma: no cover (<PY35)
            argnodes.append(py2_kwargs)

        arg_offsets = set()
        is_multiline = False
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
                if offset.line > orig:
                    is_multiline = True
                arg_offsets.add(offset)

        # If the sole argument is a generator, don't add a trailing comma as
        # this breaks lib2to3 based tools
        only_a_generator = (
            len(argnodes) == 1 and isinstance(argnodes[0], ast.GeneratorExp)
        )

        if is_multiline and not only_a_generator:
            key = Offset(node.lineno, node.col_offset)
            self.calls[key] = Node(node, has_starargs, arg_offsets)

        if (
                sum(_is_star_arg(n) for n in node.args) > 1 or
                sum(_is_star_star_kwarg(n) for n in node.keywords) > 1
        ):  # pragma: no cover (PY35+)
            self.has_new_syntax = True

        self.generic_visit(node)


def _fix_call(call, i, tokens):
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
    #
    # Once that is identified, walk until the paren stack is empty -- this will
    # put us at the last paren
    #
    #     func_name(arg, arg, arg)
    #                            ^ paren stack is empty
    first_paren = None
    paren_stack = []
    for i in range(i, len(tokens)):
        token = tokens[i]
        if token.src == '(':
            paren_stack.append(i)
        elif token.src == ')':
            paren_stack.pop()

        if (token.line, token.utf8_byte_offset) in call.arg_offsets:
            first_paren = paren_stack[0]

        if first_paren is not None and not paren_stack:
            break
    else:
        raise AssertionError('Past end?')

    # This was not actually a multi-line call, despite the ast telling us that
    if tokens[first_paren].line == tokens[i].line:
        return

    # From there, we can walk backwards and decide whether a comma is needed
    i -= 1
    while tokens[i].name in NON_CODING_TOKENS:
        i -= 1

    # If we're not a hugging paren, we can insert a comma
    if tokens[i].src != ',' and tokens[i + 1].src != ')':
        tokens.insert(i + 1, Token('OP', ','))


def _fix_calls(contents_text, py35_plus):
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    visitor = FindCalls()
    visitor.visit(ast_obj)

    tokens = src_to_tokens(contents_text)
    for i, token in reversed(tuple(enumerate(tokens))):
        key = Offset(token.line, token.utf8_byte_offset)
        if key in visitor.calls:
            call = visitor.calls[key]
            # Only fix stararg calls if asked to
            if not call.star_args or py35_plus or visitor.has_new_syntax:
                _fix_call(call, i, tokens)

    return tokens_to_src(tokens)


def fix_file(filename, args):
    with open(filename, 'rb') as f:
        contents_bytes = f.read()

    try:
        contents_text_orig = contents_text = contents_bytes.decode('UTF-8')
    except UnicodeDecodeError:
        print('{} is non-utf-8 (not supported)'.format(filename))
        return 1

    contents_text = _fix_calls(contents_text, args.py35_plus)

    if contents_text != contents_text_orig:
        print('Rewriting {}'.format(filename))
        with io.open(filename, 'w', encoding='UTF-8') as f:
            f.write(contents_text)
        return 1

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    parser.add_argument('--py35-plus', action='store_true')
    args = parser.parse_args(argv)

    ret = 0
    for filename in args.filenames:
        ret |= fix_file(filename, args)
    return ret


if __name__ == '__main__':
    exit(main())
