# (yet another) pandas.DataFrame → LaTeX table formatter
© 2018 Paul Natsuo Kishimoto (<mail@paul.kishimoto.name>)

Provided under the GNU General Public License, version 3.0

I know—there are a lot of these:

- Actively developed:
  - [DataFrame.to_latex()](http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_latex.html) in pandas itself.
  - [tabulate](https://bitbucket.org/astanin/python-tabulate)
  - [pytablewriter](http://pytablewriter.readthedocs.io)
- Others (with latest commit date):
  - [PyLaTeXtables](https://github.com/lahwaacz/PyLaTeXtables) (2018-03-18)
  - [pandas_latex](https://github.com/kevinali1/pandas_latex) (2016-08-15)
  - [df2latex](https://github.com/dmarasco/df2latex) (2015-04-24)
  - [pandas_format](https://github.com/alanhdu/pandas_format) (2015-01-11)

The chief advantage of this one is the use of callbacks. The `header` and `row` arguments to the `format()` method allow the user to specify callables used to format those parts of the table. Cell contents and column headers are sanitized before going through these callbacks, and helper methods like `line()` are provided:

```python
import pandas as pd
import pandas_latex

data = pd.DataFrame([[0, 1], [2, 3]],
                    index=['foo', 'bar'],
                    columns=['col_one', 'coltwo'])

def header_cb(name, columns):
    s = r'\rotatebox{90}{\ttfamily %s}'
    return [pandas_latex.line(name, *map(lambda c: s % c, columns))]

lines = pandas_latex.format(data, header_cb, coltype='lcS')

print('\n'.join(lines))
```

…gives a result like:
```latex
\begin{tabular}{lcS}
\toprule
 & \rotatebox{90}{\ttfamily col\_one} & \rotatebox{90}{\ttfamily coltwo} \\
\midrule
foo & 0 & 1 \\
bar & 2 & 3 \\
\bottomrule
\end{tabular}
```

See [the source code](https://github.com/khaeru/pandas_latex/blob/master/src/pandas_latex/__init__.py) for more documentation.

Run tests using `python3 setup.py test`
