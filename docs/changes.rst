.. Copyright 2017-2019 IBM Corp. All Rights Reserved.
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

.. _`Change log`:

Change log
----------

Version 0.19.0
^^^^^^^^^^^^^^

Released: 2019-02-20

**Incompatible changes:**

* The ``lpar deactivate`` command is now non-forceful by default, but
  can be made to behave like previously by specifying the new ``--force``
  option. In force mode, the deactivation operation is permitted when the
  LPAR status is "operating".

**Bug fixes:**

* Aligned the check for when to use pyreadline instead of readline in
  zhmcclient/_helper.py to be consistent with the platform check in
  requirements.txt: By checking for the win32 platform.
  Related to issue #47.

**Enhancements:**

* Fixes and improvements in Makefile.

* Added initial set of function tests for zhmc command.

* Improved the table output of complex properties (arrays or nested objects),
  to use nested tables, where possible. See issue #9.

* Added support for a ``--force`` option in the ``lpar activate``,
  ``lpar deactivate``, and ``lpar load`` commands. It controls whether
  the operation is permitted when the LPAR status is "operating".

  Note that this changes ``lpar deactivate`` to be non-forceful by default
  (force=True was hard coded for deactivate, before this change).

* Added support for a ``--activation-profile-name`` option in LPAR activate.

* Added support for ``cpc set-power'save``, ``cp set-power-capping``
  and ``cpc get-em-data`` operations.

- Improved support for logging to the system log in zhmccli.py:
  Added support for retrying multiple addresses if creating a Python system
  log handler fails. Added localhost:514 as a second choice for Linux and
  OS-X. This fixes the system log issue on the Travis CI with Ubuntu 14.04
  (Issue 35). Added support for system log in CygWin, using /dev/log and
  localhost:514 as the addresses to try.

- Removed the assertions in zhmccli.reset_logger() that verified
  the result of resetting the log handlers. It turned out that recently,
  a log capture logger is present that is caused by the test environment.
  These assertions were probably a bit overkill anyway (Issue #35).


Version 0.18.0
^^^^^^^^^^^^^^

Released: 2017-10-19

This is the base version for this change log. The zhmccli project was
split off of the python-zhmcclient project based upon its released
version 0.17.0. For prior changes, see the change log of the
python-zhmcclient project.

Additional changes:

* Fixed the issue that the readline module is not available in
  standard python on Windows, by using the pyreadline module
  in that case.

* Fixed a flawed setup of setuptools in Python 2.7 on the Travis CI, where
  the metadata directory of setuptools existed twice, by adding a script
  `remove_duplicate_setuptools.py` that removes the moot copy of the metadata
  directory (python-zhmcclient issue #434).

* Added the version of the zhmcclient package to the output of
  ``zhmc --version``.
