import sys

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
    assert _fix_src(src, min_version=(2, 7)) == src


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
    assert _fix_src(src, min_version=(2, 7)) == expected


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
    assert _fix_src(src, min_version=(3, 6)) == expected


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
    assert _fix_src(src, min_version=(2, 7)) == expected
