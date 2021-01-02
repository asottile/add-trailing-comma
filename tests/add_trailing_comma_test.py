import ast
import io
import sys
from unittest import mock

import pytest

from add_trailing_comma import _fix_src
from add_trailing_comma import main


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
        pytest.param(
            'x = (\n'
            '    f" {test(t)}"\n'
            ')\n',

            id='regression test for #106',
        ),
    ),
)
def test_fix_calls_noops(src):
    ret = _fix_src(src, py35_plus=False, py36_plus=False)
    assert ret == src


def _has_16806_bug():
    # See https://bugs.python.org/issue16806
    body = ast.parse('"""\n"""').body[0]
    assert isinstance(body, ast.Expr)
    return body.value.col_offset == -1


@pytest.mark.xfail(not _has_16806_bug(), reason='multiline string parse bug')
def test_ignores_invalid_ast_node():
    src = (
        'x(\n'
        '    """\n'
        '    """\n'
        ')'
    )
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


def test_py35_plus_rewrite():
    src = (
        'x(\n'
        '    *args\n'
        ')'
    )
    ret = _fix_src(src, py35_plus=True, py36_plus=False)
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
    ),
)
def test_fixes_calls(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.parametrize(
    'src',
    (
        '(1, 2, 3, 4)',
        '[1, 2, 3, 4]',
        '{1, 2, 3, 4}',
        '{1: 2, 3: 4}',
        # Regression test for #26
        'if True:\n'
        '    pass\n'
        '[x] = {y}',
        pytest.param('x[1, 2, 3, 4]', id='multi-slice'),
    ),
)
def test_noop_literals(src):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


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
        pytest.param(
            'x[\n'
            '    1,\n'
            '    2,\n'
            '    3\n'
            ']',
            'x[\n'
            '    1,\n'
            '    2,\n'
            '    3,\n'
            ']',
            id='multi-line multi-slice adds comma at end',
        ),
        pytest.param(
            'x[1, 2, 3, ]',
            'x[1, 2, 3]',
            id='single line with trailing comma with space removes comma',
        ),
        pytest.param(
            'x[1, 2, 3,]',
            'x[1, 2, 3]',
            id='single line with trailing comma with no space removes comma',
        ),
        pytest.param(
            'x[\n'
            '    (1,),\n'
            '    2,\n'
            '    3\n'
            ']',
            'x[\n'
            '    (1,),\n'
            '    2,\n'
            '    3,\n'
            ']',
            id='nested tuple',
        ),
    ),
)
def test_fixes_literals(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


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
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


def test_noop_tuple_literal_without_braces():
    src = (
        'x = \\\n'
        '    1, \\\n'
        '    2, \\\n'
        '    3'
    )
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


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
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


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
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'def f(\n'
            '    *args\n'
            '): pass',

            'def f(\n'
            '    *args,\n'
            '): pass',
        ),
        (
            'def f(\n'
            '    **kwargs\n'
            '): pass',

            'def f(\n'
            '    **kwargs,\n'
            '): pass',
        ),
        (
            'def f(\n'
            '    *, kw=1\n'
            '): pass',

            'def f(\n'
            '    *, kw=1,\n'
            '): pass',
        ),
    ),
)
def test_fixes_defs_py36_plus(src, expected):
    assert _fix_src(src, py35_plus=True, py36_plus=True) == expected


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
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


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
            'f(a\n'
            ')',

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
        # Regression test for #29
        (
            'x = ([a,\n'
            '      b], None)',

            'x = (\n'
            '    [\n'
            '        a,\n'
            '        b,\n'
            '    ], None,\n'
            ')',
        ),
        # Regression test for #32
        (
            '[a()\n'
            '    for b in c\n'
            '    if (\n'
            '        d\n'
            '    )\n'
            ']',

            '[\n'
            '    a()\n'
            '    for b in c\n'
            '    if (\n'
            '        d\n'
            '    )\n'
            ']',
        ),
        pytest.param(
            'x = [x\n'
            '     for x in y()]\n',

            'x = [\n'
            '    x\n'
            '    for x in y()\n'
            ']\n',

            id='#42: listcomp unhug ends in brace',
        ),
    ),
)
def test_fix_unhugs(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


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
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.xfail(sys.version_info < (3, 8), reason='py38+')
@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'def f(\n'
            '    x, /\n'
            '): pass\n',

            'def f(\n'
            '    x, /,\n'
            '): pass\n',
        ),
    ),
)
def test_fix_posonlyargs(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


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
        # Regression test for #79
        'if True:\n'
        '    if True:\n'
        '        pass\n'
        '\n'
        '    x = (\n'
        '    1,\n'
        '    )\n',
    ),
)
def test_noop_trailing_brace(src):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


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
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.parametrize(
    'src',
    (
        'from os import path, makedirs\n',
        'from os import (path, makedirs)\n',
        'from os import (\n'
        '    path,\n'
        '    makedirs,\n'
        ')',
    ),
)
def test_fix_from_import_noop(src):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'from os import (\n'
            '    makedirs,\n'
            '    path\n'
            ')',
            'from os import (\n'
            '    makedirs,\n'
            '    path,\n'
            ')',
        ),
        (
            'from os import \\\n'
            '   (\n'
            '        path,\n'
            '        makedirs\n'
            '   )\n',
            'from os import \\\n'
            '   (\n'
            '        path,\n'
            '        makedirs,\n'
            '   )\n',
        ),
        (
            'from os import (\n'
            '    makedirs,\n'
            '    path,\n'
            '    )',
            'from os import (\n'
            '    makedirs,\n'
            '    path,\n'
            ')',
        ),
        (
            'if True:\n'
            '    from os import (\n'
            '        makedirs\n'
            '    )',
            'if True:\n'
            '    from os import (\n'
            '        makedirs,\n'
            '    )',
        ),
    ),
)
def test_fix_from_import(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.parametrize(
    'src',
    (
        'class C: pass',
        'class C(): pass',
        'class C(object): pass',
        'class C(\n'
        '    object,\n'
        '): pass',
    ),
)
def test_fix_classes_noop(src):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == src


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'class C(\n'
            '    object\n'
            '): pass',
            'class C(\n'
            '    object,\n'
            '): pass',
        ),
    ),
)
def test_fix_classes(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        # can't rewrite 1-element tuple
        ('(1,)', '(1,)'),
        # but I do want the whitespace fixed!
        ('(1, )', '(1,)'),
        ('(1, 2,)', '(1, 2)'),
        ('[1, 2,]', '[1, 2]'),
        ('[1, 2,   ]', '[1, 2]'),
        ('{1, 2, }', '{1, 2}'),
        ('{1: 2, }', '{1: 2}'),
        ('f(1, 2,)', 'f(1, 2)'),
    ),
)
def test_remove_extra_comma(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        (
            'bases = (object,)\n'
            'class C(\n'
            '    *bases\n'
            '): pass',
            'bases = (object,)\n'
            'class C(\n'
            '    *bases,\n'
            '): pass',
        ),
        (
            'kws = {"metaclass": type}\n'
            'class C(\n'
            '    **kws\n'
            '): pass',
            'kws = {"metaclass": type}\n'
            'class C(\n'
            '    **kws,\n'
            '): pass',
        ),
        (
            'class C(\n'
            '    metaclass=type\n'
            '): pass',
            'class C(\n'
            '    metaclass=type,\n'
            '): pass',
        ),
    ),
)
def test_fix_classes_py3_only_syntax(src, expected):
    assert _fix_src(src, py35_plus=False, py36_plus=False) == expected


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
    _, err = capsys.readouterr()
    assert err == f'Rewriting {f}\n'
    assert f.read() == 'x(\n    1,\n)\n'


def test_main_preserves_line_endings(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary(b'x(\r\n    1\r\n)\r\n')
    assert main((f.strpath,)) == 1
    _, err = capsys.readouterr()
    assert err == f'Rewriting {f}\n'
    assert f.read_binary() == b'x(\r\n    1,\r\n)\r\n'


def test_main_syntax_error(tmpdir):
    f = tmpdir.join('f.py')
    f.write('from __future__ import print_function\nprint 1\n')
    assert main((f.strpath,)) == 0


def test_main_non_utf8_bytes(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary('# -*- coding: cp1252 -*-\nx = €\n'.encode('cp1252'))
    assert main((f.strpath,)) == 1
    _, err = capsys.readouterr()
    assert err == f'{f} is non-utf-8 (not supported)\n'


def test_main_py27_syntaxerror_coding(tmpdir):
    f = tmpdir.join('f.py')
    f.write('# -*- coding: utf-8 -*-\n[1, 2,]\n')
    assert main((f.strpath,)) == 1
    assert f.read() == '# -*- coding: utf-8 -*-\n[1, 2]\n'


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


def test_main_py36_plus_implies_py35_plus(tmpdir):
    f = tmpdir.join('f.py')
    f.write('x(\n    **kwargs\n)\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'x(\n    **kwargs\n)\n'
    assert main((f.strpath, '--py36-plus')) == 1
    assert f.read() == 'x(\n    **kwargs,\n)\n'


def test_main_py36_plus_function_trailing_commas(tmpdir):
    f = tmpdir.join('f.py')
    f.write('def f(\n    **kwargs\n): pass\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'def f(\n    **kwargs\n): pass\n'
    assert main((f.strpath, '--py36-plus')) == 1
    assert f.read() == 'def f(\n    **kwargs,\n): pass\n'


def test_main_stdin_no_changes(capsys):
    stdin = io.TextIOWrapper(io.BytesIO(b'x = 5\n'), 'UTF-8')
    with mock.patch.object(sys, 'stdin', stdin):
        assert main(('-',)) == 0
    out, err = capsys.readouterr()
    assert out == 'x = 5\n'


def test_main_stdin_with_changes(capsys):
    stdin = io.TextIOWrapper(io.BytesIO(b'x(\n    1\n)\n'), 'UTF-8')
    with mock.patch.object(sys, 'stdin', stdin):
        assert main(('-',)) == 1
    out, err = capsys.readouterr()
    assert out == 'x(\n    1,\n)\n'


def test_main_exit_zero_even_if_changed(tmpdir):
    f = tmpdir.join('t.py')
    f.write('x(\n    1\n)')
    assert not main((str(f), '--exit-zero-even-if-changed'))
    assert f.read() == 'x(\n    1,\n)'
    assert not main((str(f), '--exit-zero-even-if-changed'))
