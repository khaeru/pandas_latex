from pathlib import Path

import pandas as pd
import pytest

import pandas_latex as pl

data = pd.DataFrame([[0, 1], [2, 3]],
                    index=['foo', 'bar'],
                    columns=['col_one', 'coltwo'])

tests_dir = Path(__file__).parent


def assert_expected(name, lines):
    """Assert that lines *name*.tex."""
    expected = map(str.rstrip, open(tests_dir / f'{name}.tex').readlines())
    for i, (exp, act) in enumerate(zip(expected, lines)):
        assert exp == act, 'at line %d' % i


def test_escape():
    assert (pl.escape('foo#bar$foo%bar&foo_bar') ==
            r'foo\#bar\$foo\%bar\&foo\_bar')
    assert pl.escape('foo___bar') == r'foo\_\_\_bar'
    assert pl.escape('foo\_bar') == r'foo\_bar'


def test_basic():
    formatter = pl.TableFormatter()
    assert_expected('basic', formatter.format(data))

    formatter.booktabs = False
    assert_expected('booktabs_false', formatter.format(data))


def test_multiindex():
    df = data.copy()

    # Double-up the index on both axes
    df.index = pd.MultiIndex.from_arrays([df.index, df.index])
    df.columns = pd.MultiIndex.from_arrays([df.columns, df.columns])

    assert_expected('multiindex', pl.format(df))

    assert_expected('multiindex_noescape', pl.format(df, escape=['coltwo']))


def test_header_cb():
    def header_cb(name, columns):
        s = r'\rotatebox{90}{\ttfamily %s}'
        return [pl.line(name, *map(lambda c: s % c, columns))]

    lines = pl.format(data, header=header_cb, coltype='lr')
    assert_expected('header_cb', lines)


def test_stateful_cb():
    tf = pl.TableFormatter()

    @tf.hook('row', rownum=0)
    def _(name, cells, state):
        state.rownum += 1
        return pl.line('%d %s' % (state.rownum, name), *cells)

    assert_expected('stateful_cb', tf.format(data))


def test_coltype_cline():
    lines = pl.format(data, coltype='rcl', clines={2, 3})
    assert_expected('coltype_cline', lines)


def test_coltype_raises():
    with pytest.raises(ValueError):
        lines = pl.format(data, coltype=('a', 'b', 'c', 'toomany'))
        # Must yield at least one item to trigger this exception
        next(lines)


def test_noescape():
    assert_expected('noescape', pl.format(data, escape=pl.ALL ^ pl.COLUMNS))

    # No effect because test data don't contain escapable contents
    assert_expected('basic', pl.format(data, escape=[pl.ALL, 'coltwo']))

    with pytest.raises(ValueError):
        assert_expected('basic', pl.format(data, escape=[pl.ALL, 'colthree']))


def test_env_longtable():
    lines = pl.format(data, env='longtable',
                      before_repeat_header='% before_repeat_header hook')
    assert_expected('longtable', lines)


def test_write(tmpdir):
    # Using the class method
    formatter = pl.TableFormatter()
    formatter.write(tmpdir / 'test.tex', data)
    lines = map(str.rstrip, open(tmpdir / 'test.tex').readlines())
    assert_expected('basic', lines)

    # Using the utility method
    pl.write(tmpdir / 'test2.tex', data)
    lines = map(str.rstrip, open(tmpdir / 'test2.tex').readlines())
    assert_expected('basic', lines)
