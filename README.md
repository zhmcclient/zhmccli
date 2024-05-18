# zhmccli - A CLI for the IBM Z HMC, written in pure Python

[![Version on Pypi](https://img.shields.io/pypi/v/zhmccli.svg)](https://pypi.python.org/pypi/zhmccli/)
[![Test status (master)](https://github.com/zhmcclient/zhmccli/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/zhmcclient/zhmccli/actions/workflows/test.yml?query=branch%3Amaster)
[![Docs status (master)](https://readthedocs.org/projects/zhmccli/badge/?version=latest)](https://readthedocs.org/projects/zhmccli/builds/)
[![Test coverage (master)](https://img.shields.io/coveralls/zhmcclient/zhmccli.svg)](https://coveralls.io/r/zhmcclient/zhmccli)
[![Code Climate](https://codeclimate.com/github/zhmcclient/zhmccli/badges/gpa.svg)](https://codeclimate.com/github/zhmcclient/zhmccli)

# Overview

The zhmccli package is a CLI written in pure Python that interacts with
the Hardware Management Console (HMC) of
[IBM Z](http://www.ibm.com/systems/z/) or
[LinuxONE](http://www.ibm.com/systems/linuxone/) machines. The goal of
this package is to provide an easy-to-use command line interface for
operators.

The zhmccli package uses the API provided by the zhmcclient package,
which interacts with the Web Services API of the HMC. It supports
management of the lifecycle and configuration of various platform
resources, such as partitions, CPU, memory, virtual switches, I/O
adapters, and more.

# Installation

The quick way:

``` bash
$ pip install zhmccli
```

For more details, see the
[Installation section](http://zhmccli.readthedocs.io/en/latest/intro.html#installation)
in the documentation.

# Quickstart

The following example lists the names of the machines (CPCs) managed by
an HMC:

``` bash
$ hmc_host="<IP address or hostname of the HMC>"
$ hmc_userid="<userid on that HMC>"
$ zhmc -h $hmc_host -u $hmc_userid cpc list --names-only
Enter password (for user ... at HMC ...): .......
+----------+
| name     |
|----------+
| P000S67B |
+----------+
```

# Documentation

- [Documentation](http://zhmccli.readthedocs.io/en/latest/)
- [Change log](http://zhmccli.readthedocs.io/en/latest/changes.html)

# Contributing

For information on how to contribute to this project, see the
[Development section](http://zhmccli.readthedocs.io/en/latest/development.html)
in the documentation.

# License

The zhmccli package is licensed under the
[Apache 2.0 License](https://github.com/zhmcclient/zhmccli/tree/master/LICENSE).
