from __future__ import annotations

import pytest

from add_trailing_comma._main import _fix_src


@pytest.mark.parametrize(
    'src',
    (
        'def f(): pass',
        'def f(arg1, arg2): pass',
        'def f(\n'
        '        arg1,\n'
        '        arg2,\n'
        '): pass',
    ),
)
def test_noop_function_defs(src):
    assert _fix_src(src) == src


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
        pytest.param(
            'async def f(\n'
            '        x\n'
            '): pass',
            'async def f(\n'
            '        x,\n'
            '): pass',
            id='async def',
        ),
    ),
)
def test_fixes_defs(src, expected):
    assert _fix_src(src) == expected


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
    assert _fix_src(src) == expected


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
    assert _fix_src(src) == expected
