def escape(text):
    # TODO also handle &%$#{}~^\
    return text.replace('_', '\_')


def callback(cb, **kwargs):
    cb_result = cb(**kwargs)
    if isinstance(cb_result, str):
        cb_result = [cb(**kwargs)]
    return


def default_header(name, columns):
    return [line(name, *columns)]


def default_row(name, cells):
    return [line(name, *cells)]


def line(*entries):
    return ' & '.join(entries) + r' \\'


def format(df, header=None, row=None, preamble=[], coltype='lc', clines=[],
           booktabs=True, env='tabular'):
    """Format the pandas.DataFrame *df* as a LaTeX table.

    Returns an iterable of lines.

    Optional arguments:
    *header* (string or callable) - a function called with df.columns as an
      argument, returning a string containing the header row of the table. By
      default, the column names are enclosed in braces { }.
    *row_cb* - a function called with each row of *df* as a pandas.Series,
      return a string containing the formatted row of the table.
    *preamble* - arbitrary string prepended to the table.
    *coltype* (string, or iterable) - if a string, used as the column type
      specifier for every column. If an iterable, it is used directly. Column
      types can include the LaTeX defaults (`l`, `c`, `r`) or others from
      specific packages, e.g. `S` (siunitx).
    *clines* (iterable) - if clines contains an integer i, then a vertical line
      (|) is added to the left of that column. Column indices are 0-based.
    *booktabs* (bool) - if True (default), horizontal rules from the `booktabs`
      package are added. If false, `\hline` is used.
    *env* (string) - the table environment to be used.

    The user should take care to add appropriate `\\usepackage{…}` commands to
    the document preamble.
    """
    # Process arguments
    header = default_header if header is None else header
    row = default_row if row is None else row
    preamble = [preamble] if isinstance(preamble, str) else preamble

    # Callback for rules
    def rule(which):
        if booktabs:
            assert which in ('top', 'mid', 'bottom')
            return [r'\{}rule'.format(which)]
        else:
            return [r'\hline']

    # Escape header contents and then use the callback
    def _header():
        df_name = escape(getattr(df, 'name', ''))
        df_cols = df.columns.to_series().apply(escape)
        return header(name=df_name, columns=df_cols)

    # Escape row contents and then use the callback
    def _row(df_row):
        row_name = escape(df_row.name)
        cells = df_row.astype(str).apply(escape)
        return row(name=row_name, cells=cells)

    # Format column spec
    n_cols = df.shape[1]
    if isinstance(coltype, str) and len(coltype) == 2:
        coltype = coltype[0] + n_cols * coltype[1]

    colspec = ''
    for n, ctype in enumerate(coltype):
        colspec += ('|' if n in clines else '') + ctype

    lines = preamble \
        + [r'\begin{%s}{%s}' % (env, colspec)] \
        + rule('top') \
        + _header() \
        + rule('mid')

    for rowlines in df.apply(_row, axis=1):
        lines.extend(rowlines)

    lines += rule('bottom') + [r'\end{%s}' % env]

    return list(map(lambda s: s + '\n', lines))
