from enum import Flag, auto
from functools import partial
from itertools import tee
import re

__all__ = [
    'TableFormatter',
    'escape',
    'line',
    'format',
    'write',
    ]


class Escape(Flag):
    """Flag for items to escape. See TableFormatter documentation."""
    NAME = auto()
    COLUMNS = auto()
    INDEX = auto()
    CELLS = auto()
    ALL = NAME | COLUMNS | INDEX | CELLS

    @classmethod
    def unpack(cls, value):
        """Break ALL into a set() of other values."""
        return filter(lambda v: v in value and v is not cls.ALL, cls)


# Add Escape members to the global name space
globals().update(Escape.__members__)


# Pre-compiled regular expression for escape()
_escape_re = re.compile(r'(?<!\\)([#$%&_{}])')


# Public methods
def escape(text, go=True):
    """Convert *text* to str() and excape LaTeX special characters.

    If *text* is a tuple() (for instance, a pd.MultiIndex label), the elements
    are escaped recursively. Any of # $ % & _ { } that is not already prefixed
    by a slash is escaped.

    If *go* is False, the replacement is not performed.
    """
    # TODO also handle ~^\
    if isinstance(text, tuple):
        # For instance, a pd.MultiIndex label
        return tuple(map(partial(escape, go=go), text))
    else:
        return _escape_re.sub(_escape_repl, str(text)) if go else str(text)


def line(*entries):
    """Concatenate *entries* to a single line with & and \\ characters."""
    return ' & '.join(entries) + r' \\'


# Internal methods
def _lines(value):
    """Wrap a string in a list."""
    return [value] if isinstance(value, str) else value


def _comma_sep(value):
    """Collapse a tuple to a comma-separated string."""
    return ', '.join(value) if isinstance(value, tuple) else value


def _escape_repl(match):
    """Replacement helper for escape()."""
    return r'\{}'.format(match.groups()[0])


class TableFormatter:
    """Format pandas.DataFrames as LaTeX tables.

    Properties of the class (below) control the table formatting. These may be
    set with keyword arguments to the constructor, or by assigning to a class
    instance:

    >>> tf = TableFormatter(booktabs=False)
    >>> tf.header = lambda name, columns: r'foo \\'
    >>> tf.write(filename, data)

    Basic properties:
    env : str (default 'tabular')
         LaTeX table environment.
    coltype : str or iterable of str
        If a length-2 string, the first character is used as the column type
        specifier for the index column, and the second character for the data
        columns. If an iterable of strings, each element is a specifier for the
        index (first element) or one of the columns. Column type specifiers can
        include the LaTeX defaults (`l`, `c`, `r`) or those from optional
        packages, e.g. `S` from siunitx.
    clines: iterable of int
        Vertical lines (`|`) are added to the left of (zero-based) column
        number *c* for every integer *c* in this argument.
    booktabs : bool
        If True (default), horizontal rules from the `booktabs` package are
        added. If False, `\hline` is used.
    escape : Escape, or iterable of (Escape or str)
        Items to pass through escape(). These may be one or more flag values of
        the Escape class, or the names of columns in the table data. The
        default is Escape.ALL, which implies:

        - Escape.NAME: the `name` attribute of the pd.DataFrame.
        - Escape.INDEX: index labels.
        - Escape.COLUMNS: column labels
        - Escape.CELLS: cells in all data columns.

        If any column name is included in *escape*, then Escape.CELLS is
        ignored.

    Optional callback functions. If not supplied, simple defaults are used:
    header : callable
        Called with the arguments: name=df.name, columns=df.columns. Must
        return a string, or iterable of strings, containing the formatted
        header row(s) of the table.
    row : callable
        Called for each row of the table data with the arguments:
        name=row.name, cells=row (as a pandas.Series). Must return a string, or
        iterable of strings, containing a formatted row of the table.

    Optional lines or iterables of lines:
    preamble :
        Insertd before the table environment.
    before_header :
        Inserted within the table environment, or the within the first header
        of a longtable.
    before_repeat_header :
        Inserted before the repeated header of a longtable.

    Notes
    -----
    The user should take care to add appropriate `\\usepackage{…}` commands to
    the document preamble.
    """
    # Basic table properties
    env = 'tabular'
    coltype = 'lc'
    clines = set()
    booktabs = True
    escape = Escape.ALL

    _to_escape = None

    # Default callbacks
    @staticmethod
    def header(name, columns):
        return line(_comma_sep(name), *map(_comma_sep, columns))

    @staticmethod
    def row(name, cells):
        return line(_comma_sep(name), *cells)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def _colspec(self, df):
        """Format column spec."""
        n_cols = df.shape[1]

        coltype = self.coltype

        if isinstance(coltype, str) and len(coltype) == 2:
            # Use a length-2 string as (index, data) column type specifiers
            coltype = coltype[0] + n_cols * coltype[1]
        elif isinstance(coltype, (list, tuple)):
            # Use a sequence as explicit coltypes
            if len(coltype) != n_cols + 1:
                msg = "coltype '{}' has length {} != {} data columns + index"
                raise ValueError(msg.format(coltype, len(coltype), n_cols))

        # Prepare the spec
        result = ''
        for n, ctype in enumerate(coltype):
            # Add column lines where requested
            result += ('|' if n in self.clines else '') + ctype

        return result

    def _escape(self, which, value, df=None):
        """Escape LaTeX special characters in *value* according to *which*.

        *which* is either a flag value of Escape, or None. If None, *value*
        must be a pd.DataFrame, and its name is used to determine whether to
        escape its contents.
        """
        if self._to_escape is None:
            # First run: compute sets of things to escape
            to_escape = set()
            discard_cells = False

            # Wrap a single value
            try:
                esc = iter(self.escape)
            except TypeError:
                esc = [self.escape]

            for e in esc:
                if isinstance(e, Escape):
                    # Unpack Escape.ALL to the other flag values
                    to_escape.update(Escape.unpack(e))
                elif e in df.columns:
                    # Add the column name
                    to_escape.add(e)
                    discard_cells = True
                else:
                    raise ValueError("don't know how to escape '%s'" % e)

            if discard_cells:
                # One or more column names specified directly
                to_escape.discard(Escape.CELLS)

            if Escape.CELLS in to_escape:
                # Add the names of all columns
                to_escape.update(df.columns)

            # Store for the rest of the current format() operation
            self._to_escape = to_escape

        # Condition for escaping: the flag value or pd.DataFrame.name is in
        # _to_escape
        go = (value.name if which is None else which) in self._to_escape
        func = partial(escape, go=go)

        # Apply to a pd.Series, or escape a string
        return value.apply(func) if which is None else func(value)

    def _header(self, df):
        """Format the header."""
        # Maybe escape header contents and then use the callback
        df_name = self._escape(Escape.NAME, getattr(df, 'name', ''), df)
        df_cols = df.columns \
                    .to_series() \
                    .apply(partial(self._escape, Escape.COLUMNS))
        return _lines(self.header(name=df_name, columns=df_cols))

    def _optional_lines(self, group):
        """Return a group of optional lines."""
        return _lines(getattr(self, group, []))

    def _row(self, df_row):
        """Format a row."""
        # Maybe escape row name and then use the callback
        row_name = self._escape(Escape.INDEX, df_row.name)
        cells = df_row.astype(str)
        return _lines(self.row(name=row_name, cells=cells))

    def _rule(self, which):
        """Return a horizontal rule."""
        if self.booktabs:
            assert which in ('top', 'mid', 'bottom')
            return r'\{}rule'.format(which)
        else:
            return r'\hline'

    def format(self, df):
        """Generate lines for a LaTeX representation of *df*."""
        yield from self._optional_lines('preamble')
        yield r'\begin{%s}{%s}' % (self.env, self._colspec(df))

        # Emit the table header
        yield from self._optional_lines('before_header')

        header = self._header(df)

        if self.env == 'longtable':
            # The header must be emitted twice
            header, repeat_header = tee(self._header(df), 2)

        yield self._rule('top')
        yield from header
        yield self._rule('mid')

        # For longtable, the initial & running headers, and footer, go first
        if self.env == 'longtable':
            yield r'\endfirsthead'
            yield from self._optional_lines('before_repeat_header')
            yield self._rule('top')
            yield from repeat_header
            yield self._rule('mid')
            yield r'\endhead'
            yield self._rule('bottom')
            yield r'\endfoot'

        # Escape the data
        df_escaped = df.apply(lambda column: self._escape(None, column))

        # Emit the rows
        # NB df.apply() doesn't work here when df.index is a MultiIndex; the
        # result is a DataFrame instead of a Series, and the elements are
        # strings, not lists. This way also avoids storing the entire result.
        for _, r in df_escaped.iterrows():
            yield from self._row(r)

        # Emit bottom rule
        if self.env != 'longtable':
            yield self._rule('bottom')

        # End the table
        yield r'\end{%s}' % self.env
        yield ''

        # Reset _to_escape; this forces _escape() to regenerate it on the next
        # call of format(), in case the escape_values or no_escape attributes
        # have changes
        self._to_escape = None

    def write(self, path, df):
        """Write a LaTeX representation of *df* to *path*."""
        with open(path, 'w') as f:
            f.writelines('%s\n' % line for line in self.format(df))


def format(df, **kwargs):
    """Convenience wrapper around TableFormatter.format()."""
    return TableFormatter(**kwargs).format(df)


def write(path, df, **kwargs):
    """Convenience wrapper around TableFormatter.write()."""
    return TableFormatter(**kwargs).write(path, df)
