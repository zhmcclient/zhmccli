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


import sys
import platform
import re
import csv
import tempfile
import pytest

from zhmccli._helper import CSV_DELIM, CSV_QUOTE, CSV_QUOTING


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
