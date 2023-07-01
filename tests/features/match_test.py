from __future__ import annotations

import sys

import pytest

from add_trailing_comma._main import _fix_src


@pytest.mark.parametrize(
    's',
    (
        pytest.param(
            'match x:\n'
            '    case 1, 2:\n'
            '        pass\n',
            id='sequence without braces',
        ),
        pytest.param(
            'match x:\n'
            '    case a():\n'
            '        pass\n',
            id='class without args',
        ),
    ),
)
def test_noop(s):
    assert _fix_src(s) == s


@pytest.mark.xfail(sys.version_info < (3, 10), reason='py310+')
@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        pytest.param(
            'match x:\n'
            '    case A(\n'
            '        1,\n'
            '        x=2\n'
            '    ):\n'
            '        pass\n',
            'match x:\n'
            '    case A(\n'
            '        1,\n'
            '        x=2,\n'
            '    ):\n'
            '        pass\n',
            id='match class',
        ),
        pytest.param(
            'match x:\n'
            '    case (\n'
            '        1,\n'
            '        2\n'
            '    ):\n'
            '        pass\n',
            'match x:\n'
            '    case (\n'
            '        1,\n'
            '        2,\n'
            '    ):\n'
            '        pass\n',
            id='match sequence tuple',
        ),
        pytest.param(
            'match x:\n'
            '    case (1, ):\n'
            '        pass\n',
            'match x:\n'
            '    case (1,):\n'
            '        pass\n',
            id='match sequence 1-element tuple',
        ),
        pytest.param(
            'match x:\n'
            '    case [\n'
            '        1,\n'
            '        2\n'
            '    ]:\n'
            '        pass\n',
            'match x:\n'
            '    case [\n'
            '        1,\n'
            '        2,\n'
            '    ]:\n'
            '        pass\n',
            id='match sequence list',
        ),
        pytest.param(
            'match x:\n'
            '    case [1, ]:\n'
            '        pass\n',
            'match x:\n'
            '    case [1]:\n'
            '        pass\n',
            id='match sequence list removes comma',
        ),
        pytest.param(
            'match x:\n'
            '    case {\n'
            '        True: 1,\n'
            '        False: 2\n'
            '    }:\n'
            '        pass\n',
            'match x:\n'
            '    case {\n'
            '        True: 1,\n'
            '        False: 2,\n'
            '    }:\n'
            '        pass\n',
            id='match mapping',
        ),
        pytest.param(
            'match x:\n'
            '    case {"x": 1,}:\n'
            '        pass\n',
            'match x:\n'
            '    case {"x": 1}:\n'
            '        pass\n',
            id='match mapping removes extra comma',
        ),
    ),
)
def test_fix(src, expected):
    assert _fix_src(src) == expected
