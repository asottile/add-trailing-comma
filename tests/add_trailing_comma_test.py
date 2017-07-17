# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import ast
import sys

import pytest

from add_trailing_comma import _fix_src
from add_trailing_comma import main


xfailif_py2 = pytest.mark.xfail(sys.version_info < (3,), reason='py3+')
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
    ret = _fix_src(src, py35_plus=False)
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
    assert _fix_src(src, py35_plus=False) == src


def test_py35_plus_rewrite():
    src = (
        'x(\n'
        '    *args\n'
        ')'
    )
    ret = _fix_src(src, py35_plus=True)
    assert ret == (
        'x(\n'
        '    *args,\n'
        ')'
    )


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
        # Regression test for #22
        (
            'x({}).y(\n'
            '    x\n'
            ')',

            'x({}).y(\n'
            '    x,\n'
            ')',
        ),
        # Regression test for #23
        (
            '(\n'
            '    {k: v},\n'
            '    ()\n'
            ')',

            '(\n'
            '    {k: v},\n'
            '    (),\n'
            ')',
        ),
    ),
)
def test_fixes_calls(src, expected):
    assert _fix_src(src, py35_plus=False) == expected


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
    assert _fix_src(src, py35_plus=False) == src


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
    assert _fix_src(src, py35_plus=False) == expected


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
    assert _fix_src(src, py35_plus=False) == expected


def test_noop_tuple_literal_without_braces():
    src = (
        'x = \\\n'
        '    1, \\\n'
        '    2, \\\n'
        '    3'
    )
    assert _fix_src(src, py35_plus=False) == src


@pytest.mark.parametrize(
    'src',
    (
        'def f(): pass',
        'def f(arg1, arg2): pass',
        'def f(\n'
        '        arg1,\n'
        '        arg2,\n'
        '): pass',
        # *args forbid trailing commas
        'def f(\n'
        '        *args\n'
        '): pass',
        # **kwargs forbid trailing commas
        'def f(\n'
        '        **kwargs\n'
        '): pass',
        # keyword-only args forbid trailing commas (or are py2 syntax error)
        'def f(\n'
        '        *, arg=1\n'
        '): pass',
    ),
)
def test_noop_function_defs(src):
    assert _fix_src(src, py35_plus=False) == src


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'def f(\n'
            '        x\n'
            '): pass',

            'def f(\n'
            '        x,\n'
            '): pass',
        ),
    ),
)
def test_fixes_defs(src, expected):
    assert _fix_src(src, py35_plus=False) == expected


@pytest.mark.parametrize(
    'src',
    (
        'f(x, y, z)',
        'f(\n'
        '    x,\n'
        ')',
        # Single argument, don't unhug
        'f((\n'
        '    1, 2, 3,\n'
        '))',
        'f([\n'
        '    1, 2, 3,\n'
        '])',
        # Single triple-quoted-string argument, don't unhug
        'textwrap.dedent("""\n'
        '    hi\n'
        '""")',
    ),
)
def test_noop_unhugs(src):
    assert _fix_src(src, py35_plus=False) == src


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'f(\n'
            '    a)',

            'f(\n'
            '    a,\n'
            ')',
        ),
        (
            'f(a,\n'
            '  b,\n'
            ')',

            'f(\n'
            '    a,\n'
            '    b,\n'
            ')',
        ),
        (
            'f(a,\n'
            '  b,\n'
            '  c)',

            'f(\n'
            '    a,\n'
            '    b,\n'
            '    c,\n'
            ')',
        ),
        (
            'def f(\n'
            '    *args): pass',

            'def f(\n'
            '    *args\n'
            '): pass',
        ),
        (
            'def f(\n'
            '    **kwargs): pass',

            'def f(\n'
            '    **kwargs\n'
            '): pass',
        ),
        # if there's already a trailing comma, don't add a new one
        (
            'f(\n'
            '    a,)',

            'f(\n'
            '    a,\n'
            ')',
        ),
        (
            'with a(\n'
            '    b,\n'
            '    c):\n'
            '    pass',

            'with a(\n'
            '    b,\n'
            '    c,\n'
            '):\n'
            '    pass',
        ),
        (
            'if True:\n'
            '    with a(\n'
            '        b,\n'
            '        c):\n'
            '        pass',

            'if True:\n'
            '    with a(\n'
            '        b,\n'
            '        c,\n'
            '    ):\n'
            '        pass',
        ),
        (
            "{'foo': 'bar',\n"
            " 'baz':\n"
            '    {\n'
            "       'id': 1,\n"
            ' },\n'
            ' }',

            '{\n'
            "    'foo': 'bar',\n"
            "    'baz':\n"
            '       {\n'
            "          'id': 1,\n"
            '       },\n'
            '}',
        ),
        (
            'f(g(\n'
            '      a,\n'
            '  ),\n'
            '  1,\n'
            ')',

            'f(\n'
            '    g(\n'
            '        a,\n'
            '    ),\n'
            '    1,\n'
            ')',
        ),
        (
            'f(\n'
            '    *args)',

            'f(\n'
            '    *args\n'
            ')',
        ),
        (
            '{"foo": a[0],\n'
            ' "bar": a[1]}',

            '{\n'
            '    "foo": a[0],\n'
            '    "bar": a[1],\n'
            '}',
        ),
        (
            'x = (f(\n'
            '    a,\n'
            '), f(\n'
            '    a,\n'
            '))',

            'x = (\n'
            '    f(\n'
            '        a,\n'
            '    ), f(\n'
            '        a,\n'
            '    ),\n'
            ')',
        ),
        (
            'x = [long_function_name(arg,\n'
            '                        arg),\n'
            '     long_function_name(arg,\n'
            '                        arg)]',

            'x = [\n'
            '    long_function_name(\n'
            '        arg,\n'
            '        arg,\n'
            '    ),\n'
            '    long_function_name(\n'
            '        arg,\n'
            '        arg,\n'
            '    ),\n'
            ']',
        ),
        (
            'x = ("foo"\n'
            '     "bar")',

            'x = (\n'
            '    "foo"\n'
            '    "bar"\n'
            ')',
        ),
        # Regression test for #17
        (
            'x("foo", (\n'
            '    "bar",\n'
            '\n'
            '    "baz",\n'
            '))',

            'x(\n'
            '    "foo", (\n'
            '        "bar",\n'
            '\n'
            '        "baz",\n'
            '    ),\n'
            ')',
        ),
        # Regression test for #16
        (
            'x("foo"\n'
            '  "bar")',

            'x(\n'
            '    "foo"\n'
            '    "bar",\n'
            ')',
        ),
    ),
)
def test_fix_unhugs(src, expected):
    assert _fix_src(src, py35_plus=False) == expected


@xfailif_py2
@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        # python 2 doesn't kwonlyargs
        (
            'def f(\n'
            '    *, kw=1, kw2=2): pass',

            'def f(\n'
            '    *, kw=1, kw2=2\n'
            '): pass',
        ),
    ),
)
def test_fix_unhugs_py3_only(src, expected):
    assert _fix_src(src, py35_plus=False) == expected


@pytest.mark.parametrize(
    'src',
    (
        '[]',
        'x = [\n'
        '    1, 2, 3,\n'
        ']',
        'y = [\n'
        '    [\n'
        '        1, 2, 3, 4,\n'
        '    ],\n'
        ']',
        # Regression test for #11
        'foo.\\\n'
        '    bar(\n'
        '        5,\n'
        '    )',
    ),
)
def test_noop_trailing_brace(src):
    assert _fix_src(src, py35_plus=False) == src


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'x = [\n'
            '    1,\n'
            '    ]',

            'x = [\n'
            '    1,\n'
            ']',
        ),
        (
            'x % (\n'
            '    f(\n'
            '        a,\n'
            '    ),\n'
            '    )',

            'x % (\n'
            '    f(\n'
            '        a,\n'
            '    ),\n'
            ')',
        ),
        (
            'x = (\n'
            '    "foo"\n'
            '    "bar"\n'
            '    )',

            'x = (\n'
            '    "foo"\n'
            '    "bar"\n'
            ')',
        ),
    ),
)
def test_fix_trailing_brace(src, expected):
    assert _fix_src(src, py35_plus=False) == expected


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
