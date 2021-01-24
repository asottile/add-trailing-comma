import pytest

from add_trailing_comma._main import _fix_src


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
    assert _fix_src(src, min_version=(2, 7)) == src


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
    assert _fix_src(src, min_version=(2, 7)) == expected
