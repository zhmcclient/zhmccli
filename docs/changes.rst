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


Version 1.5.0.dev1
^^^^^^^^^^^^^^^^^^

This version contains all fixes up to version 1.4.x.

Released: not yet

**Incompatible changes:**

**Deprecations:**

**Bug fixes:**

* Test: Fixed install error of Python 2.7, 3,5, 3,6 on Ubuntu in GitHub Actions.

**Enhancements:**

**Cleanup:**

**Known issues:**

* See `list of open issues`_.

.. _`list of open issues`: https://github.com/zhmcclient/zhmccli/issues


Version 1.4.0
^^^^^^^^^^^^^

Released: 2022-10-25

**Enhancements:**

* Added a new command 'zhmc adapter list-nics' for listing the NICs backed
  by a network adapter. (issue #110)

* Added commands 'lpar reset-clear' and 'lpar reset-normal'. (issue #111)

* Increased zhmcclient to version 1.5.0 to pick up needed functionality.


Version 1.3.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.2.3.

Released: 2022-10-23

**Bug fixes:**

* Fixed that --vlan-id could not be ommitted in 'zhmc nic create' and
  'zhmc nic update'. (issue #291)

* Added a '--vlan-type' option to 'zhmc nic create' and 'zhmc nic update' to
  set the VLAN type. (issue #292)

* Fixed a flake8 AttributeError when using importlib-metadata 5.0.0 on
  Python >=3.7, by pinning importlib-metadata to <5.0.0 on these Python
  versions.

* Fixed that 'user create' passed the 'mfa-types' and
  'multi-factor-authentication-required' properties to the HMC even when no
  MFA-related options were specified. This caused rejection of the command on
  HMC versions 2.14.0 and older. (issue #286)

* Fixed that the --boot-iso option of the 'partition update' command took a
  TEXT argument (which was not used). Changed that to a flag option.
  (issue #287)

* Fixed a TypeError raised by 'zhmc vstorageresource list' when a
  candidate adapter had not yet been discovered. (part of issue #307)

**Enhancements:**

* Help messages now use the actual terminal width up to 160 characters, and
  require a minimum terminal width of 80. The automatic detection of the
  terminal width can be overridden by setting the env var ZHMCCLI_TERMWIDTH
  to the desired terminal width.

* Added support for specifying the 'acceptable-status' property in the
  zhmc commands 'partition create' and 'partition update' via a new
  --acceptable-status option. Multiple status values can be specified as a
  comma-separated list. (issue #285)

* Extended the --acceptable-status option of the zhmc commands 'cpc update'
  and 'lpar update' to support multiple status values as a comma-separated
  list. (issue #285)

* Added artificial properties to all 'show' commands that show the name of
  resources referenced via an URI. (issue #307)

* Added artificial properties to the 'zhmc nic show' command for the backing
  adapter and port if the NIC is backed by a vswitch (i.e. for OSA,
  Hipersockets). (issue #307)


Version 1.2.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.1.1.

Released: 2022-04-02

**Bug fixes:**

* Fixed that the "lpar scsi-load" and "lpar scsi-dump" commands defined their
  --disk-partition-id option value incorrectly as a string, when it should have
  been an integer. (issue #270)

* Fixed that "lpar list --names-only" had an empty "cpc" column. (issue #269)

* Increaed minimum vbersion of zhmcclient to 1.2.1 to pick up several fixes,
  including the fix for 'lpar scsi-dump' failing due to missing 'secure_boot'
  parameter (issue #280)

**Enhancements:**

* Properties in JSON output are now always sorted by property name. (issue #267)

* Added support for the "console" command group, with the following commands:

  - get-audit-log     - Get the audit log of the targeted HMC.
  - get-security-log  - Get the security log of the targeted HMC.
  - show              - Show properties of the console of the targeted HMC.

  Issue #277


Version 1.1.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.0.3.

Released: 2021-12-23

**Bug fixes:**

* Changed development status of zhmccli on Pypi from 4 (Beta) to
  5 (Production/Stable). (issue #221)

* Fixed new issues reported by Pylint 2.10.

* Disabled new Pylint issue 'consider-using-f-string', since f-strings were
  introduced only in Python 3.6.

* Fixed install error of wrapt 1.13.0 on Python 2.7 on Windows due to lack of
  MS Visual C++ 9.0 on GitHub Actions, by pinning it to <1.13.

* Fixed confusing CR in Aborted message when breaking a prompt.

* Fixed an error in the 'partition dump' command when --operation-timeout
  was specified, and in 'storagegroup delete' when the email options were used.
  (issue #250)

**Enhancements:**

* Added support for managing the auto-start list of a CPC (in DPM mode) via a
  new command group 'cpc autostart'. (issue #33)

* Improved error handling so that exceptions raised by zhmcclient now always
  result in displaying a proper error message instead of a Python traceback.

* Added support for managing HMC users, user roles, and password rules
  via new command groups 'user', 'userrole', 'passwordrule', and
  'passwordrule characterrule'. (part of issue #96)

* Added support for exporting and importing a DPM configuration from / to a
  CPC via new 'dpm-export' and 'dpm-import' commands of the 'cpc' command
  group. (issue #243)

* Increased minimum version of zhmcclient to 1.1.0, and added the jsonschema,
  PyYAML and yamllloader packages as new dependencies, as part of issue #243.

* Support for Python 3.10: Added Python 3.10 in GitHub Actions tests, and in
  package metadata.

* Added support for a '--like' option when creating users. This will use
  certain properties of the like user as defaults for the new user.

**Cleanup:**

* Removed import of the pyreadline package on Windows for enabling history in
  interactive mode, and import of the built-in readline module since it no
  longer seems to be needed and interactive mode history is available without
  them.

* Removed building of the Windows binary install program, since that is no
  longer supported by pip/setuptools. It was not used in the package anyway.


Version 1.0.0
^^^^^^^^^^^^^

Released: 2021-08-18

**Incompatible changes:**

* Dropped support for Python 3.4. Python 3.4 has had its last release as 3.4.10
  on March 18, 2019 and has officially reached its end of life as of that date.
  Current Linux distributions no longer support Python 3.4. (issue #185)

* Changed default for option '--usage' of 'storagevolume update' command to
  not be changed. Prior default was to set usage to 'data', which required
  specifying it with the old value if it was supposed not to be changed.
  (part of issue #125)

**Bug fixes:**

* Fixed HTTP errors raised as traceback during various 'list' commands. These
  errors are now shown as proper error messages. (issue #215)

**Enhancements:**

* Increased minimum version of zhmcclient to 1.0.0.

* Added defaults to help text of command options with value, where missing.
  (issue #125)

* Added a '--secure-boot' option to the 'lpar scsi-dump' and 'partition update'
  commands. It had already been supported by the 'lpar scsi-load' command.
  (issue #206)

* Added support for setting some properties of lpar, partition and nic resources
  to null when specifying an empty string as the option value in create and
  update commands. The option help text has been updated accordingly. (issue #2)

* Clarified in help text of '--ssc-dns-servers' option of the 'partition
  create' and 'partition update' commands that multiple DNS servers are
  specified using a comma-separated list. (issue #216)


Version 0.22.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 0.21.2.

Released: 2021-07-02

**Incompatible changes:**

* The zhmc command now verifies HMC server certificates by default, using the
  CA certificates in the 'certifi' Python package. This verification will reject
  the self-signed certificates the HMC is set up with initially. To deal with
  this, install a CA-verifiable certificate in the HMC and specify the correct
  CA certificates with the new '-c / --ca-certs' option. As a temporary quick
  fix, you can disable the verification with the new '-n / --no-verify'
  option.

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

* The 'nic create' and 'nic update' commands can now specify the backing port
  with the --adapter and --port options for all types of network adapters.
  Previously, they could be used only for OSA and Hipersocket adapters.
  The --virtual-switch option has been deprecated but for compatibility reasons
  is still supported for OSA and Hipersocket adapters. (issues #201, #198)

**Cleanup:**

* Added the missing closing of the image file in the 'partition mount-iso'
  command.

* Disabled a Pylint 'consider-using-with' issue on a Popen in test code that
  was properly terminated again.


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
