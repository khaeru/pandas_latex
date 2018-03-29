from os.path import dirname, join
import pandas as pd

import pytest

import pandas_latex

data = pd.DataFrame([[0, 1], [2, 3]],
                    index=['foo', 'bar'],
                    columns=['col_one', 'coltwo'])

tests_dir = dirname(__file__)


def expected(name):
    return open(join(tests_dir, '{}.tex').format(name)).read()


def test_escape():
    assert (pandas_latex._escape('foo#bar$foo%bar&foo_bar') ==
            r'foo\#bar\$foo\%bar\&foo\_bar')
    assert pandas_latex._escape('foo___bar') == r'foo\_\_\_bar'
    assert pandas_latex._escape('foo\_bar') == r'foo\_bar'


def test_basic():
    lines = pandas_latex.format(data)
    assert '\n'.join(lines) == expected('basic')


def test_multiindex():
    df = data.copy()

    # Double-up the index on both axes
    df.index = pd.MultiIndex.from_arrays([df.index, df.index])
    df.columns = pd.MultiIndex.from_arrays([df.columns, df.columns])

    lines = pandas_latex.format(df)
    assert '\n'.join(lines) == expected('multiindex')


def test_header_cb():
    def header_cb(name, columns):
        s = r'\rotatebox{90}{\ttfamily %s}'
        return [pandas_latex.line(name, *map(lambda c: s % c, columns))]

    lines = pandas_latex.format(data, header=header_cb, coltype='lr')
    assert '\n'.join(lines) == expected('header_cb')


def test_coltype_cline():
    lines = pandas_latex.format(data, coltype='rcl', clines={2, 3})
    assert '\n'.join(lines) == expected('coltype_cline')


def test_coltype_raises():
    with pytest.raises(ValueError):
        lines = pandas_latex.format(data, coltype=('a', 'b', 'c', 'toomany'))
        # Must yield at least one item to trigger this exception
        next(lines)
