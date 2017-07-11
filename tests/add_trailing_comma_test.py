# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import ast
import sys

import pytest

from add_trailing_comma import _fix_commas
from add_trailing_comma import main


xfailif_lt_py35 = pytest.mark.xfail(sys.version_info < (3, 5), reason='py35+')


@pytest.mark.parametrize(
    'src',
    (
        # No relevant multiline calls
        'x = 5',
        'x(1)',
        # Don't rewrite functions that have a single generator argument as
        # this breaks lib2to3 based tools.
        'tuple(\n'
        '    a for a in b\n'
        ')',
        # Don't rewrite *args or **kwargs unless --py35-plus
        'x(\n'
        '    *args\n'
        ')',
        'x(\n'
        '    **kwargs\n'
        ')',
        # The ast tells us that the inner call starts on line 2, but the first
        # paren (and last paren) are actually both on line 3.
        'x(\n'
        '    "foo"\n'
        '    "bar".format(1),\n'
        ')',
        # Don't add a comma when it's not at the end of a line
        'x((\n'
        '    1,\n'
        '))',
        # regression test for #3
        '(\n'
        '    a\n'
        ').f(b)',
    ),
)
def test_fix_calls_noops(src):
    ret = _fix_commas(src, py35_plus=False)
    assert ret == src


def _has_16806_bug():
    # See https://bugs.python.org/issue16806
    return ast.parse('"""\n"""').body[0].value.col_offset == -1


@pytest.mark.xfail(not _has_16806_bug(), reason='multiline string parse bug')
def test_ignores_invalid_ast_node():
    src = (
        'x(\n'
        '    """\n'
        '    """\n'
        ')'
    )
    assert _fix_commas(src, py35_plus=False) == src


def test_py35_plus_rewrite():
    src = (
        'x(\n'
        '    *args\n'
        ')'
    )
    ret = _fix_commas(src, py35_plus=True)
    assert ret == (
        'x(\n'
        '    *args,\n'
        ')'
    )


@xfailif_lt_py35
@pytest.mark.parametrize(
    'syntax',
    (
        '(1, 2, *a)\n',
        '[1, 2, *a]\n',
        '{1, 2, *a}\n',
        '{1: 2, **k}\n',
        'y(*args1, *args2)\n',
        'y(**kwargs1, **kwargs2)\n',
    ),
)
def test_auto_detected_py35_plus_rewrite(syntax):
    src = syntax + 'x(\n    *args\n)'
    expected = syntax + 'x(\n    *args,\n)'
    assert _fix_commas(src, py35_plus=False) == expected


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'x(\n'
            '    1\n'
            ')',

            'x(\n'
            '    1,\n'
            ')',
        ),
        (
            'x(\n'
            '    kwarg=5\n'
            ')',

            'x(\n'
            '    kwarg=5,\n'
            ')',
        ),
        (
            'foo()(\n'
            '    1\n'
            ')',

            'foo()(\n'
            '    1,\n'
            ')',
        ),
    ),
)
def test_fixes_calls(src, expected):
    assert _fix_commas(src, py35_plus=False) == expected


@pytest.mark.parametrize(
    'src',
    (
        '(1, 2, 3, 4)',
        '[1, 2, 3, 4]',
        '{1, 2, 3, 4}',
        '{1: 2, 3: 4}',
    ),
)
def test_noop_one_line_literals(src):
    assert _fix_commas(src, py35_plus=False) == src


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'x = [\n'
            '    1\n'
            ']',

            'x = [\n'
            '    1,\n'
            ']',
        ),
        (
            'x = {\n'
            '    1\n'
            '}',

            'x = {\n'
            '    1,\n'
            '}',
        ),
        (
            'x = {\n'
            '    1: 2\n'
            '}',

            'x = {\n'
            '    1: 2,\n'
            '}',
        ),
        (
            'x = (\n'
            '    1,\n'
            '    2\n'
            ')',

            'x = (\n'
            '    1,\n'
            '    2,\n'
            ')',
        ),
    ),
)
def test_fixes_literals(src, expected):
    assert _fix_commas(src, py35_plus=False) == expected


@xfailif_lt_py35
@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'x = {\n'
            '    1, *y\n'
            '}',

            'x = {\n'
            '    1, *y,\n'
            '}',
        ),
        (
            'x = [\n'
            '    1, *y\n'
            ']',

            'x = [\n'
            '    1, *y,\n'
            ']',
        ),
        (
            'x = (\n'
            '    1, *y\n'
            ')',

            'x = (\n'
            '    1, *y,\n'
            ')',
        ),
        (
            'x = {\n'
            '    1: 2, **y\n'
            '}',

            'x = {\n'
            '    1: 2, **y,\n'
            '}',
        ),
    ),
)
def test_fixes_py35_plus_literals(src, expected):
    assert _fix_commas(src, py35_plus=False) == expected


def test_noop_tuple_literal_without_braces():
    src = (
        'x = \\\n'
        '    1, \\\n'
        '    2, \\\n'
        '    3'
    )
    assert _fix_commas(src, py35_plus=False) == src


def test_main_trivial():
    assert main(()) == 0


def test_main_noop(tmpdir):
    f = tmpdir.join('f.py')
    f.write('x = 5\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'x = 5\n'


def test_main_changes_a_file(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write('x(\n    1\n)\n')
    assert main((f.strpath,)) == 1
    out, _ = capsys.readouterr()
    assert out == 'Rewriting {}\n'.format(f.strpath)
    assert f.read() == 'x(\n    1,\n)\n'


def test_main_syntax_error(tmpdir):
    f = tmpdir.join('f.py')
    f.write('from __future__ import print_function\nprint 1\n')
    assert main((f.strpath,)) == 0


def test_main_non_utf8_bytes(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary('# -*- coding: cp1252 -*-\nx = €\n'.encode('cp1252'))
    assert main((f.strpath,)) == 1
    out, _ = capsys.readouterr()
    assert out == '{} is non-utf-8 (not supported)\n'.format(f.strpath)


def test_main_py35_plus_argument_star_args(tmpdir):
    f = tmpdir.join('f.py')
    f.write('x(\n    *args\n)\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'x(\n    *args\n)\n'
    assert main((f.strpath, '--py35-plus')) == 1
    assert f.read() == 'x(\n    *args,\n)\n'


def test_main_py35_plus_argument_star_star_kwargs(tmpdir):
    f = tmpdir.join('f.py')
    f.write('x(\n    **args\n)\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'x(\n    **args\n)\n'
    assert main((f.strpath, '--py35-plus')) == 1
    assert f.read() == 'x(\n    **args,\n)\n'
