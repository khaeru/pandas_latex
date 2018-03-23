__all__ = [
    'line',
    'format',
    ]


def _escape(text):
    # TODO also handle &%$#{}~^\
    return text.replace('_', '\_')


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
    return [line(name, *columns)]


def _default_row(name, cells):
    return [line(name, *cells)]


def line(*entries):
    """Concatenate *entries to a single line with & and \\ characters."""
    return ' & '.join(entries) + r' \\'


def format(df, header=None, row=None, preamble=[], coltype='lc', clines=[],
           booktabs=True, env='tabular'):
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

    The user should take care to add appropriate `\\usepackage{…}` commands to
    the document preamble.
    """
    # Process arguments
    preamble = [preamble] if isinstance(preamble, str) else preamble

    # Emit rules according to *booktabs*
    def rule(which):
        if booktabs:
            assert which in ('top', 'mid', 'bottom')
            return r'\{}rule'.format(which)
        else:
            return r'\hline'

    def _header():
        # Escape header contents and then use the callback
        df_name = _escape(getattr(df, 'name', ''))
        df_cols = df.columns.to_series().apply(_escape)
        return _callback(header, _default_header,
                         name=df_name, columns=df_cols)

    def _row(df_row):
        # Escape row contents and then use the callback
        row_name = _escape(df_row.name)
        cells = df_row.astype(str).apply(_escape)
        return _callback(row, _default_row,
                         name=row_name, cells=cells)

    # Format column spec
    n_cols = df.shape[1]

    # Use a length-2 string as (index, data) column type specificers
    if isinstance(coltype, str) and len(coltype) == 2:
        coltype = coltype[0] + n_cols * coltype[1]

    colspec = ''
    for n, ctype in enumerate(coltype):
        colspec += ('|' if n in clines else '') + ctype

    # Emit the table header
    yield from preamble
    yield r'\begin{%s}{%s}' % (env, colspec)
    yield rule('top')
    yield from _header()
    yield rule('mid')

    # Emit the rows
    for rowlines in df.apply(_row, axis=1):
        yield from rowlines

    # Emit the lines
    yield rule('bottom')
    yield r'\end{%s}' % env
    yield ''
