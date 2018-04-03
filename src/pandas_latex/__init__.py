from itertools import tee
import re

__all__ = [
    'line',
    'format',
    ]


_escape_re = re.compile(r'(?<!\\)([#$%&_{}])')


def _escape_repl(match):
    return r'\{}'.format(match.groups()[0])


def _escape(text):
    """Escape special characters.

    Any of # $ % & _ { } that is not already prefixed by a slash is escaped.
    """
    # TODO also handle ~^\
    if isinstance(text, tuple):
        # For instance, a pd.MultiIndex label
        return tuple(map(_escape, text))
    else:
        return _escape_re.sub(_escape_repl, str(text))


def _noescape(text):
    if isinstance(text, tuple):
        return tuple(map(_noescape, text))
    else:
        return str(text)


def _callback(cb, default, **kwargs):
    """Run the callback *cb*, or *default* if *cb* is None.

    Optional *kwargs* are passed on to *cb*.
    """
    if cb is None:
        # No callback supplied, use the default
        return default(**kwargs)
    else:
        cb_result = cb(**kwargs)

        # Be forgiving: if the user's callback returns a string, wrap it
        if isinstance(cb_result, str):
            cb_result = [cb(**kwargs)]

        return cb_result


# Default callbacks
def _default_header(name, columns):
    # Handle non-string labels, e.g. MultiIndex
    name = ', '.join(name) if isinstance(name, tuple) else name
    if isinstance(columns[0], tuple):
        columns = [', '.join(col) for col in columns]
    return [line(name, *columns)]


def _default_row(name, cells):
    name = ', '.join(name) if isinstance(name, tuple) else name
    return [line(name, *cells)]


def line(*entries):
    """Concatenate *entries to a single line with & and \\ characters."""
    return ' & '.join(entries) + r' \\'


def format(df, header=None, row=None, preamble=[], coltype='lc', clines=set(),
           booktabs=True, env='tabular', escape={'all'}, no_escape=set(),
           **kwargs):
    """Format the pandas.DataFrame *df* as a LaTeX table.

    Returns an iterable of lines.

    Optional arguments:
    *header* (callable) - called with the arguments: name=df.name,
      columns=df.columns. Must return a string, or iterable of strings,
      containing the formatted header row(s) of the table. If not supplied,
      `default_header` is used.
    *row* (callable) - a function called for each row of *df*, with the
      arguments: name=row.name, cells=row (as a pandas.Series). Must return a
      string, or iterable of strings, containing a formatted row of the table.
      If not supplied, `default_row` is used.
    *preamble* - arbitrary string prepended to the table.
    *coltype* (string, or iterable) - if a length-2 string, the first character
      is used as the column type specifier for the index column, and the second
      character for the data columns. If an iterable or string, it is used
      directly. Column types specifiers can include the LaTeX defaults (`l`,
      `c`, `r`) or others from specific packages, e.g. `S` (siunitx).
    *clines* (iterable or collection) - vertical lines (`|`) are added to the
       left of column number *c* (0-based) for every *c* in this argument.
    *booktabs* (bool) - if True (default), horizontal rules from the `booktabs`
      package are added. If False, `\hline` is used.
    *env* (string) - the table environment to be used; default 'tabular'.

    *escape*, *no_escape* (sets) - names of things to pass through _escape();
      either column names or one of the special values below. The items
      specified by *no_escape* are subtracted from those specified by *escape*.
      - 'all' (*escape* only): shorthand for _name, _index, _columns, _cells
      - '_name': *df*'s name attribute
      - '_index': index labels
      - '_columns': column labels
      - '_cells': all data columns

    The user should take care to add appropriate `\\usepackage{…}` commands to
    the document preamble.
    """
    # Process arguments
    preamble = [preamble] if isinstance(preamble, str) else preamble

    # Things to escape (or not!)
    escape = set(escape)
    if 'all' in escape:
        escape = {'_name', '_index', '_columns'} | set(df.columns)
    elif '_cells' in escape:
        escape |= set(df.columns)
    escape -= set(no_escape)
    esc_name = _escape if '_name' in escape else _noescape
    esc_index = _escape if '_index' in escape else _noescape
    esc_columns = _escape if '_columns' in escape else _noescape

    def _header():
        # Maybe escape header contents and then use the callback
        df_name = esc_name(getattr(df, 'name', ''))
        df_cols = df.columns.to_series().apply(esc_columns)
        return _callback(header, _default_header,
                         name=df_name, columns=df_cols)

    def _row(df_row):
        # Maybe escape row name and then use the callback
        row_name = esc_index(df_row.name)
        cells = df_row.astype(str)
        return _callback(row, _default_row,
                         name=row_name, cells=cells)

    # Format column spec
    n_cols = df.shape[1]

    # Use a length-2 string as (index, data) column type specificers
    if isinstance(coltype, str) and len(coltype) == 2:
        coltype = coltype[0] + n_cols * coltype[1]
    elif isinstance(coltype, (list, tuple)):
        if len(coltype) != n_cols + 1:
            raise ValueError(("coltype '{}' has length {} != {} data columns +"
                              " index").format(coltype, len(coltype), n_cols))

    colspec = ''
    for n, ctype in enumerate(coltype):
        colspec += ('|' if n in clines else '') + ctype

    # Emit rules according to *booktabs*
    def rule(which):
        if booktabs:
            assert which in ('top', 'mid', 'bottom')
            return r'\{}rule'.format(which)
        else:
            return r'\hline'

    # Emit the table header
    yield from preamble
    yield r'\begin{%s}{%s}' % (env, colspec)
    if 'before_header' in kwargs:
        yield kwargs['before_header']

    if env == 'longtable':
        header, repeat_header = tee(_header(), 2)
    else:
        header = _header()
    yield rule('top')
    yield from header
    yield rule('mid')

    if env == 'longtable':
        yield r'\endfirsthead'
        yield rule('top')
        yield from repeat_header
        yield rule('mid')
        yield r'\endhead'
        yield rule('bottom')
        yield r'\endfoot'

    # Escape the data
    for col in escape - {'_name', '_index', '_columns'}:
        df[col] = df[col].apply(_escape)

    # Emit the rows
    # NB df.apply() doesn't work here when df.index is a MultiIndex; the result
    #    is a DataFrame instead of a Series, and the elements are strings, not
    #    lists. This way also avoids storing the entire result.
    for _, r in df.iterrows():
        yield from _row(r)

    # Emit the lines
    if env != 'longtable':
        yield rule('bottom')
    yield r'\end{%s}' % env
    yield ''
