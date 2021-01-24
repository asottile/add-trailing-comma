import pytest

from add_trailing_comma._main import _fix_src


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
    assert _fix_src(src, min_version=(2, 7)) == src


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
    assert _fix_src(src, min_version=(2, 7)) == expected
