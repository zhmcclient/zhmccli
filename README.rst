.. Copyright 2016-2019 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

zhmccli - A CLI for the IBM Z HMC, written in pure Python
=========================================================

.. image:: https://img.shields.io/pypi/v/zhmccli.svg
    :target: https://pypi.python.org/pypi/zhmccli/
    :alt: Version on Pypi

.. image:: https://travis-ci.org/zhmcclient/zhmccli.svg?branch=master
    :target: https://travis-ci.org/zhmcclient/zhmccli
    :alt: Travis test status (master)

.. image:: https://ci.appveyor.com/api/projects/status/i022iaeu3dao8j5x/branch/master?svg=true
    :target: https://ci.appveyor.com/project/leopoldjuergen/zhmccli
    :alt: Appveyor test status (master)

.. image:: https://readthedocs.org/projects/zhmccli/badge/?version=latest
    :target: http://zhmccli.readthedocs.io/en/latest/
    :alt: Docs build status (latest)

.. image:: https://img.shields.io/coveralls/zhmcclient/zhmccli.svg
    :target: https://coveralls.io/r/zhmcclient/zhmccli
    :alt: Test coverage (master)

.. image:: https://codeclimate.com/github/zhmcclient/zhmccli/badges/gpa.svg
    :target: https://codeclimate.com/github/zhmcclient/zhmccli
    :alt: Code Climate

.. contents:: Contents:
   :local:

Overview
========

The zhmccli package is a CLI written in pure Python that interacts with the
Hardware Management Console (HMC) of `IBM Z`_ or `LinuxONE`_ machines. The goal
of this package is to provide an easy-to-use command line interface
for operators.

.. _IBM Z: http://www.ibm.com/systems/z/
.. _LinuxONE: http://www.ibm.com/systems/linuxone/

The zhmccli package uses the API provided by the zhmcclient package, which
interacts with the Web Services API of the HMC. It supports management of the
lifecycle and configuration of various platform resources, such as partitions,
CPU, memory, virtual switches, I/O adapters, and more.

Installation
============

The quick way:

.. code-block:: bash

    $ pip install zhmccli

For more details, see the `Installation section`_ in the documentation.

.. _Installation section: http://zhmccli.readthedocs.io/en/stable/intro.html#installation

Quickstart
===========

The following example code lists the machines (CPCs) managed by an HMC:

.. code-block:: bash

    $ hmc_host="<IP address or hostname of the HMC>"
    $ hmc_userid="<userid on that HMC>"
    $ zhmc -h $hmc_host -u $hmc_userid cpc list
    Enter password (for user <hmc_user> at HMC <hmc_host>): .......
    +----------+------------------+
    | name     | status           |
    |----------+------------------|
    | P000S67B | service-required |
    +----------+------------------+

Documentation
=============

The zhmccli documentation is on RTD:

* `Documentation for latest version on Pypi`_
* `Documentation for master branch in Git repo`_

.. _Documentation for latest version on Pypi: http://zhmccli.readthedocs.io/en/stable/
.. _Documentation for master branch in Git repo: http://zhmccli.readthedocs.io/en/latest/

Contributing
============

For information on how to contribute to this project, see the
`Development section`_ in the documentation.

.. _Development section: http://zhmccli.readthedocs.io/en/stable/development.html

License
=======

The zhmccli package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://github.com/zhmcclient/zhmccli/tree/master/LICENSE
