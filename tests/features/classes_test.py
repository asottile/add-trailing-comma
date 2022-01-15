from __future__ import annotations

import pytest

from add_trailing_comma._main import _fix_src


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
    assert _fix_src(src, min_version=(2, 7)) == src


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
    assert _fix_src(src, min_version=(2, 7)) == expected


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
    assert _fix_src(src, min_version=(2, 7)) == expected
