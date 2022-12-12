from __future__ import annotations

import io
import sys
from unittest import mock

from add_trailing_comma._main import main


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
    assert main((f.strpath, '--py36-plus')) == 1
    _, err = capsys.readouterr()
    assert err == f'Rewriting {f}\n'
    assert f.read() == 'x(\n    1,\n)\n'


def test_main_preserves_line_endings(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary(b'x(\r\n    1\r\n)\r\n')
    assert main((f.strpath, '--py36-plus')) == 1
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
    assert main((f.strpath, '--py36-plus')) == 1
    _, err = capsys.readouterr()
    assert err == f'{f} is non-utf-8 (not supported)\n'


def test_main_py27_syntaxerror_coding(tmpdir):
    f = tmpdir.join('f.py')
    f.write('# -*- coding: utf-8 -*-\n[1, 2,]\n')
    assert main((f.strpath, '--py36-plus')) == 1
    assert f.read() == '# -*- coding: utf-8 -*-\n[1, 2]\n'


def test_main_py35_plus_argument_star_args(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write('x(\n    *args\n)\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'x(\n    *args\n)\n'
    out, err = capsys.readouterr()
    assert err.startswith('WARNING: add-trailing-comma will only use 3.6+')
    assert main((f.strpath, '--py35-plus')) == 1
    assert f.read() == 'x(\n    *args,\n)\n'
    out, err = capsys.readouterr()
    assert err.startswith('WARNING: add-trailing-comma will only use 3.6+')


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
