# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from add_trailing_comma import main


def test_main_trivial():
    assert main(()) == 0


def test_main_noop(tmpdir):
    f = tmpdir.join('f.py')
    f.write('x = 5\n')
    assert main((f.strpath,)) == 0
    assert f.read() == 'x = 5\n'


# def test_main_changes_a_file(tmpdir, capsys):
#     f = tmpdir.join('f.py')
#     f.write('x(\n    1\n)\n')
#     assert main((f.strpath,)) == 1
#     out, _ = capsys.readouterr()
#     assert out == 'Rewriting {}\n'.format(f.strpath)
#     assert f.read() == 'x(\n    1,\n)\n'


def test_main_syntax_error(tmpdir):
    f = tmpdir.join('f.py')
    f.write('from __future__ import print_function\nprint 1\n')
    assert main((f.strpath,)) == 0


def test_main_non_utf8_bytes(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary('# -*- coding: cp1252 -*-\nx = €\n'.encode('cp1252'))
    assert main((f.strpath,)) == 1
    out, _ = capsys.readouterr()
    assert out == '{} is non-utf-8 (not supported)\n'.format(f.strpath)


# def test_py35_plus_argument_star_args(tmpdir):
#     f = tmpdir.join('f.py')
#     f.write('x(\n    *args\n)\n')
#     assert main((f.strpath,)) == 0
#     assert f.read() == 'x(\n    *args\n)\n')
#     assert main((f.strpath, '--py35-plus')) == 1
#     assert f.read() == 'x(\n    *args,\n)\n'
