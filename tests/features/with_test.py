from __future__ import annotations

import sys

import pytest

from add_trailing_comma._main import _fix_src


@pytest.mark.parametrize(
    'src',
    (
        pytest.param(
            'from threading import Lock\n'
            'with (Lock() as l):\n'
            '    pass',
            id='simple named context manager',
        ),
        pytest.param(
            'with (\n'
            '    open("wat")\n'
            ') as f, open("2") as f2: pass',
            id='parenthesized expression',
        ),
        pytest.param(
            'with open("/tmp/t.py") as f: pass',
            id='old style',
        ),
        pytest.param(
            'with open("/tmp/t.py") as f, \\\n'
            '     open("/tmp/y.py") as g: pass',
            id='escaped newline',
        ),
        pytest.param(
            'with (open("/tmp/t.py") as f): pass',
            id='single item',
        ),
        pytest.param(
            'with (open("/tmp/t.py") as t, open("/tmp/y.py") as y): pass',
            id='single line',
        ),
    ),
)
def test_noop(src):
    assert _fix_src(src) == src


@pytest.mark.xfail(sys.version_info < (3, 9), reason='py39+')
@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        pytest.param(
            # Make sure that whitespace is not expected after "with"
            'with(\n'
            '        open("/tmp/t.txt") as file1,\n'
            '        open("/tmp/t.txt") as file2\n'
            '): pass',

            'with(\n'
            '        open("/tmp/t.txt") as file1,\n'
            '        open("/tmp/t.txt") as file2,\n'
            '): pass',
            id='simple usecase',
        ),
        pytest.param(
            'from threading import lock\n'
            'with (lock() as l,\n'
            '     open("/tmp/t.txt")):\n'
            '    pass',

            'from threading import lock\n'
            'with (\n'
            '    lock() as l,\n'
            '    open("/tmp/t.txt"),\n'
            '):\n'
            '    pass',
            id='unhug',
        ),
        pytest.param(
            'with (open(\n'
            '    "a",\n'
            '    some_other_really_long_parameter=True,\n'
            ') as a, a.lock): pass',

            'with (\n'
            '    open(\n'
            '        "a",\n'
            '        some_other_really_long_parameter=True,\n'
            '    ) as a, a.lock,\n'
            '): pass',
            id='lower level linebreaks',
        ),
        pytest.param(
            'with (a as b, c as d,): pass\n',
            'with (a as b, c as d): pass\n',
            id='remove unnecessary comma',
        ),
        pytest.param(
            'with (a as b,): pass\n',
            'with (a as b): pass\n',
            id='remove unnecessary comma one item',
        ),
    ),
)
def test_py39_multiwith(src, expected):
    assert _fix_src(src) == expected
