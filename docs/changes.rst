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


Version 0.22.0.dev1
^^^^^^^^^^^^^^^^^^^

This version contains all fixes up to version 0.21.x.

Released: not yet

**Incompatible changes:**

* The zhmc command now verifies HMC server certificates by default, using the
  CA certificates in the 'certifi' Python package. This verification will reject
  the self-signed certificates the HMC is set up with initially. To deal with
  this, install a CA-verifiable certificate in the HMC and specify the correct
  CA certificates with the new '-c / --ca-certs' option. As a temporary quick
  fix, you can disable the verification with the new '-n / --no-verify'
  option.

**Deprecations:**

**Bug fixes:**

* Fixed install error on Python>=3.6 caused by click-repl being incompatible
  with click 8.0.

* Fixed the issue that some commands (e.g. cpc list) stopped the spinner too
  early. (issue #142)

* Docs: Added statement that the command group for HBAs can be used only on
  z13 and earlier. (issue #199)

* Docs: Clarified which command groups can only be used in DPM mode or in
  classic mode. (issue #200)

**Enhancements:**

* The zhmc command now supports verification of the HMC server certificate.
  There are two new command line options '-n / --no-verify' and '-c / --ca-certs'
  that control the verification behavior.

* Increased the minimum version of zhmcclient to 0.32.0. Adjusted code to
  accomodate the immutable properties of resource objects.

* Added a '-T' / '--operation-timeout' general option to the following commands,
  that specifies the operation timeout when waiting for completion of
  asynchronous HMC operations. (issue #126)

  - lpar activate
  - lpar deactivate
  - lpar load
  - lpar stop
  - lpar psw_restart
  - lpar scsi-load
  - lpar scsi-dump
  - partition start
  - partition stop
  - partition dump
  - storagegroup discover-fcp

* Partition commands: On HMC 2.14.0 and later, the partition commands now use
  the "List Permitted Partitions" operation instead of going through the CPC,
  which improves the response time, and no longer requires that the user has
  object access permission to the targeted CPC.
  In addition, the CPC on the 'partition list' command is now optional. If not
  specified, permitted partitions on all managed CPCs are listed.
  (issue #192)

* Lpar commands: On HMC 2.14.0 and later, the lpar commands now use the
  "List Permitted Logical Partitions" operation instead of going through the
  CPC, which improves the response time.
  In addition, on HMC API version 3.6 or later (an update to HMC 2.15.0),
  the lpar commands no longer require that the user has object access permission
  to the targeted CPC.
  In addition, the CPC on the 'lpar list' command is now optional. If not
  specified, permitted LPARs on all managed CPCs are listed.
  (issue #192)

**Cleanup:**

* Added the missing closing of the image file in the 'partition mount-iso'
  command.

* Disabled a Pylint 'consider-using-with' issue on a Popen in test code that
  was properly terminated again.

**Known issues:**

* See `list of open issues`_.

.. _`list of open issues`: https://github.com/zhmcclient/zhmccli/issues


Version 0.21.0
^^^^^^^^^^^^^^

Released: 2021-04-06

**Enhancements:**

* Increased minimum version of zhmcclient to 0.30.0.

* Added an option `--secure-boot` to `lpar scsi-load` command (issue #148).

* Added an option `--force` to `lpar scsi-dump` command (issue #148).

* Added support for DPM capacity groups with a new 'capacitygroup' command
  group. (issue #157)


Version 0.20.0
^^^^^^^^^^^^^^

Released: 2021-03-25

**Incompatible changes:**

* In the 'cpc list'  command, removed the output of the 'iml-mode' and
  'is-ensemble-member' properties, because ensemble support has been removed
  from the HMC by now.

**Deprecations:**

* Deprecated several property control options in 'list' commands because the
  corresponding properties are now always shown:

  * ``--type`` option in the 'adapter list' command
  * ``--type`` option in the 'cpc list' command
  * ``--mach`` option in the 'cpc list' command
  * ``--type`` option in the 'lpar list' command
  * ``--type`` option in the 'nic list' command
  * ``--type`` option in the 'partition list' command
  * ``--adapter`` option in the 'vswitch list' command

* Deprecated the options ``--boot-storage-hba/wwpn/lun`` of the
  'partition update' command for booting from an FCP storage volume. Use the
  new ``--boot-storage-volume`` option instead with the "HBA/WWPN/LUN" format.
  (part of issue #130)

**Bug fixes:**

* Fixed a log test failure in zhmccli caused by a change in logging output
  in zhmcclient 0.23.0.

* Fixed an exception "No formatted text" on python 2.7 by pinning 'prompt-toolkit'
  to <2.0 on Python 2.7 (issue #53).

* Mitigated the coveralls HTTP status 422 by pinning coveralls-python to
  <3.0.0.

* Pinned Pygments to <2.4.0 on Python 3.4.

* Pinned readme-renderer to <25.0 on Python 3.4.

* Fixed AttributeError when listing hbas on CPCs that have the storage mgmt
  feature (z14 and later) (issue #113).

* Fixed a KeyError when accessing the email-related options in the
  'storagegroup create' and 'storagegroup update' commands. (issue #129)

* Fixed a KeyError when accessing a no longer existing option in the
  'storagevolume create' command. (issue #137)

* Test: Fixed GitHub Actions test workflow failure by increasing the version of
  the 'readme-renderer' package to a minimum of 0.23.0 which moved the failing
  'cmarkgfm' dependent package to an extra we are not using.

**Enhancements:**

* Increased minimum version of zhmcclient package from 0.19.0 to 0.25.0
  due to new LPAR related functions being used.

* Added a 'dump' command for 'zhmc partition' that works for CPCs with and
  without the DPM storage management feature.

* Added more 'zhmc lpar' commands for logical partitions in CPCs in classic
  mode:

  - zhmc lpar stop
  - zhmc lpar psw-restart
  - zhmc lpar scsi-load
  - zhmc lpar scsi-dump

* Added support for usage related command line options to the `partition list`
  command that include additional fields in the output:
  `--memory-usage` for showing memory allocation to the partitions,
  `--ifl-usage` and `--cp-usage` for showing IFL and CP allocation, weighted
  capacity and actual usage.

* Added more ``lpar load`` command options:

  - Added ``--clear-indicator`` and ``--no-clear-indicator`` flags to
    the ``lpar load`` command. It controls whether the memory should
    be cleared before performing the load operation or not.
  - Added ``--store-status-indicator`` flag to the ``lpar load``
    command. It controls whether the status should be stored before
    performing the load operation or not.

* Added ``os-ipl-token`` option to the ``lpar scsi-dump`` command.

* Added support for the storage management feature, by adding new command
  groups ``storagegroup``, ``storagevolume``, and ``vstorageresource``
  and by adding new storage management related sub-commands to the
  ``partition`` command group (issue #56).

* Added support for Python 3.7.

* Migrated from Travis and Appveyor to GitHub Actions. This required several
  changes in package dependencies for development.

* Dropped the use of the pbr package. The package version is now managed
  in zhmccli/_version.py. (See issue #64)

* Added Python 3.9 to the set of versions that is tested in the CI.

* Test: Ensured that dependent packages are upgraded to their latest versions
  in 'make install' and 'make develop' by invoking Pip with
  '--upgrade-strategy eager'.

* Added some more resource properties to 'list' commands, including name
  properties of the parent resources. All 'list' commands now support these
  options for controlling the properties shown (issue #93):

  - ``--names-only``: Restrict properties shown to only the names of the
    resource and its parents
  - ``--uri``: Add the resource URI to the properties shown
  - ``--all``: Show all properties

* Increased minimum version of Click from 6.6. to 7.0 to get support for
  'hidden' property of options (related to issue #93).

* Added support for setting a storage volume in a storage group as the boot
  volume for a partition, by adding an option ``--boot-storage-volume``
  to the 'partition update' command (issue #130)

* Conflicting boot options specified for the 'partition update' and
  'partition create' command are now detected instead of silently applying
  an undocumented preference scheme. (part of issue #130)

* Changed CPC and LPAR properties that were always hidden in the output of
  the ``cpc show`` and ``lpar show`` commands due to their length or object
  nesting depth, to now be hidden only in certain cases.

  Changed Partition properties in the output of the ``partition show`` command
  that have a significant length or object nesting depth to now be hidden in
  certain cases.

  The hidden properties are now always shown in the JSON output format, and they
  are shown in the table output formats if a newly added ``--all`` option is
  used on these ``show`` commands.

  Hidden CPC properties:
  - auto-start-list
  - available-features-list
  - cpc-power-saving-state
  - ec-mcl-description
  - network1-ipv6-info
  - network2-ipv6-info
  - stp-configuration

  Hidden LPAR properties:
  - program-status-word-information

  Hidden Partition properties:
  - crypto-configuration

  (related to issue #56, also issue #144).

* Increased minimum version of zhmcclient to 0.29.0.

* Docs: Changed documentation theme to Sphinx RTD Theme. (issue #155)

**Cleanup:**

* Changed old-style string formatting to new-style (issue #89).

* Removed build tools no longer needed on GitHub Actions.


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
