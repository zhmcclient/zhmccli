# Copyright 2017,2019 IBM Corp. All Rights Reserved.
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
Function tests for global options, using faked HMCs (zhmcclient mock).
"""

import os
import subprocess
import re
import json
import pytest
from zhmcclient import Client
from zhmcclient_mock import FakedSession

from zhmccli._helper import convert_ec_mcl_description

from .utils import call_zhmc_child, call_zhmc_inline, assert_rc, \
    assert_patterns

TEST_LOGFILE = 'tmp_testfile.log'


def setup_faked_hmc():
    """
    Set up a faked HMC with two CPC resources.

    Returns:
      FakedSession: The faked session.
    """
    faked_session = FakedSession(
        'fake-host', 'hmc1', '2.16', '4.10',
        userid='fake-user')

    faked_session.hmc.consoles.add({
        'object-id': None,
        # object-uri will be automatically set
        'parent': None,
        'class': 'console',
        'name': 'fake-console1',
        'description': 'Console #1',
        "ec-mcl-description": {
            "ec": [
                {
                    "number": "P41499",
                    "part-number": "01LL062",
                    "mcl": [
                        {
                            "level": "333",
                            "type": "retrieved",
                            "last-update": 1650524126000
                        },
                        {
                            "level": "333",
                            "type": "activated",
                            "last-update": 1650526481000
                        },
                        {
                            "level": "327",
                            "type": "accepted",
                            "last-update": 1642750400000
                        },
                        {
                            "level": "333",
                            "type": "installable-concurrent",
                            "last-update": None
                        },
                        {
                            "level": "328",
                            "type": "removable-concurrent",
                            "last-update": None
                        }
                    ],
                    "description": "Hardware Management Console Framework",
                    "type": "SYSTEM"
                },
                {
                    "number": "P41470",
                    "part-number": "01LL058",
                    "mcl": [
                        {
                            "level": "2",
                            "type": "retrieved",
                            "last-update": 1566551669000
                        },
                        {
                            "level": "2",
                            "type": "activated",
                            "last-update": 1566551779000
                        },
                        {
                            "level": "2",
                            "type": "accepted",
                            "last-update": 1566553286000
                        },
                        {
                            "level": "2",
                            "type": "installable-concurrent",
                            "last-update": None
                        },
                        {
                            "level": "000",
                            "type": "removable-concurrent",
                            "last-update": None
                        }
                    ],
                    "description": "Hardware Management Console Platform Fw",
                    "type": "HMCBIOS"
                }
            ]
        }
    })

    faked_session.hmc.cpcs.add({
        'object-id': 'fake-cpc1-oid',
        # object-uri is set up automatically
        'parent': None,
        'class': 'cpc',
        'name': 'CPC1',
        'description': 'CPC 1 (classic mode)',
        'status': 'operating',
        'dpm-enabled': False,
        'se-version': '2.16',
        'machine-type': '3931',
        'machine-model': 'A01',
        'machine-serial-number': 'SN-CPC1',
    })
    faked_session.hmc.cpcs.add({
        'object-id': 'fake-cpc2-oid',
        # object-uri is set up automatically
        'parent': None,
        'class': 'cpc',
        'name': 'CPC2',
        'description': 'CPC 2 (DPM mode)',
        'status': 'active',
        'dpm-enabled': True,
        'se-version': '2.16',
        'machine-type': '3931',
        'machine-model': 'LA1',
        'machine-serial-number': 'SN-CPC2',
    })

    return faked_session


def test_option_help():
    """
    Test 'zhmc --help'
    """

    rc, stdout, stderr = call_zhmc_child(['--help'])

    assert_rc(0, rc, stdout, stderr)
    assert stdout.startswith(
        "Usage: zhmc [GENERAL-OPTIONS] COMMAND [ARGS]...\n"), \
        f"stdout={stdout!r}"
    assert stderr == ""


def test_option_version():
    """
    Test 'zhmc --version'
    """

    rc, stdout, stderr = call_zhmc_child(['--version'])

    assert_rc(0, rc, stdout, stderr)
    assert re.match(r'^zhmc, version [0-9]+\.[0-9]+\.[0-9]+', stdout)
    assert stderr == ""


OPTION_FORMAT_TABLE_PROPS_TESTCASES = [
    ('table',
     # Order of properties must match:
     '+-------------------+----------+\n'
     '| Field Name        | Value    |\n'
     '|-------------------+----------|\n'
     '| api-major-version | {v[amaj]:<8} |\n'
     '| api-minor-version | {v[amin]:<8} |\n'
     '| hmc-name          | {v[hnam]:8} |\n'
     '| hmc-version       | {v[hver]:8} |\n'
     '+-------------------+----------+\n'),
    ('plain',
     # Order of properties must match:
     'Field Name         Value\n'
     'api-major-version  {v[amaj]}\n'
     'api-minor-version  {v[amin]}\n'
     'hmc-name           {v[hnam]}\n'
     'hmc-version        {v[hver]}\n'),
    ('simple',
     # Order of properties must match:
     'Field Name         Value\n'
     '-----------------  --------\n'
     'api-major-version  {v[amaj]}\n'
     'api-minor-version  {v[amin]}\n'
     'hmc-name           {v[hnam]}\n'
     'hmc-version        {v[hver]}\n'),
    ('psql',
     # Order of properties must match:
     '+-------------------+----------+\n'
     '| Field Name        | Value    |\n'
     '|-------------------+----------|\n'
     '| api-major-version | {v[amaj]:<8} |\n'
     '| api-minor-version | {v[amin]:<8} |\n'
     '| hmc-name          | {v[hnam]:8} |\n'
     '| hmc-version       | {v[hver]:8} |\n'
     '+-------------------+----------+\n'),
    ('rst',
     # Order of properties must match:
     '=================  ========\n'
     'Field Name         Value\n'
     '=================  ========\n'
     'api-major-version  {v[amaj]}\n'
     'api-minor-version  {v[amin]}\n'
     'hmc-name           {v[hnam]}\n'
     'hmc-version        {v[hver]}\n'
     '=================  ========\n'),
    ('mediawiki',
     # Order of properties must match:
     '{{| class="wikitable" style="text-align: left;"\n'
     '|+ <!-- caption -->\n'
     '|-\n'
     '! Field Name        !! Value\n'
     '|-\n'
     '| api-major-version || {v[amaj]}\n'
     '|-\n'
     '| api-minor-version || {v[amin]}\n'
     '|-\n'
     '| hmc-name          || {v[hnam]}\n'
     '|-\n'
     '| hmc-version       || {v[hver]}\n'
     '|}}\n'),
    ('html',
     # Order of properties must match:
     '<table>\n'
     '<thead>\n'
     '<tr><th>Field Name       </th><th>Value   </th></tr>\n'
     '</thead>\n'
     '<tbody>\n'
     '<tr><td>api-major-version</td><td>{v[amaj]:<8}</td></tr>\n'
     '<tr><td>api-minor-version</td><td>{v[amin]:<8}</td></tr>\n'
     '<tr><td>hmc-name         </td><td>{v[hnam]:8}</td></tr>\n'
     '<tr><td>hmc-version      </td><td>{v[hver]:8}</td></tr>\n'
     '</tbody>\n'
     '</table>\n'),
    ('latex',
     # Order of properties must match:
     '\\begin{{tabular}}{{ll}}\n'
     '\\hline\n'
     ' Field Name        & Value    \\\\\n'
     '\\hline\n'
     ' api-major-version & {v[amaj]:<8} \\\\\n'
     ' api-minor-version & {v[amin]:<8} \\\\\n'
     ' hmc-name          & {v[hnam]:8} \\\\\n'
     ' hmc-version       & {v[hver]:8} \\\\\n'
     '\\hline\n'
     '\\end{{tabular}}\n'),
]


@pytest.mark.parametrize(
    "out_format, exp_stdout_template",
    OPTION_FORMAT_TABLE_PROPS_TESTCASES
)
@pytest.mark.parametrize(
    # Transpose only affects metrics output, but not info output.
    # Transpose is accepted and ignored for all table output formats.
    "transpose_opt", [
        None,
        '-x',
        '--transpose',
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('hmc-name', '2.14.0', '2.20'),
    ]
)
def test_option_format_table_props(
        hmc_name, hmc_version, api_version, out_opt, transpose_opt, out_format,
        exp_stdout_template):
    """
    Test global options (-o, --output-format) and (-x, --transpose), for all
    table formats, with the 'zhmc info' command which displays properties.
    """

    faked_session = FakedSession(
        'fake-host', hmc_name, hmc_version, api_version,
        userid='fake-user')

    api_version_parts = [int(vp) for vp in api_version.split('.')]
    exp_values = {
        'hnam': hmc_name,
        'hver': hmc_version,
        'amaj': api_version_parts[0],
        'amin': api_version_parts[1],
    }
    exp_stdout = exp_stdout_template.format(v=exp_values)

    args = [out_opt, out_format]
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.append('info')

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(0, rc, stdout, stderr)
    assert stdout == exp_stdout
    assert stderr == ""


# pylint: disable=line-too-long
OPTION_FORMAT_TABLE_RES_TESTCASES = [
    ('table',
     """+--------+-----------+---------------+--------------+----------------+-----------------+-------------------------+----------------------+
| name   | status    | dpm-enabled   | se-version   | machine-type   | machine-model   | machine-serial-number   | description          |
|--------+-----------+---------------+--------------+----------------+-----------------+-------------------------+----------------------|
| {c1[name]:<6} | {c1[status]:<9} | {c1[dpm-enabled]!r:<13} | {c1[se-version]:<12} | {c1[machine-type]:<14} | {c1[machine-model]:<15} | {c1[machine-serial-number]:<23} | {c1[description]:<20} |
| {c2[name]:<6} | {c2[status]:<9} | {c2[dpm-enabled]!r:<13} | {c2[se-version]:<12} | {c2[machine-type]:<14} | {c2[machine-model]:<15} | {c2[machine-serial-number]:<23} | {c2[description]:<20} |
+--------+-----------+---------------+--------------+----------------+-----------------+-------------------------+----------------------+
"""),  # noqa: E501
    ('plain',
     """name    status     dpm-enabled    se-version    machine-type    machine-model    machine-serial-number    description
{c1[name]:<6}  {c1[status]:<9}  {c1[dpm-enabled]!r:<13}  {c1[se-version]:<12}  {c1[machine-type]:<14}  {c1[machine-model]:<15}  {c1[machine-serial-number]:<23}  {c1[description]}
{c2[name]:<6}  {c2[status]:<9}  {c2[dpm-enabled]!r:<13}  {c2[se-version]:<12}  {c2[machine-type]:<14}  {c2[machine-model]:<15}  {c2[machine-serial-number]:<23}  {c2[description]}
"""),  # noqa: E501
    ('simple',
     """name    status     dpm-enabled    se-version    machine-type    machine-model    machine-serial-number    description
------  ---------  -------------  ------------  --------------  ---------------  -----------------------  --------------------
{c1[name]:<6}  {c1[status]:<9}  {c1[dpm-enabled]!r:<13}  {c1[se-version]:<12}  {c1[machine-type]:<14}  {c1[machine-model]:<15}  {c1[machine-serial-number]:<23}  {c1[description]}
{c2[name]:<6}  {c2[status]:<9}  {c2[dpm-enabled]!r:<13}  {c2[se-version]:<12}  {c2[machine-type]:<14}  {c2[machine-model]:<15}  {c2[machine-serial-number]:<23}  {c2[description]}
"""),  # noqa: E501
    ('psql',
     """+--------+-----------+---------------+--------------+----------------+-----------------+-------------------------+----------------------+
| name   | status    | dpm-enabled   | se-version   | machine-type   | machine-model   | machine-serial-number   | description          |
|--------+-----------+---------------+--------------+----------------+-----------------+-------------------------+----------------------|
| {c1[name]:<6} | {c1[status]:<9} | {c1[dpm-enabled]!r:<13} | {c1[se-version]:<12} | {c1[machine-type]:<14} | {c1[machine-model]:<15} | {c1[machine-serial-number]:<23} | {c1[description]:<20} |
| {c2[name]:<6} | {c2[status]:<9} | {c2[dpm-enabled]!r:<13} | {c2[se-version]:<12} | {c2[machine-type]:<14} | {c2[machine-model]:<15} | {c2[machine-serial-number]:<23} | {c2[description]:<20} |
+--------+-----------+---------------+--------------+----------------+-----------------+-------------------------+----------------------+
"""),  # noqa: E501
    ('rst',
     """======  =========  =============  ============  ==============  ===============  =======================  ====================
name    status     dpm-enabled    se-version    machine-type    machine-model    machine-serial-number    description
======  =========  =============  ============  ==============  ===============  =======================  ====================
{c1[name]:<6}  {c1[status]:<9}  {c1[dpm-enabled]!r:<13}  {c1[se-version]:<12}  {c1[machine-type]:<14}  {c1[machine-model]:<15}  {c1[machine-serial-number]:<23}  {c1[description]}
{c2[name]:<6}  {c2[status]:<9}  {c2[dpm-enabled]!r:<13}  {c2[se-version]:<12}  {c2[machine-type]:<14}  {c2[machine-model]:<15}  {c2[machine-serial-number]:<23}  {c2[description]}
======  =========  =============  ============  ==============  ===============  =======================  ====================
"""),  # noqa: E501
    ('mediawiki',
     """{{| class="wikitable" style="text-align: left;"
|+ <!-- caption -->
|-
! name   !! status    !! dpm-enabled   !! se-version   !! machine-type   !! machine-model   !! machine-serial-number   !! description
|-
| {c1[name]:<6} || {c1[status]:<9} || {c1[dpm-enabled]!r:<13} || {c1[se-version]:<12} || {c1[machine-type]:<14} || {c1[machine-model]:<15} || {c1[machine-serial-number]:<23} || {c1[description]}
|-
| {c2[name]:<6} || {c2[status]:<9} || {c2[dpm-enabled]!r:<13} || {c2[se-version]:<12} || {c2[machine-type]:<14} || {c2[machine-model]:<15} || {c2[machine-serial-number]:<23} || {c2[description]}
|}}
"""),  # noqa: E501
    ('html',
     """<table>
<thead>
<tr><th>name  </th><th>status   </th><th>dpm-enabled  </th><th>se-version  </th><th>machine-type  </th><th>machine-model  </th><th>machine-serial-number  </th><th>description         </th></tr>
</thead>
<tbody>
<tr><td>{c1[name]:<6}</td><td>{c1[status]:<9}</td><td>{c1[dpm-enabled]!r:<13}</td><td>{c1[se-version]:<12}</td><td>{c1[machine-type]:<14}</td><td>{c1[machine-model]:<15}</td><td>{c1[machine-serial-number]:<23}</td><td>{c1[description]:<20}</td></tr>
<tr><td>{c2[name]:<6}</td><td>{c2[status]:<9}</td><td>{c2[dpm-enabled]!r:<13}</td><td>{c2[se-version]:<12}</td><td>{c2[machine-type]:<14}</td><td>{c2[machine-model]:<15}</td><td>{c2[machine-serial-number]:<23}</td><td>{c2[description]:<20}</td></tr>
</tbody>
</table>
"""),  # noqa: E501
    ('latex',
     """\\begin{{tabular}}{{llllllll}}
\\hline
 name   & status    & dpm-enabled   & se-version   & machine-type   & machine-model   & machine-serial-number   & description          \\\\
\\hline
 {c1[name]:<6} & {c1[status]:<9} & {c1[dpm-enabled]!r:<13} & {c1[se-version]:<12} & {c1[machine-type]:<14} & {c1[machine-model]:<15} & {c1[machine-serial-number]:<23} & {c1[description]:<20} \\\\
 {c2[name]:<6} & {c2[status]:<9} & {c2[dpm-enabled]!r:<13} & {c2[se-version]:<12} & {c2[machine-type]:<14} & {c2[machine-model]:<15} & {c2[machine-serial-number]:<23} & {c2[description]:<20} \\\\
\\hline
\\end{{tabular}}
"""),  # noqa: E501
]
# pylint: enable=line-too-long


@pytest.mark.parametrize(
    "out_format, exp_stdout_template",
    OPTION_FORMAT_TABLE_RES_TESTCASES
)
@pytest.mark.parametrize(
    # Transpose only affects metrics output, but not info output.
    # Transpose is accepted and ignored for all table output formats.
    "transpose_opt", [
        None,
        '-x',
        '--transpose',
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
def test_option_format_table_res(
        out_opt, transpose_opt, out_format, exp_stdout_template):
    """
    Test global options (-o, --output-format) and (-x, --transpose), for all
    table formats, with the 'zhmc cpc list' command which displays a list of
    resources.
    """

    faked_session = setup_faked_hmc()
    client = Client(faked_session)
    cpcs = client.cpcs.list(full_properties=True)
    cpc1 = cpcs[0]
    cpc2 = cpcs[1]

    exp_stdout = exp_stdout_template.format(
        c1=cpc1.properties, c2=cpc2.properties)

    args = [out_opt, out_format]
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.extend(['cpc', 'list'])

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(0, rc, stdout, stderr)
    assert stdout == exp_stdout, (
        "Unexpected stdout:\n"
        f"Actual: {stdout!r}\n"
        f"Expected: {exp_stdout!r}")
    assert stderr == ""


# pylint: disable=line-too-long
OPTION_FORMAT_TABLE_DICT_TESTCASES = [
    ('table',
     """+-------------+-----------------------------------------+-------------+--------------------+-------------+------------+------------------+
| ec-number   | description                             | retrieved   | installable-conc   | activated   | accepted   | removable-conc   |
|-------------+-----------------------------------------+-------------+--------------------+-------------+------------+------------------|
| {f1[ec-number]:<11} | {f1[description]:<39} | {f1[retrieved]:<11} | {f1[installable-conc]:<18} | {f1[activated]:<11} | {f1[accepted]:<10} | {f1[removable-conc]:<16} |
| {f2[ec-number]:<11} | {f2[description]:<39} | {f2[retrieved]:<11} | {f2[installable-conc]:<18} | {f2[activated]:<11} | {f2[accepted]:<10} | {f2[removable-conc]:<16} |
+-------------+-----------------------------------------+-------------+--------------------+-------------+------------+------------------+
"""),  # noqa: E501
    ('plain',
     """ec-number    description                              retrieved    installable-conc    activated    accepted    removable-conc
{f1[ec-number]:<11}  {f1[description]:<39}  {f1[retrieved]:<11}  {f1[installable-conc]:<18}  {f1[activated]:<11}  {f1[accepted]:<10}  {f1[removable-conc]}
{f2[ec-number]:<11}  {f2[description]:<39}  {f2[retrieved]:<11}  {f2[installable-conc]:<18}  {f2[activated]:<11}  {f2[accepted]:<10}  {f2[removable-conc]}
"""),  # noqa: E501
    ('simple',
     """ec-number    description                              retrieved    installable-conc    activated    accepted    removable-conc
-----------  ---------------------------------------  -----------  ------------------  -----------  ----------  ----------------
{f1[ec-number]:<11}  {f1[description]:<39}  {f1[retrieved]:<11}  {f1[installable-conc]:<18}  {f1[activated]:<11}  {f1[accepted]:<10}  {f1[removable-conc]}
{f2[ec-number]:<11}  {f2[description]:<39}  {f2[retrieved]:<11}  {f2[installable-conc]:<18}  {f2[activated]:<11}  {f2[accepted]:<10}  {f2[removable-conc]}
"""),  # noqa: E501
    ('psql',
     """+-------------+-----------------------------------------+-------------+--------------------+-------------+------------+------------------+
| ec-number   | description                             | retrieved   | installable-conc   | activated   | accepted   | removable-conc   |
|-------------+-----------------------------------------+-------------+--------------------+-------------+------------+------------------|
| {f1[ec-number]:<11} | {f1[description]:<39} | {f1[retrieved]:<11} | {f1[installable-conc]:<18} | {f1[activated]:<11} | {f1[accepted]:<10} | {f1[removable-conc]:<16} |
| {f2[ec-number]:<11} | {f2[description]:<39} | {f2[retrieved]:<11} | {f2[installable-conc]:<18} | {f2[activated]:<11} | {f2[accepted]:<10} | {f2[removable-conc]:<16} |
+-------------+-----------------------------------------+-------------+--------------------+-------------+------------+------------------+
"""),  # noqa: E501
    ('rst',
     """===========  =======================================  ===========  ==================  ===========  ==========  ================
ec-number    description                              retrieved    installable-conc    activated    accepted    removable-conc
===========  =======================================  ===========  ==================  ===========  ==========  ================
{f1[ec-number]:<11}  {f1[description]:<39}  {f1[retrieved]:<11}  {f1[installable-conc]:<18}  {f1[activated]:<11}  {f1[accepted]:<10}  {f1[removable-conc]}
{f2[ec-number]:<11}  {f2[description]:<39}  {f2[retrieved]:<11}  {f2[installable-conc]:<18}  {f2[activated]:<11}  {f2[accepted]:<10}  {f2[removable-conc]}
===========  =======================================  ===========  ==================  ===========  ==========  ================
"""),  # noqa: E501
    ('mediawiki',
     """{{| class="wikitable" style="text-align: left;"
|+ <!-- caption -->
|-
! ec-number   !! description                             !! retrieved   !! installable-conc   !! activated   !! accepted   !! removable-conc
|-
| {f1[ec-number]:<11} || {f1[description]:<39} || {f1[retrieved]:<11} || {f1[installable-conc]:<18} || {f1[activated]:<11} || {f1[accepted]:<10} || {f1[removable-conc]}
|-
| {f2[ec-number]:<11} || {f2[description]:<39} || {f2[retrieved]:<11} || {f2[installable-conc]:<18} || {f2[activated]:<11} || {f2[accepted]:<10} || {f2[removable-conc]}
|}}
"""),  # noqa: E501
    ('html',
     """<table>
<thead>
<tr><th>ec-number  </th><th>description                            </th><th>retrieved  </th><th>installable-conc  </th><th>activated  </th><th>accepted  </th><th>removable-conc  </th></tr>
</thead>
<tbody>
<tr><td>{f1[ec-number]:<11}</td><td>{f1[description]:<39}</td><td>{f1[retrieved]:<11}</td><td>{f1[installable-conc]:<18}</td><td>{f1[activated]:<11}</td><td>{f1[accepted]:<10}</td><td>{f1[removable-conc]:<16}</td></tr>
<tr><td>{f2[ec-number]:<11}</td><td>{f2[description]:<39}</td><td>{f2[retrieved]:<11}</td><td>{f2[installable-conc]:<18}</td><td>{f2[activated]:<11}</td><td>{f2[accepted]:<10}</td><td>{f2[removable-conc]:<16}</td></tr>
</tbody>
</table>
"""),  # noqa: E501
    ('latex',
     """\\begin{{tabular}}{{lllllll}}
\\hline
 ec-number   & description                             & retrieved   & installable-conc   & activated   & accepted   & removable-conc   \\\\
\\hline
 {f1[ec-number]:<11} & {f1[description]:<39} & {f1[retrieved]:<11} & {f1[installable-conc]:<18} & {f1[activated]:<11} & {f1[accepted]:<10} & {f1[removable-conc]:<16} \\\\
 {f2[ec-number]:<11} & {f2[description]:<39} & {f2[retrieved]:<11} & {f2[installable-conc]:<18} & {f2[activated]:<11} & {f2[accepted]:<10} & {f2[removable-conc]:<16} \\\\
\\hline
\\end{{tabular}}
"""),  # noqa: E501
]
# pylint: enable=line-too-long


@pytest.mark.parametrize(
    "out_format, exp_stdout_template",
    OPTION_FORMAT_TABLE_DICT_TESTCASES
)
@pytest.mark.parametrize(
    # Transpose only affects metrics output, but not info output.
    # Transpose is accepted and ignored for all table output formats.
    "transpose_opt", [
        None,
        '-x',
        '--transpose',
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
def test_option_format_table_dict(
        out_opt, transpose_opt, out_format, exp_stdout_template):
    """
    Test global options (-o, --output-format) and (-x, --transpose), for all
    table formats, with the 'zhmc console list-firmware' command which displays
    a dict.
    """

    faked_session = setup_faked_hmc()
    client = Client(faked_session)
    console = client.consoles.console

    console.pull_properties('ec-mcl-description')
    ec_mcl = console.properties['ec-mcl-description']
    firmware_list = convert_ec_mcl_description(ec_mcl)

    # The dicts display sorts the output by the first column
    sorted_firmware_list = sorted(
        firmware_list, key=lambda row: row[list(row.keys())[0]])
    f1 = sorted_firmware_list[0]
    f2 = sorted_firmware_list[1]

    exp_stdout = exp_stdout_template.format(f1=f1, f2=f2)

    args = [out_opt, out_format]
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.extend(['console', 'list-firmware'])

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(0, rc, stdout, stderr)
    assert stdout == exp_stdout, (
        "Unexpected stdout:\n"
        f"Actual: {stdout!r}\n"
        f"Expected: {exp_stdout!r}")
    assert stderr == ""


JSON_PROPS_STDOUT_TEMPLATE = \
    '{{' \
    '"api-major-version": {v[amaj]},' \
    '"api-minor-version": {v[amin]},' \
    '"hmc-name": "{v[hnam]}",' \
    '"hmc-version": "{v[hver]}"' \
    '}}'

JSON_PROPS_CONFLICT_PATTERNS = [
    r"Error: Transposing output tables .* conflicts with non-table "
    r"output format .* json",
]


@pytest.mark.parametrize(
    "transpose_opt, exp_rc, exp_stdout_template, exp_stderr_patterns", [
        (None, 0, JSON_PROPS_STDOUT_TEMPLATE, None),
        ('-x', 1, None, JSON_PROPS_CONFLICT_PATTERNS),
        ('--transpose', 1, None, JSON_PROPS_CONFLICT_PATTERNS),
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('hmc-name', '2.14.0', '2.20'),
    ]
)
def test_option_format_json_props(
        hmc_name, hmc_version, api_version, out_opt, transpose_opt,
        exp_rc, exp_stdout_template, exp_stderr_patterns):
    """
    Test global options (-o, --output-format) and (-x, --transpose), for the
    'json' format, with the 'zhmc info' command which displays properties.
    """

    faked_session = FakedSession(
        'fake-host', hmc_name, hmc_version, api_version,
        userid='fake-user')

    args = [out_opt, 'json']
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.append('info')

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(exp_rc, rc, stdout, stderr)

    if exp_stdout_template:
        api_version_parts = [int(vp) for vp in api_version.split('.')]
        exp_values = {
            'hnam': hmc_name,
            'hver': hmc_version,
            'amaj': api_version_parts[0],
            'amin': api_version_parts[1],
        }
        exp_stdout = exp_stdout_template.format(v=exp_values)
        exp_stdout_dict = json.loads(exp_stdout)
        stdout_dict = json.loads(stdout)
        assert stdout_dict == exp_stdout_dict
    else:
        assert stdout == ""

    if exp_stderr_patterns:
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
    else:
        assert stderr == ""


JSON_RES_STDOUT_TEMPLATE = \
    '[' \
    '{{' \
    '"name": "{c1[name]}",' \
    '"status": "{c1[status]}",' \
    '"dpm-enabled": {c1[dpm-enabled]},' \
    '"se-version": "{c1[se-version]}",' \
    '"machine-type": "{c1[machine-type]}",' \
    '"machine-model": "{c1[machine-model]}",' \
    '"machine-serial-number": "{c1[machine-serial-number]}",' \
    '"description": "{c1[description]}"' \
    '}},' \
    '{{' \
    '"name": "{c2[name]}",' \
    '"status": "{c2[status]}",' \
    '"dpm-enabled": {c2[dpm-enabled]},' \
    '"se-version": "{c2[se-version]}",' \
    '"machine-type": "{c2[machine-type]}",' \
    '"machine-model": "{c2[machine-model]}",' \
    '"machine-serial-number": "{c2[machine-serial-number]}",' \
    '"description": "{c2[description]}"' \
    '}}' \
    ']'

JSON_RES_CONFLICT_PATTERNS = [
    r"Error: Transposing output tables .* conflicts with non-table "
    r"output format .* json",
]


@pytest.mark.parametrize(
    "transpose_opt, exp_rc, exp_stdout_template, exp_stderr_patterns", [
        (None, 0, JSON_RES_STDOUT_TEMPLATE, None),
        ('-x', 1, None, JSON_RES_CONFLICT_PATTERNS),
        ('--transpose', 1, None, JSON_RES_CONFLICT_PATTERNS),
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
def test_option_format_json_res(
        out_opt, transpose_opt, exp_rc, exp_stdout_template,
        exp_stderr_patterns):
    """
    Test global options (-o, --output-format) and (-x, --transpose), for the
    'json' format, with the 'zhmc cpc list' command which displays a list of
    resources.
    """

    faked_session = setup_faked_hmc()
    client = Client(faked_session)
    cpcs = client.cpcs.list(full_properties=True)
    cpc1 = cpcs[0]
    cpc2 = cpcs[1]

    args = [out_opt, 'json']
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.extend(['cpc', 'list'])

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(exp_rc, rc, stdout, stderr)

    if exp_stdout_template:
        c1 = dict(cpc1.properties)
        c1['dpm-enabled'] = 'true' if c1['dpm-enabled'] else 'false'
        c2 = dict(cpc2.properties)
        c2['dpm-enabled'] = 'true' if c2['dpm-enabled'] else 'false'
        exp_stdout = exp_stdout_template.format(c1=c1, c2=c2)
        exp_stdout_dict = json.loads(exp_stdout)
        stdout_dict = json.loads(stdout)
        assert stdout_dict == exp_stdout_dict, (
            "Unexpected stdout (as dict):\n"
            f"Actual: {stdout_dict!r}\n"
            f"Expected: {exp_stdout_dict!r}")
    else:
        assert stdout == ""

    if exp_stderr_patterns:
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
    else:
        assert stderr == ""


JSON_DICT_STDOUT_TEMPLATE = \
    '[' \
    '{{' \
    '"ec-number": "{f1[ec-number]}",' \
    '"description": "{f1[description]}",' \
    '"retrieved": "{f1[retrieved]}",' \
    '"installable-conc": "{f1[installable-conc]}",' \
    '"activated": "{f1[activated]}",' \
    '"accepted": "{f1[accepted]}",' \
    '"removable-conc": "{f1[removable-conc]}"' \
    '}},' \
    '{{' \
    '"ec-number": "{f2[ec-number]}",' \
    '"description": "{f2[description]}",' \
    '"retrieved": "{f2[retrieved]}",' \
    '"installable-conc": "{f2[installable-conc]}",' \
    '"activated": "{f2[activated]}",' \
    '"accepted": "{f2[accepted]}",' \
    '"removable-conc": "{f2[removable-conc]}"' \
    '}}' \
    ']'

JSON_DICT_CONFLICT_PATTERNS = [
    r"Error: Transposing output tables .* conflicts with non-table "
    r"output format .* json",
]


@pytest.mark.parametrize(
    "transpose_opt, exp_rc, exp_stdout_template, exp_stderr_patterns", [
        (None, 0, JSON_DICT_STDOUT_TEMPLATE, None),
        ('-x', 1, None, JSON_DICT_CONFLICT_PATTERNS),
        ('--transpose', 1, None, JSON_DICT_CONFLICT_PATTERNS),
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
def test_option_format_json_dict(
        out_opt, transpose_opt, exp_rc, exp_stdout_template,
        exp_stderr_patterns):
    """
    Test global options (-o, --output-format) and (-x, --transpose), for the
    'json' format, with the 'zhmc cpc list' command which displays a list of
    resources.
    """

    faked_session = setup_faked_hmc()
    client = Client(faked_session)
    console = client.consoles.console

    console.pull_properties('ec-mcl-description')
    ec_mcl = console.properties['ec-mcl-description']
    firmware_list = convert_ec_mcl_description(ec_mcl)

    # The JSON dicts display does not sort the output
    f1 = firmware_list[0]
    f2 = firmware_list[1]

    args = [out_opt, 'json']
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.extend(['console', 'list-firmware'])

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(exp_rc, rc, stdout, stderr)

    if exp_stdout_template:
        exp_stdout = exp_stdout_template.format(f1=f1, f2=f2)
        exp_stdout_dict = json.loads(exp_stdout)
        stdout_dict = json.loads(stdout)
        assert stdout_dict == exp_stdout_dict, (
            "Unexpected stdout (as dict):\n"
            f"Actual: {stdout_dict!r}\n"
            f"Expected: {exp_stdout_dict!r}")
    else:
        assert stdout == ""

    if exp_stderr_patterns:
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
    else:
        assert stderr == ""


CSV_RES_STDOUT_TEMPLATE = (
    # Note: The quoting must be consistent with how the CSV file is written.
    '"name","status","dpm-enabled","se-version","machine-type",'
    '"machine-model","machine-serial-number","description"\n'
    '"{c1[name]}","{c1[status]}",{c1[dpm-enabled]},"{c1[se-version]}",'
    '"{c1[machine-type]}","{c1[machine-model]}","{c1[machine-serial-number]}",'
    '"{c1[description]}"\n'
    '"{c2[name]}","{c2[status]}",{c2[dpm-enabled]},"{c2[se-version]}",'
    '"{c2[machine-type]}","{c2[machine-model]}","{c2[machine-serial-number]}",'
    '"{c2[description]}"\n'
)

CSV_RES_CONFLICT_PATTERNS = [
    r"Error: Transposing output tables .* conflicts with non-table "
    r"output format .* csv",
]


@pytest.mark.parametrize(
    "transpose_opt, exp_rc, exp_stdout_template, exp_stderr_patterns", [
        (None, 0, CSV_RES_STDOUT_TEMPLATE, None),
        ('-x', 1, None, CSV_RES_CONFLICT_PATTERNS),
        ('--transpose', 1, None, CSV_RES_CONFLICT_PATTERNS),
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
def test_option_format_csv_res(
        out_opt, transpose_opt, exp_rc, exp_stdout_template,
        exp_stderr_patterns):
    """
    Test global options (-o, --output-format) and (-x, --transpose),
    for the 'csv' output format,
    with the 'zhmc cpc list' command which displays a list of resources.
    """

    faked_session = setup_faked_hmc()
    client = Client(faked_session)
    cpcs = client.cpcs.list(full_properties=True)
    cpc1 = cpcs[0]
    cpc2 = cpcs[1]

    args = [out_opt, 'csv']
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.extend(['cpc', 'list'])

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(exp_rc, rc, stdout, stderr)

    if exp_stdout_template:
        exp_stdout = exp_stdout_template.format(
            c1=cpc1.properties, c2=cpc2.properties, q='"')
        assert stdout == exp_stdout, (
            "Unexpected stdout:\n"
            f"Actual: {stdout!r}\n"
            f"Expected: {exp_stdout!r}")
    else:
        assert stdout == ""

    if exp_stderr_patterns:
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
    else:
        assert stderr == ""


CSV_DICT_STDOUT_TEMPLATE = (
    '"ec-number","description","retrieved","installable-conc","activated",'
    '"accepted","removable-conc"\n'
    '"{f1[ec-number]}","{f1[description]}","{f1[retrieved]}",'
    '"{f1[installable-conc]}","{f1[activated]}","{f1[accepted]}",'
    '"{f1[removable-conc]}"\n'
    '"{f2[ec-number]}","{f2[description]}","{f2[retrieved]}",'
    '"{f2[installable-conc]}","{f2[activated]}","{f2[accepted]}",'
    '"{f2[removable-conc]}"\n'
)


CSV_DICT_CONFLICT_PATTERNS = [
    r"Error: Transposing output tables .* conflicts with non-table "
    r"output format .* csv",
]


@pytest.mark.parametrize(
    "transpose_opt, exp_rc, exp_stdout_template, exp_stderr_patterns", [
        (None, 0, CSV_DICT_STDOUT_TEMPLATE, None),
        ('-x', 1, None, CSV_DICT_CONFLICT_PATTERNS),
        ('--transpose', 1, None, CSV_DICT_CONFLICT_PATTERNS),
    ]
)
@pytest.mark.parametrize(
    "out_opt", ['-o', '--output-format']
)
def test_option_format_csv_dict(
        out_opt, transpose_opt, exp_rc, exp_stdout_template,
        exp_stderr_patterns):
    """
    Test global options (-o, --output-format) and (-x, --transpose),
    for the 'csv' output format,
    with the 'zhmc cpc list' command which displays a list of resources.
    """

    faked_session = setup_faked_hmc()
    client = Client(faked_session)
    console = client.consoles.console

    console.pull_properties('ec-mcl-description')
    ec_mcl = console.properties['ec-mcl-description']
    firmware_list = convert_ec_mcl_description(ec_mcl)

    # The dicts display sorts the output by the first column
    sorted_firmware_list = sorted(
        firmware_list, key=lambda row: row[list(row.keys())[0]])
    f1 = sorted_firmware_list[0]
    f2 = sorted_firmware_list[1]

    args = [out_opt, 'csv']
    if transpose_opt is not None:
        args.append(transpose_opt)
    args.extend(['console', 'list-firmware'])

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        args, faked_session=faked_session)

    assert_rc(exp_rc, rc, stdout, stderr)

    if exp_stdout_template:
        exp_stdout = exp_stdout_template.format(f1=f1, f2=f2, q='"')
        assert stdout == exp_stdout, (
            "Unexpected stdout:\n"
            f"Actual: {stdout!r}\n"
            f"Expected: {exp_stdout!r}")
    else:
        assert stdout == ""

    if exp_stderr_patterns:
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
    else:
        assert stderr == ""


LOG_API_DEBUG_PATTERNS = [
    r"DEBUG zhmcclient.api: .* Client.query_api_version\(\), "
    r"args: \(.*\), kwargs: \{.*\}",
    r"DEBUG zhmcclient.api: .* Client.query_api_version\(\), "
    r"result: \{.*\}",
]


@pytest.mark.parametrize(
    "log_value, exp_rc, exp_stderr_patterns", [
        ('api=error', 0, []),
        ('api=warning', 0, []),
        ('api=info', 0, []),
        ('api=debug', 0, LOG_API_DEBUG_PATTERNS),
        ('api=debug,hmc=error', 0, LOG_API_DEBUG_PATTERNS),
        (',api=debug,hmc=error', 0, LOG_API_DEBUG_PATTERNS),
        ('api=debug,,hmc=error', 0, LOG_API_DEBUG_PATTERNS),
        ('api=debug,hmc=error,', 0, LOG_API_DEBUG_PATTERNS),
        (',,api=debug,,', 0, LOG_API_DEBUG_PATTERNS),
        (',,', 0, []),
        ('api:debug', 1, ["Error: Missing '=' .*"]),
        ('api=debugx', 1, ["Error: Invalid log level .*"]),
        ('apix=debug', 1, ["Error: Invalid log component .*"]),
    ]
)
@pytest.mark.parametrize(
    "log_opt", ['--log']
)
@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('hmc-name', '2.14.0', '10.2'),
    ]
)
def test_option_log(
        hmc_name, hmc_version, api_version, log_opt, log_value,
        exp_rc, exp_stderr_patterns):
    """
    Test 'zhmc info' with global option --log
    """

    faked_session = FakedSession(
        'fake-host', hmc_name, hmc_version, api_version,
        userid='fake-user')

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_inline(
        [log_opt, log_value, 'info'],
        faked_session=faked_session)

    assert_rc(exp_rc, rc, stdout, stderr)
    assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')


@pytest.mark.parametrize(
    "logdest_value, exp_rc, exp_stderr_patterns", [
        (None, 0, LOG_API_DEBUG_PATTERNS),
        ('stderr', 0, LOG_API_DEBUG_PATTERNS),
        ('syslog', 0, []),
        ('none', 0, []),
        (TEST_LOGFILE, 0, []),
    ]
)
@pytest.mark.parametrize(
    "logdest_opt", ['--log-dest']
)
@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('fake-hmc', '2.14.0', '10.2'),
    ]
)
def test_option_logdest(
        hmc_name, hmc_version, api_version, logdest_opt,
        logdest_value, exp_rc, exp_stderr_patterns):
    """
    Test 'zhmc info' with global option --log-dest (and --log)
    """

    faked_session = FakedSession(
        'fake-host', hmc_name, hmc_version, api_version,
        userid='fake-user')

    args = ['--log', 'api=debug']
    logger_name = 'zhmcclient.api'  # corresponds to --log option
    if logdest_value is not None:
        args.append(logdest_opt)
        args.append(logdest_value)
    args.append('info')

    try:

        # Remove a possibly existing log file
        if logdest_value == TEST_LOGFILE:
            if os.path.exists(TEST_LOGFILE):
                os.remove(TEST_LOGFILE)

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_inline(
            args, faked_session=faked_session)

        assert_rc(exp_rc, rc, stdout, stderr)
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')

        # Check system log
        if logdest_value == 'syslog':
            syslog_files = ['/var/log/messages', '/var/log/syslog']
            for syslog_file in syslog_files:
                if os.path.exists(syslog_file):
                    break
            else:
                syslog_file = None
                print("Warning: Cannot check syslog; syslog file not found "
                      "in: {f!r}".format(f=syslog_files))
            syslog_lines = None
            if syslog_file:
                try:
                    syslog_lines = subprocess.check_output(
                        'sudo tail {f} || tail {f}'.format(f=syslog_file),
                        shell=True)  # nosec: B602
                except Exception as exc:  # pylint: disable=broad-except
                    print("Warning: Cannot tail syslog file {f}: {msg}".
                          format(f=syslog_file, msg=exc))
            if syslog_lines:
                syslog_lines = syslog_lines.decode('utf-8').splitlines()
                logger_lines = []
                for line in syslog_lines:
                    if logger_name in line:
                        logger_lines.append(line)
                logger_lines = logger_lines[
                    -len(LOG_API_DEBUG_PATTERNS):]
                exp_patterns = [r'.*' + p for p in LOG_API_DEBUG_PATTERNS]
                assert_patterns(exp_patterns, logger_lines, 'syslog')

        # Check log file
        if logdest_value == TEST_LOGFILE:
            with open(TEST_LOGFILE, encoding='utf-8') as fp:
                log_lines = fp.readlines()
                logger_lines = []
                for line in log_lines:
                    if logger_name in line:
                        logger_lines.append(line)
                logger_lines = logger_lines[
                    -len(LOG_API_DEBUG_PATTERNS):]
                exp_patterns = [r'.*' + p for p in LOG_API_DEBUG_PATTERNS]
                assert_patterns(exp_patterns, logger_lines, 'syslog')

    finally:
        # Clean up a possibly existing log file
        if logdest_value == TEST_LOGFILE:
            if os.path.exists(TEST_LOGFILE):
                try:
                    os.remove(TEST_LOGFILE)
                except OSError:
                    # On Windows with Python 3, PermissionError is raised.
                    # TODO: Find out why and resolve this better.
                    pass
