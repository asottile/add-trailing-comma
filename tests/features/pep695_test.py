from __future__ import annotations

import sys

import pytest

from add_trailing_comma._main import _fix_src


@pytest.mark.parametrize(
    's',
    (
        pytest.param(
            'class A[K]:\n'
            '    ...\n',
            id='single line classdef',
        ),
        pytest.param(
            'def not_none[K](v: K) -> K:\n'
            '    ...\n',
            id='single line functiondef',
        ),
        pytest.param(
            'type ListOrSet[T] = list[T] | set[T]',
            id='single line generic type alias',
        ),
        pytest.param(
            'type ListOrSet = list[str] | set[int]',
            id='no type-param type alias',
        ),
    ),
)
def test_noop(s):
    assert _fix_src(s) == s


@pytest.mark.xfail(sys.version_info < (3, 12), reason='py312+')
@pytest.mark.parametrize(
    ('s', 'e'),
    (
        pytest.param(
            'class ClassA[\n'
            '    T: str\n'
            ']:\n'
            '    ...',

            'class ClassA[\n'
            '    T: str,\n'
            ']:\n'
            '    ...',
            id='multiline classdef',
        ),
        pytest.param(
            'def f[\n'
            '    T\n'
            '](x: T) -> T:\n'
            '    ...',

            'def f[\n'
            '    T,\n'
            '](x: T) -> T:\n'
            '    ...',
            id='multiline functiondef',
        ),
        pytest.param(
            'type ListOrSet[\n'
            '    T,\n'
            '    K\n'
            '] = list[T] | set[K]',
            'type ListOrSet[\n'
            '    T,\n'
            '    K,\n'
            '] = list[T] | set[K]',
            id='multiline generic type alias',
        ),
        pytest.param(
            'def f[\n'
            '    T: (\n'
            '        "ForwardReference",\n'
            '        bytes\n'
            '    )\n'
            '](x: T) -> T:\n'
            '    ...',

            'def f[\n'
            '    T: (\n'
            '        "ForwardReference",\n'
            '        bytes,\n'
            '    ),\n'
            '](x: T) -> T:\n'
            '    ...',
            id='multiline function constrained types',
        ),
        pytest.param(
            'class ClassB[\n'
            '    T: (\n'
            '        "ForwardReference",\n'
            '        bytes\n'
            '    )\n'
            ']:\n'
            '    ...\n',

            'class ClassB[\n'
            '    T: (\n'
            '        "ForwardReference",\n'
            '        bytes,\n'
            '    ),\n'
            ']:\n'
            '    ...\n',
            id='multiline class constrained types',
        ),
    ),
)
def test_fix(s, e):
    assert _fix_src(s) == e
