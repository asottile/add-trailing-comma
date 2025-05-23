from __future__ import annotations

import pytest

from add_trailing_comma._main import _fix_src


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
        # single triple-quoted fstring argument, don't unhug
        'textwrap.dedent(f"""\n'
        '    hi\n'
        '""")',
        # single triple-quoted tstring argument, don't unhug
        'textwrap.dedent(t"""\n'
        '    hi\n'
        '""")',
    ),
)
def test_noop_unhugs(src):
    assert _fix_src(src) == src


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
            '    *args,\n'
            '): pass',
        ),
        (
            'def f(\n'
            '    **kwargs): pass',

            'def f(\n'
            '    **kwargs,\n'
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
            '    *args,\n'
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
        (
            'def f(\n'
            '    *, kw=1, kw2=2): pass',

            'def f(\n'
            '    *, kw=1, kw2=2,\n'
            '): pass',
        ),
    ),
)
def test_fix_unhugs(src, expected):
    assert _fix_src(src) == expected
