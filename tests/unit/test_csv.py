# Copyright 2025 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test the behavior of the Python 'csv' module for our purposes.
"""

import io
import sys
import platform
import re
import csv
import tempfile
import pytest

from zhmccli._helper import CSV_DELIM, CSV_QUOTE, CSV_QUOTING

# Boolean indicating that we run on Python 3.12
PY_312 = (sys.version_info >= (3, 12) and sys.version_info < (3, 13))

PROP_NAMES = ['p1', 'p2']
PROPS_LIST = [
    {'p1': 'a1', 'p2': 'a2'},
    {'p1': 'b1', 'p2': 'b2'},
]


@pytest.mark.parametrize(
    "lineterminator", ["\r\n", "\n"]
)
def test_csv_newlines_file(lineterminator):
    """
    Test the behavior of the Python 'csv' module w.r.t. newlines with a file.
    """

    # Verify the parameters of sys.stdout
    assert sys.stdout.mode == "w"
    assert sys.stdout.newlines is None

    # Open the file with the same parameters as sys.stdout
    with tempfile.NamedTemporaryFile(
            suffix='.csv', delete=False,
            mode="w", newline=None, encoding=sys.stdout.encoding) as csvfile:

        # Write file CSV file using the csv module, compatible to how it would
        # be done on sys.stdout.
        writer = csv.DictWriter(
            csvfile, fieldnames=PROP_NAMES, lineterminator=lineterminator,
            delimiter=CSV_DELIM, quotechar=CSV_QUOTE, quoting=CSV_QUOTING)
        writer.writeheader()
        for props in PROPS_LIST:
            writer.writerow(props)
        csvfile.close()

        # Read the CSV file in binary mode, to get at the newline characters in
        # the file without any additional translation.
        with open(csvfile.name, 'rb') as csvfile2:
            content = csvfile2.read()
        content = content.decode(sys.stdout.encoding)
        m = re.search(r"[^\r\n]([\r\n]+)[^\r\n]", content)
        assert m is not None
        newline_chars = m.group(1)

        # Verify the expectation for the newline characters.
        if platform.system() == "Windows":
            assert newline_chars == "\r" + lineterminator
        else:
            assert newline_chars == lineterminator


@pytest.mark.parametrize(
    "lineterminator", ["\r\n", "\n"]
)
def test_csv_newlines_stdout(capsys, lineterminator):
    """
    Test the behavior of the Python 'csv' module w.r.t. newlines with stdout.
    """

    # Write file CSV file using the csv module, compatible to how it would
    # be done on sys.stdout.
    writer = csv.DictWriter(
        sys.stdout, fieldnames=PROP_NAMES, lineterminator=lineterminator,
        delimiter=CSV_DELIM, quotechar=CSV_QUOTE, quoting=CSV_QUOTING)
    writer.writeheader()
    for props in PROPS_LIST:
        writer.writerow(props)

    captured = capsys.readouterr()
    content = captured.out

    m = re.search(r"[^\r\n]([\r\n]+)[^\r\n]", content)
    assert m is not None
    newline_chars = m.group(1)

    # Verify the expectation for the newline characters.
    assert newline_chars == lineterminator


ALLTYPES_FIELD_NAMES = [
    "str", "int", "float", "bool", "none", "list", "dict", "set"
]
ALLTYPES_FIELD_ROWS = [
    {
        "str": "foo", "int": 42, "float": 3.14, "bool": True,
        "none": None, "list": ["a", "b"], "dict": {"a": 1, "b": 2},
        "set": {"a"},
        # Note: sets are not reliably ordered, so not testing with
        # multiple items.
    },
    {
        "str": "", "int": 0, "float": 0.0, "bool": False,
        "none": None, "list": ["a"], "dict": {"a": 1}, "set": {"a"},
    },
    {
        "str": "", "int": 0, "float": 0.0, "bool": False,
        "none": None, "list": [], "dict": {}, "set": {},
    },
]

TESTCASES_CSV_DICTWRITER = [
    # Testcases for test_csv_dictwriter(). Each list item is a testcase tuple
    # with:
    # - field_names (list): Field names
    # - field_rows (list): Field rows
    # - quoting_attr (str): Attr name of csv.QUOTE_* quoting constant to be used
    # - exp_csv_content (str): Expected content of .csv file
    # Note: csv.QUOTE_STRINGS and csv.QUOTE_NOTNULL were added in Python 3.12.
    #       Testcases using them will be skipped below Python 3.12.
    (
        ALLTYPES_FIELD_NAMES,
        ALLTYPES_FIELD_ROWS,
        "QUOTE_STRINGS",
        """\
"str","int","float","bool","none","list","dict","set"
"foo",42,3.14,True,,"['a', 'b']","{'a': 1, 'b': 2}",{'a'}
"",0,0.0,False,,['a'],{'a': 1},{'a'}
"",0,0.0,False,,[],{},{}
"""
    ),
    (
        ALLTYPES_FIELD_NAMES,
        ALLTYPES_FIELD_ROWS,
        "QUOTE_NONNUMERIC",
        """\
"str","int","float","bool","none","list","dict","set"
"foo",42,3.14,True,"","['a', 'b']","{'a': 1, 'b': 2}","{'a'}"
"",0,0.0,False,"","['a']","{'a': 1}","{'a'}"
"",0,0.0,False,"","[]","{}","{}"
"""
    ),
    (
        ALLTYPES_FIELD_NAMES,
        ALLTYPES_FIELD_ROWS,
        "QUOTE_NOTNULL",
        """\
"str","int","float","bool","none","list","dict","set"
"foo","42","3.14","True",,"['a', 'b']","{'a': 1, 'b': 2}","{'a'}"
"","0","0.0","False",,"['a']","{'a': 1}","{'a'}"
"","0","0.0","False",,"[]","{}","{}"
"""
    ),
    (
        ALLTYPES_FIELD_NAMES,
        ALLTYPES_FIELD_ROWS,
        "QUOTE_MINIMAL",
        """\
str,int,float,bool,none,list,dict,set
foo,42,3.14,True,,"['a', 'b']","{'a': 1, 'b': 2}",{'a'}
,0,0.0,False,,['a'],{'a': 1},{'a'}
,0,0.0,False,,[],{},{}
"""
    ),
]


@pytest.mark.parametrize(
    "field_names, field_rows, quoting_attr, exp_csv_content",
    TESTCASES_CSV_DICTWRITER
)
def test_csv_dictwriter(field_names, field_rows, quoting_attr, exp_csv_content):
    """
    Test the behavior of the Python 'csv.DictWriter' class for different quoting
    modes.
    """

    quoting = getattr(csv, quoting_attr, None)
    if quoting is None:
        pytest.skip(f"This Python version does not support csv.{quoting_attr}")

    csv_stream = io.StringIO()

    # The code to be tested
    writer = csv.DictWriter(
        csv_stream, fieldnames=field_names, lineterminator="\n",
        delimiter=CSV_DELIM, quotechar=CSV_QUOTE, quoting=quoting)
    writer.writeheader()
    for row in field_rows:
        writer.writerow(row)

    # Verify the .csv content
    csv_stream.seek(0)
    csv_content = csv_stream.read()
    assert csv_content == exp_csv_content


TESTCASES_CSV_DICTREADER = [
    # Testcases for test_csv_dictreader(). Each list item is a testcase tuple
    # with:
    # - csv_content (str): Content of .csv file
    # - quoting_attr (str): Attr name of csv.QUOTE_* quoting constant to be used
    # - exp_exc_type (type): Expected exception type, or None for success
    # - exp_exc_msg (str): Expected exception message pattern, or None
    # - exp_field_rows (list): Expected field rows
    # Note: csv.QUOTE_STRINGS and csv.QUOTE_NOTNULL were added in Python 3.12.
    #       Testcases using them will be skipped below Python 3.12.
    # Note: csv.QUOTE_STRINGS has a bug in Python 3.12 in that it behaves like
    #       csv.QUOTE_NONNUMERIC. The bug was fixed in Python 3.13.
    (
        """\
"str","int","float","none"
"foo",42,3.14,
"",0,0.0,
""",
        "QUOTE_STRINGS",
        None,
        None,
        [
            {
                "str": "foo",
                "int": "42" if PY_312 else 42,
                "float": "3.14" if PY_312 else 3.14,
                "none": "" if PY_312 else None,
            },
            {
                "str": "",
                "int": "0" if PY_312 else 0,
                "float": "0.0" if PY_312 else 0.0,
                "none": "" if PY_312 else None,
            },
        ]
    ),
    (
        """\
str,int,float,none
foo,42,3.14,
"",0,0.0,
""",
        "QUOTE_MINIMAL",
        None,
        None,
        [
            {
                "str": "foo",
                "int": "42",
                "float": "3.14",
                "none": "",
            },
            {
                "str": "",
                "int": "0",
                "float": "0.0",
                "none": "",
            },
        ]
    ),
    (
        """\
"bool"
True
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"bool": "True"}] if PY_312 else None
    ),
    (
        """\
"bool"
True
""",
        "QUOTE_MINIMAL",
        None,
        None,
        [{"bool": "True"}]
    ),
    (
        """\
"bool"
False
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"bool": "False"}] if PY_312 else None
    ),
    (
        """\
"bool"
False
""",
        "QUOTE_MINIMAL",
        None,
        None,
        [{"bool": "False"}]
    ),
    (
        """\
"list"
[]
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"list": "[]"}] if PY_312 else None
    ),
    (
        """\
"list"
[]
""",
        "QUOTE_MINIMAL",
        None,
        None,
        [{"list": "[]"}]
    ),
    (
        """\
"list"
['a']
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"list": "['a']"}] if PY_312 else None
    ),
    (
        """\
"list"
['a']
""",
        "QUOTE_MINIMAL",
        None,
        None,
        [{"list": "['a']"}]
    ),
    (
        """\
"list"
['a', 'b']
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"list": "['a'", None: [" 'b']"]}] if PY_312 else None  # ???
    ),
    (
        """\
"list"
['a', 'b']
""",
        "QUOTE_MINIMAL",
        None,
        None,
        [{"list": "['a'", None: [" 'b']"]}]  # ???
    ),
    (
        """\
"dict"
{}
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"dict": "{}"}] if PY_312 else None
    ),
    (
        """\
"dict"
{'a': 1}
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"dict": "{'a': 1}"}] if PY_312 else None
    ),
    (
        """\
"dict"
{'a': 1, 'b': 2}
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"dict": "{'a': 1", None: [" 'b': 2}"]}] if PY_312 else None  # ???
    ),
    (
        """\
"set"
{'a'}
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"set": "{'a'}"}] if PY_312 else None
    ),
    (
        """\
"set"
{'a', 'b'}
""",
        "QUOTE_STRINGS",
        None if PY_312 else ValueError,
        None if PY_312 else "could not convert string to float:",
        [{"set": "{'a'", None: [" 'b'}"]}] if PY_312 else None
    ),
]


@pytest.mark.parametrize(
    "csv_content, quoting_attr, exp_exc_type, exp_exc_msg, exp_field_rows",
    TESTCASES_CSV_DICTREADER
)
def test_csv_dictreader(
        csv_content, quoting_attr, exp_exc_type, exp_exc_msg, exp_field_rows):
    """
    Test the behavior of the Python 'csv.DictReader' class for different quoting
    modes.
    """

    quoting = getattr(csv, quoting_attr, None)
    if quoting is None:
        pytest.skip(f"This Python version does not support csv.{quoting_attr}")

    csv_stream = io.StringIO()

    # Prepare the .csv content
    csv_stream.write(csv_content)
    csv_stream.seek(0)

    if exp_exc_type:
        with pytest.raises(exp_exc_type) as exc_info:

            # The code to be tested
            # Note: The list() causes the returned generator to be traversed,
            #       and that is needed in order to provoke the error.
            _ = list(csv.DictReader(
                csv_stream, lineterminator="\n", delimiter=CSV_DELIM,
                quotechar=CSV_QUOTE, quoting=quoting))

        exc = exc_info.value
        assert re.search(exp_exc_msg, str(exc)) is not None
    else:

        # The code to be tested
        rows = list(csv.DictReader(
            csv_stream, lineterminator="\n", delimiter=CSV_DELIM,
            quotechar=CSV_QUOTE, quoting=quoting))

        # Verify that the data that was read
        for i, row in enumerate(rows):
            exp_row = exp_field_rows[i]
            exp_field_names = list(exp_row.keys())
            assert list(row.keys()) == exp_field_names
            for name in exp_field_names:
                assert row[name] == exp_row[name]
