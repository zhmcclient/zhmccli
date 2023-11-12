"""
Parser for complex name-value strings.
"""

from __future__ import absolute_import

from pyparsing import Forward, Opt, Group, nums, alphas, Literal, Char, Word, \
    CharsNotIn, QuotedString, DelimitedList, Suppress, ParseResults, \
    ParseException

__all__ = ['NameValueParseError', 'NameValueParser']


class NameValueParseError(Exception):
    # pylint: disable=too-few-public-methods
    """
    Indicates an error when parsing a complex name-value string.
    """
    pass


class NameValueParser(object):
    # pylint: disable=too-few-public-methods
    """
    Parser for complex name-value strings.

    The syntax for a complex name-value string is as follows:

    * ``complex-value := simple-value | array-value | object-value``

    * ``simple-value`` is a value of a simple type, as follows:

      - none/null: ``null``.
        Will be returned as Python ``None``.

      - bool: ``true`` or ``false``.
        Will be returned as Python ``True`` or ``False``.

      - int: decimal string representation of an integer number that is
        parseable by ``int()``.
        Will be returned as a Python ``int`` value.

      - float: string representation of a floating point number that is
        parseable by ``float()``.
        Will be returned as a Python ``float`` value.

      - string: Unicode string value, with character range and representation
        as for JSON string values, surrounded by double quotes. The quoting
        character can be configured, the escape character is always ``\\``
        (backslash). The quoting characters can be omitted if the string value
        is not escaped, does not contain any of ``[]{}``, blank, the escape
        character, the quoting character, the separator character, the
        assignment character, and if it cannot be interpreted as a value of one
        of the other simple types.
        Will be returned as an unescaped Python Unicode string value.

        The following escape sequences are recognized in quoted strings:

        - ``\\b``: U+0008 (backspace)
        - ``\\t``: U+0009 (tab)
        - ``\\n``: U+000A (newline)
        - ``\\r``: U+000D (carriage return)
        - ``\\uNNNN``: 4..6 digit Unicode code point

    * ``array-value`` is a value of array/list type, specified as a
      comma-separated list of ``complex-value`` items, surrounded by
      ``[`` and ``]``.
      The item separator character can be configured.
      Will be returned as a Python ``list`` value.

    * ``object-value`` is a value of object/dict type, specified as a
      comma-separated list of ``name=complex-value`` items, surrounded by
      ``{`` and ``}``.
      The item separator and assignment characters can be configured.
      ``name`` must begin with an alphabetic character,
      and may be followed by zero or more alphanumeric characters,
      ``-`` (hyphen) and ``_`` (underscore).
      Will be returned as a Python ``dict`` value.

    Examples (using the default quoting, separator and assignment
    characters)::

        parser = NameValueParser()

        print(parser.parse('null'))         # -> None
        print(parser.parse('false'))        # -> False
        print(parser.parse('true'))         # -> True
        print(parser.parse('"true"'))       # -> 'true'
        print(parser.parse('42'))           # -> 42
        print(parser.parse('42.'))          # -> 42.0
        print(parser.parse('.1'))           # -> 0.1
        print(parser.parse('abc'))          # -> 'abc'
        print(parser.parse('"ab c"'))       # -> 'ab c'
        print(parser.parse('"ab\\nc"'))      # -> 'ab\\nc'
        print(parser.parse('[abc,42]'))     # -> ['abc', 42]

        print(parser.parse('{interface-name=abc,port=42}'))
        # -> {'interface-name': 'abc', 'port': 42}

        print(parser.parse('{title="ab\\tc",host-addrs=[10.11.12.13,null]}'))
        # -> {'title': 'ab\\tc', 'host-addrs': ['10.11.12.13', None]}
    """

    def __init__(self, quoting_char='"', separator_char=',',
                 assignment_char='='):
        """
        Parameters:

          quoting_char(str): Quoting character, used around strings to make
            them quoted strings.

          separator_char(str): Separator character, used to separate items
            in arrays and objects.

          assignment_char(str): Assignment character, used between name and
            value within object items.
        """
        assert len(quoting_char) == 1
        assert len(separator_char) == 1
        assert len(assignment_char) == 1

        self._quoting_char = quoting_char
        self._separator_char = separator_char
        self._assignment_char = assignment_char

        # Note: Setting escape_char to anything else does not work
        escape_char = '\\'

        unquoted_forbidden_chars = ' []{}' + escape_char + quoting_char + \
            separator_char + assignment_char

        # Define pyparsing grammar
        null_value = Literal('null')
        bool_value = Literal('true') | Literal('false')
        int_value = Word(nums)
        float_value = (Word(nums) + Char('.') + Opt(Word(nums))) | \
            (Char('.') + Word(nums))
        quoted_string_value = \
            QuotedString(quote_char=quoting_char, esc_char=escape_char)
        unquoted_string_value = CharsNotIn(unquoted_forbidden_chars)
        simple_value = null_value | bool_value | float_value | int_value | \
            quoted_string_value | unquoted_string_value
        complex_value = Forward()
        name = Word(alphas, alphas + nums + '-_')
        named_value = Group(name + Suppress(assignment_char) + complex_value)
        array_value = Suppress('[') + \
            Opt(DelimitedList(complex_value, delim=separator_char)) + \
            Suppress(']')
        object_value = Suppress('{') + \
            Opt(DelimitedList(named_value, delim=separator_char)) + \
            Suppress('}')
        # pylint: disable=pointless-statement
        complex_value << (array_value | object_value | simple_value)
        self._grammar = complex_value

        array_value.add_parse_action(_as_python_list)
        object_value.add_parse_action(_as_python_dict)
        int_value.add_parse_action(_as_python_int)
        float_value.add_parse_action(_as_python_float)
        bool_value.add_parse_action(_as_python_bool)
        null_value.add_parse_action(_as_python_null)

    @property
    def quoting_char(self):
        """
        The quoting character used by this parser, used around strings to make
        them quoted strings.
        """
        return self._quoting_char

    @property
    def separator_char(self):
        """
        The separator character used by this parser, used to separate items in
        arrays and objects.
        """
        return self._separator_char

    @property
    def assignment_char(self):
        """
        The assignment character used by this parser, used between name and
        value within object items.
        """
        return self._assignment_char

    def parse(self, value):
        """
        Parse a complex name-value string and return the Python data object
        representing the value.

        Parameters:

          value(str): The complex name-value string to be parsed.

        Returns:
          object: Python object representing the complex name-value string.

        Raises:
          NameValueParseError: Parsing error.
        """
        try:
            parse_result = self._grammar.parse_string(value, parse_all=True)
        except ParseException as exc:
            raise NameValueParseError(
                "Cannot parse value {!r}: {}".format(value, exc))
        return parse_result[0]


# pyparsing parse actions

# For debugging parse actions, there are two possibilities:
# * Add @pyparsing.trace_parse_action decorator to parse action
# * Invoke set_debug(True) on grammar element

def _as_python_list(toks):
    """Return parsed array as Python list"""
    return ParseResults.List(toks.as_list())


def _as_python_dict(toks):
    """Return parsed object as Python dict"""
    result = {}
    for name, value in toks:
        result[name] = value
    return result


def _as_python_int(toks):
    """Return parsed int string as Python int"""
    assert len(toks) == 1
    return int(toks[0])


def _as_python_float(toks):
    """Return parsed float string as Python float"""
    float_str = ''.join(toks)
    return float(float_str)


def _as_python_bool(toks):
    """Return parsed bool string as Python bool"""
    assert len(toks) == 1
    mapping = {
        'true': True,
        'false': False,
    }
    return mapping[toks[0]]


def _as_python_null(toks):
    """Return parsed null string as Python None"""
    assert len(toks) == 1
    mapping = {
        'null': None,
    }
    # `None` can only be returned by using the ability of parse actions to
    # modify their ParseResults argument in place.
    toks[0] = mapping[toks[0]]
