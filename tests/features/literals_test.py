from __future__ import annotations

import pytest

from add_trailing_comma._main import _fix_src


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
        pytest.param(
            'x = (\n'
            '    object\n'
            '), object\n',
            id='regression test for #153',
        ),
    ),
)
def test_noop_literals(src):
    assert _fix_src(src) == src


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
    assert _fix_src(src) == expected


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
    assert _fix_src(src) == expected


def test_noop_tuple_literal_without_braces():
    src = (
        'x = \\\n'
        '    1, \\\n'
        '    2, \\\n'
        '    3'
    )
    assert _fix_src(src) == src
