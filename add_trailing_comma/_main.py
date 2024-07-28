from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from collections.abc import Sequence

from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src

from add_trailing_comma._ast_helpers import ast_parse
from add_trailing_comma._data import FUNCS
from add_trailing_comma._data import visit
from add_trailing_comma._token_helpers import find_simple
from add_trailing_comma._token_helpers import fix_brace
from add_trailing_comma._token_helpers import START_BRACES


def _changing_list(lst: list[Token]) -> Iterable[tuple[int, Token]]:
    i = 0
    while i < len(lst):
        yield i, lst[i]
        i += 1


def _fix_src(contents_text: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    callbacks = visit(FUNCS, ast_obj)

    tokens = src_to_tokens(contents_text)
    for i, token in _changing_list(tokens):
        # DEDENT is a zero length token
        if not token.src:
            continue

        # though this is a defaultdict, by using `.get()` this function's
        # self time is almost 50% faster
        for callback in callbacks.get(token.offset, ()):
            callback(i, tokens)

        if token.name == 'OP' and token.src in START_BRACES:
            fix_brace(
                tokens, find_simple(i, tokens),
                add_comma=False,
                remove_comma=False,
            )

    return tokens_to_src(tokens)


def fix_file(filename: str, args: argparse.Namespace) -> int:
    if filename == '-':
        contents_bytes = sys.stdin.buffer.read()
    else:
        with open(filename, 'rb') as fb:
            contents_bytes = fb.read()

    try:
        contents_text_orig = contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        msg = f'{filename} is non-utf-8 (not supported)'
        print(msg, file=sys.stderr)
        return 1

    contents_text = _fix_src(contents_text)

    if filename == '-':
        print(contents_text, end='')
    elif contents_text != contents_text_orig:
        print(f'Rewriting {filename}', file=sys.stderr)
        with open(filename, 'wb') as f:
            f.write(contents_text.encode())

    if args.exit_zero_even_if_changed:
        return 0
    else:
        return contents_text != contents_text_orig


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    parser.add_argument('--exit-zero-even-if-changed', action='store_true')
    parser.add_argument('--py35-plus', action='store_true')
    parser.add_argument('--py36-plus', action='store_true')
    args = parser.parse_args(argv)

    if args.py35_plus or args.py36_plus:
        print('WARNING: --py35-plus / --py36-plus do nothing', file=sys.stderr)

    ret = 0
    for filename in args.filenames:
        ret |= fix_file(filename, args)
    return ret


if __name__ == '__main__':
    raise SystemExit(main())
