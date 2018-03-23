from os.path import dirname, join
import pandas as pd

import pandas_latex

data = pd.DataFrame([[0, 1], [2, 3]],
                    index=['foo', 'bar'],
                    columns=['col_one', 'coltwo'])

tests_dir = dirname(__file__)


def expected(name):
    return open(join(tests_dir, '{}.tex').format(name)).read()


def test_basic():
    lines = pandas_latex.format(data)
    assert '\n'.join(lines) == expected('basic')


def test_header_cb():
    def header_cb(name, columns):
        s = r'\rotatebox{90}{\ttfamily %s}'
        return [pandas_latex.line(name, *map(lambda c: s % c, columns))]

    lines = pandas_latex.format(data, header=header_cb, coltype='lr')
    assert '\n'.join(lines) == expected('header_cb')


def test_coltype_cline():
    lines = pandas_latex.format(data, coltype='rcl', clines={2, 3})
    assert '\n'.join(lines) == expected('coltype_cline')
