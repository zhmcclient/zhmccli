"""
Function test for '_name_value_parser' module.
"""

from __future__ import absolute_import, print_function

import re
import pytest

from zhmccli import NameValueParseError, NameValueParser


TESTCASES_NAME_VALUE_PARSER_PARSE = [
    # Testcases for test_name_value_parser_parse()
    #
    # Each list item is a testcase with the following tuple items:
    # * desc (str) - Testcase description.
    # * init_kwargs (dict) -  Keyword arguments for NameValueParser().
    # * input_value (str) - Input value for NameValueParser.parse().
    # * exp_result (object) - Expected return value from NameValueParser.parse()
    #   if expected to succeed, or None if expected to fail.
    # * exp_exc_type (exception) - Expected exception type if expected to fail,
    #   or None if expected to succeed.
    # * exp_exc_message (str) - Regexp pattern to match expected exception
    #   message if expected to fail, or None if expected to succeed.

    (
        r"""Simple null value 'null'.""",
        dict(),
        r'null',
        None,
        None, None
    ),

    (
        r"""Simple bool 'true'.""",
        dict(),
        r'true',
        True,
        None, None
    ),
    (
        r"""Simple bool 'false'.""",
        dict(),
        r'false',
        False,
        None, None
    ),

    (
        r"""Simple int '42'.""",
        dict(),
        r'42',
        42,
        None, None
    ),

    (
        r"""Simple float '42.0'.""",
        dict(),
        r'42.0',
        42.0,
        None, None
    ),
    (
        r"""Simple float '.1'.""",
        dict(),
        r'.1',
        0.1,
        None, None
    ),
    (
        r"""Simple float '1.'.""",
        dict(),
        r'1.',
        1.0,
        None, None
    ),

    (
        r"""Simple quoted string '"abc"'.""",
        dict(),
        r'"abc"',
        'abc',
        None, None
    ),
    (
        r"""Simple quoted string '"42"'.""",
        dict(),
        r'"42"',
        '42',
        None, None
    ),
    (
        r"""Simple quoted string '"true"'.""",
        dict(),
        r'"true"',
        'true',
        None, None
    ),
    (
        r"""Simple quoted string '"false"'.""",
        dict(),
        r'"false"',
        'false',
        None, None
    ),
    (
        r"""Simple quoted string '"null"'.""",
        dict(),
        r'"null"',
        'null',
        None, None
    ),
    (
        r"""Simple unquoted string 'abc'.""",
        dict(),
        r'abc',
        'abc',
        None, None
    ),
    (
        r"""Simple unquoted string 'a'.""",
        dict(),
        r'a',
        'a',
        None, None
    ),
    (
        r"""Simple quoted string with blank '"a b"'.""",
        dict(),
        r'"a b"',
        'a b',
        None, None
    ),
    (
        r"""Simple quoted string with escaped newline '"a\nb"'.""",
        dict(),
        r'"a\nb"',
        'a\nb',
        None, None
    ),
    (
        r"""Simple quoted string with escaped carriage return '"a\rb"'.""",
        dict(),
        r'"a\rb"',
        'a\rb',
        None, None
    ),
    (
        r"""Simple quoted string with escaped tab '"a\tb"'.""",
        dict(),
        r'"a\tb"',
        'a\tb',
        None, None
    ),
    (
        r"""Simple quoted string with escaped backslash '"a\\b"'.""",
        dict(),
        r'"a\\b"',
        'a\\b',
        None, None
    ),
    (
        r"""Invalid simple unquoted string with blank 'a b'.""",
        dict(),
        r'a b',
        None,
        NameValueParseError, r".*: Expected end of text, found 'b'.*"
    ),
    (
        r"""Invalid simple unquoted string with leading blank ' b'.""",
        dict(),
        r' b',
        None,
        NameValueParseError, r".*: , found 'b'.*"
    ),
    (
        r"""Simple unquoted string with trailing blank 'a '.""",
        # TODO: Find out why this is not invalid.
        dict(),
        r'a ',
        'a',
        None, None
    ),
    (
        r"""Invalid simple unquoted string with escaped newline 'a\nb'.""",
        dict(),
        r'a\nb',
        None,
        NameValueParseError, r".*: Expected end of text, found '\\'.*"
    ),

    (
        r"""Empty array.""",
        dict(),
        r'[]',
        [],
        None, None
    ),
    (
        r"""Array with one null value 'null'.""",
        dict(),
        r'[null]',
        [None],
        None, None
    ),
    (
        r"""Array with one boolean 'true'.""",
        dict(),
        r'[true]',
        [True],
        None, None
    ),
    (
        r"""Array with one boolean 'false'.""",
        dict(),
        r'[false]',
        [False],
        None, None
    ),
    (
        r"""Array with one int '42'.""",
        dict(),
        r'[42]',
        [42],
        None, None
    ),
    (
        r"""Array with one float '42.0'.""",
        dict(),
        r'[42.0]',
        [42.0],
        None, None
    ),
    (
        r"""Array with one quoted string '"null"'.""",
        dict(),
        r'["null"]',
        ['null'],
        None, None
    ),
    (
        r"""Array with one quoted string '"true"'.""",
        dict(),
        r'["true"]',
        ['true'],
        None, None
    ),
    (
        r"""Array with one quoted string '"false"'.""",
        dict(),
        r'["false"]',
        ['false'],
        None, None
    ),
    (
        r"""Array with one quoted string '"a"'.""",
        dict(),
        r'["a"]',
        ['a'],
        None, None
    ),
    (
        r"""Array with one unquoted string 'a'.""",
        dict(),
        r'[a]',
        ['a'],
        None, None
    ),
    (
        r"""Array with one quoted string '"a]"'.""",
        dict(),
        r'["a]"]',
        ['a]'],
        None, None
    ),
    (
        r"""Array with one quoted string '"[a"'.""",
        dict(),
        r'["[a"]',
        ['[a'],
        None, None
    ),
    (
        r"""Array with two int items.""",
        dict(),
        r'[42,43]',
        [42, 43],
        None, None
    ),
    (
        r"""Invalid array with unquoted string with blank 'a b'.""",
        dict(),
        r'[a b]',
        None,
        NameValueParseError, r".*: , found 'b'.*"
    ),
    (
        r"""Array with unquoted string with leading blank ' b'.""",
        # TODO: Find out why this is not invalid.
        dict(),
        r'[ b]',
        ['b'],
        None, None
    ),
    (
        r"""Array with unquoted string with trailing blank 'a '.""",
        # TODO: Find out why this is not invalid.
        dict(),
        r'[a ]',
        ['a'],
        None, None
    ),
    (
        r"""Invalid array with trailing comma after one item.""",
        dict(),
        r'[42,]',
        None,
        NameValueParseError, r".*: , found ','.*"
    ),
    (
        r"""Invalid array with leading comma before one item.""",
        dict(),
        r'[,42]',
        None,
        NameValueParseError, r".*: , found ','.*"
    ),
    (
        r"""Invalid array with two commas between two items.""",
        dict(),
        r'[42,,43]',
        None,
        NameValueParseError, r".*: , found ','.*"
    ),
    (
        r"""Invalid array with missing closing ']'.""",
        dict(),
        r'[42',
        None,
        NameValueParseError, r".*: , found end of text.*"
    ),
    (
        r"""Invalid array with missing opening '['.""",
        dict(),
        r'42]',
        None,
        NameValueParseError, r".*: Expected end of text, found '\]'.*"
    ),
    (
        r"""Invalid array with additional '[' after begin.""",
        dict(),
        r'[[42]',
        None,
        NameValueParseError, r".*: , found end of text.*"
    ),
    (
        r"""Invalid array with additional ']'after begin.""",
        dict(),
        r'[]42]',
        None,
        NameValueParseError, r".*: Expected end of text, found '42'.*"
    ),
    (
        r"""Invalid array with additional '[' before end.""",
        dict(),
        r'[42[]',
        None,
        NameValueParseError, r".*: , found '\['.*"
    ),
    (
        r"""Invalid array with additional ']' before end.""",
        dict(),
        r'[42]]',
        None,
        NameValueParseError, r".*: Expected end of text, found '\]'.*"
    ),

    (
        r"""Array with one nested empty array.""",
        dict(),
        r'[[]]',
        [[]],
        None, None
    ),
    (
        r"""Array with one nested empty object.""",
        dict(),
        r'[{}]',
        [dict()],
        None, None
    ),
    (
        r"""Array with one nested array that has one item.""",
        dict(),
        r'[[42]]',
        [[42]],
        None, None
    ),
    (
        r"""Array with one nested object that has one item.""",
        dict(),
        r'[{x=42}]',
        [dict(x=42)],
        None, None
    ),
    (
        r"""Array with two nested array items.""",
        dict(),
        r'[[42,43],[]]',
        [[42, 43], []],
        None, None
    ),
    (
        r"""Array with deeply nested array items.""",
        dict(),
        r'[a,[b,[c,[d,e]]]]',
        ['a', ['b', ['c', ['d', 'e']]]],
        None, None
    ),

    (
        r"""Empty object.""",
        dict(),
        r'{}',
        dict(),
        None, None
    ),
    (
        r"""Object with one item of value 'null'.""",
        dict(),
        r'{x=null}',
        dict(x=None),
        None, None
    ),
    (
        r"""Object with one item of boolean value 'true'.""",
        dict(),
        r'{x=true}',
        dict(x=True),
        None, None
    ),
    (
        r"""Object with one item of boolean value 'false'.""",
        dict(),
        r'{x=false}',
        dict(x=False),
        None, None
    ),
    (
        r"""Object with one item of int value '42'.""",
        dict(),
        r'{x=42}',
        dict(x=42),
        None, None
    ),
    (
        r"""Object with one item of float value '42.0'.""",
        dict(),
        r'{x=42.0}',
        dict(x=42.0),
        None, None
    ),
    (
        r"""Object with one item of quoted string value '"null"'.""",
        dict(),
        r'{x="null"}',
        dict(x='null'),
        None, None
    ),
    (
        r"""Object with one item of quoted string value '"true"'.""",
        dict(),
        r'{x="true"}',
        dict(x='true'),
        None, None
    ),
    (
        r"""Object with one item of quoted string value '"false"'.""",
        dict(),
        r'{x="false"}',
        dict(x='false'),
        None, None
    ),
    (
        r"""Object with one item of quoted string value '"a"'.""",
        dict(),
        r'{x="a"}',
        dict(x='a'),
        None, None
    ),
    (
        r"""Object with one item of unquoted string value 'a'.""",
        dict(),
        r'{x=a}',
        dict(x='a'),
        None, None
    ),
    (
        r"""Object with one item of quoted string value '"a}"'.""",
        dict(),
        r'{x="a}"}',
        dict(x='a}'),
        None, None
    ),
    (
        r"""Object with one item of quoted string value '"{a"'.""",
        dict(),
        r'{x="{a"}',
        dict(x='{a'),
        None, None
    ),
    (
        r"""Object with two items of int values.""",
        dict(),
        r'{x=42,y=43}',
        dict(x=42, y=43),
        None, None
    ),
    (
        r"""Object with one item of unquoted string value with blank 'a b'.""",
        dict(),
        r'{x=a b}',
        None,
        NameValueParseError, r".*: , found 'b'.*"
    ),
    (
        r"""Object with one item of unquoted string value with leading """
        r"""blank ' b'.""",
        dict(),
        r'{x= b}',
        None,
        NameValueParseError, r".*: , found 'x'.*"
    ),
    (
        r"""Object with one item of unquoted string value with trailing """
        r"""blank 'a '.""",
        # TODO: Find out why this is not invalid.
        dict(),
        r'{x=a }',
        dict(x='a'),
        None, None
    ),

    (
        r"""Object with one item of name with hyphen.""",
        dict(),
        r'{abc-def=42}',
        {'abc-def': 42},
        None, None
    ),
    (
        r"""Object with one item of name with underscore.""",
        dict(),
        r'{abc_def=42}',
        {'abc_def': 42},
        None, None
    ),
    (
        r"""Object with one item of name with numeric.""",
        dict(),
        r'{a0=42}',
        {'a0': 42},
        None, None
    ),
    (
        r"""Object with one item of name with leading hyphen.""",
        dict(),
        r'{-a=42}',
        None,
        NameValueParseError, r".*: , found '-'.*"
    ),
    (
        r"""Object with one item of name with leading underscore.""",
        dict(),
        r'{_a=42}',
        None,
        NameValueParseError, r".*: , found '_'.*"
    ),
    (
        r"""Object with one item of name with leading numeric.""",
        dict(),
        r'{0x=42}',
        None,
        NameValueParseError, r".*: , found '0x'.*"
    ),
    (
        r"""Invalid object with one item of name/value with '='""",
        dict(),
        r'{a=b=42}',
        None,
        NameValueParseError, r".*: , found '='.*"
    ),
    (
        r"""Invalid object with one item with trailing comma.""",
        dict(),
        r'{x=42,}',
        None,
        NameValueParseError, r".*: , found ','.*"
    ),
    (
        r"""Invalid object with one item with leading comma.""",
        dict(),
        r'{x=,42}',
        None,
        NameValueParseError, r".*: , found 'x'.*"
    ),
    (
        r"""Invalid object with two commas between two items.""",
        dict(),
        r'{x=42,,y=43}',
        None,
        NameValueParseError, r".*: , found ','.*"
    ),
    (
        r"""Invalid object with missing closing '}'.""",
        dict(),
        r'{x=42',
        None,
        NameValueParseError, r".*: , found end of text.*"
    ),
    (
        r"""Invalid object with missing opening '{'.""",
        dict(),
        r'x=42}',
        None,
        NameValueParseError, r".*: Expected end of text, found '='.*"
    ),
    (
        r"""Invalid object with additional '{' after begin.""",
        dict(),
        r'{{x=42}',
        None,
        NameValueParseError, r".*: , found '\{'.*"
    ),
    (
        r"""Invalid object with additional '}' after begin.""",
        dict(),
        r'{}x=42}',
        None,
        NameValueParseError, r".*: Expected end of text, found 'x'.*"
    ),
    (
        r"""Invalid object with additional '{' before end.""",
        dict(),
        r'{x=42{}',
        None,
        NameValueParseError, r".*: , found '\{'.*"
    ),
    (
        r"""Invalid object with additional '}' before end.""",
        dict(),
        r'{x=42}}',
        None,
        NameValueParseError, r".*: Expected end of text, found '\}'.*"
    ),

    (
        r"""Object with nested empty object.""",
        dict(),
        r'{x={}}',
        dict(x=dict()),
        None, None
    ),
    (
        r"""Object with nested empty array.""",
        dict(),
        r'{x=[]}',
        dict(x=[]),
        None, None
    ),
    (
        r"""Object with nested object that has one item.""",
        dict(),
        r'{x={y=42}}',
        dict(x=dict(y=42)),
        None, None
    ),
    (
        r"""Object with nested array that has one item.""",
        dict(),
        r'{x=[42]}',
        dict(x=[42]),
        None, None
    ),
    (
        r"""Object with deeply nested object items.""",
        dict(),
        r'{a={b={c={d=x,e=y}}}}',
        dict(a=dict(b=dict(c=dict(d='x', e='y')))),
        None, None
    ),

    (
        r"""Non-default quoting char "'".""",
        dict(quoting_char="'"),
        r"'a'",
        'a',
        None, None
    ),
    (
        r"""Non-default separator char ';'.""",
        dict(separator_char=';'),
        r'[42;43]',
        [42, 43],
        None, None
    ),
    (
        r"""Invalid non-default separator char ' '.""",
        dict(separator_char=' '),
        r'[42 43]',
        None,
        NameValueParseError, r".*: , found '43'.*"
    ),
    (
        r"""Non-default assignment char ':'.""",
        dict(assignment_char=':'),
        r'{x:42}',
        dict(x=42),
        None, None
    ),
    # TODO: Add more testcases with non-default special characters
]


@pytest.mark.parametrize(
    "desc, init_kwargs, input_value, exp_result, exp_exc_type, "
    "exp_exc_message",
    TESTCASES_NAME_VALUE_PARSER_PARSE)
def test_name_value_parser_parse(
        desc, init_kwargs, input_value, exp_result, exp_exc_type,
        exp_exc_message):
    # pylint: disable=unused-argument
    """
    Test NameValueParser.parse() method.
    """

    parser = NameValueParser(**init_kwargs)

    if exp_exc_type is None:

        # The code to be tested
        result = parser.parse(input_value)

        assert result == exp_result

    else:

        with pytest.raises(exp_exc_type) as exc_info:

            # The code to be tested
            parser.parse(input_value)

        exc_value = exc_info.value
        exc_message = str(exc_value)
        match_str = exp_exc_message + '$'
        assert re.match(match_str, exc_message)
