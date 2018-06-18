# (yet another) pandas.DataFrame → LaTeX table formatter
© 2018 Paul Natsuo Kishimoto (<mail@paul.kishimoto.name>)

Provided under the GNU General Public License, version 3.0

I know—there are a lot of these:

- Actively developed:
  - [DataFrame.to_latex()](http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_latex.html) in pandas itself.
  - [tabulate](https://bitbucket.org/astanin/python-tabulate)
  - [pytablewriter](http://pytablewriter.readthedocs.io)
  - [PyLaTeX](https://jeltef.github.io/PyLaTeX/current/) has a [`Tabular`](https://jeltef.github.io/PyLaTeX/current/pylatex/pylatex.table.html) class
- Others (with latest commit date):
  - [PyLaTeXtables](https://github.com/lahwaacz/PyLaTeXtables) (2018-03-18)
  - [pandas_latex](https://github.com/kevinali1/pandas_latex) (2016-08-15)
  - [df2latex](https://github.com/dmarasco/df2latex) (2015-04-24)
  - [pandas_format](https://github.com/alanhdu/pandas_format) (2015-01-11)

The chief advantage of this one is the use of callbacks. The `header` and `row` arguments to the `format()` method allow the user to specify callables used to format those parts of the table. Cell contents and column headers are sanitized before going through these callbacks, and helper methods like `line()` are provided. The callbacks can also be assigned using the `.hook()` decorator,
with any extra keyword arguments passed as a `state` variable to the callback:

```python
import pandas as pd
import pandas_latex as pl

data = pd.DataFrame([[0, 1], [2, 3]],
                    index=['foo', 'bar'],
                    columns=['col_one', 'coltwo'])

tf = pl.TableFormatter(coltype='lcS')

@tf.hook('header')
def _h(name, columns):
    s = r'\rotatebox{90}{\ttfamily %s}'
    return pl.line(name, *map(lambda c: s % c, columns))

@tf.hook('row', num=0)
def _r(name, columns, state):
    state.num += 1
    return pl.line('%d %s' % (state.num, name), *map(lambda c: s % c, columns))

lines = tf.format(data)

print('\n'.join(lines))
```

…gives a result like:
```latex
\begin{tabular}{lcS}
\toprule
 & \rotatebox{90}{\ttfamily col\_one} & \rotatebox{90}{\ttfamily coltwo} \\
\midrule
1 foo & 0 & 1 \\
2 bar & 2 & 3 \\
\bottomrule
\end{tabular}
```

See [the source code](https://github.com/khaeru/pandas_latex/blob/master/src/pandas_latex/__init__.py) for more documentation.

Run tests using `python3 setup.py test`
