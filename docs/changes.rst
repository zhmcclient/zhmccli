
.. Copyright 2017,2019 IBM Corp. All Rights Reserved.
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


.. ============================================================================
..
.. Do not add change records here directly, but create fragment files instead!
..
.. ============================================================================

.. towncrier start
Version 1.12.3
^^^^^^^^^^^^^^

Released: 2025-04-30

**Bug fixes:**

* Fixed missing package dependencies for development.

* Addressed safety issues up to 2025-04-24.

* Fixed the values for the artificial property "candidate-adapter-port-names"
  in the output of the "zhmc storagegroup show" command. So far, it showed
  only the port name, which was not very helpful. Now, it shows adapter name
  and port name. (`#739 <https://github.com/zhmcclient/zhmccli/issues/739>`_)

* Fixed the handling of the '--port' option that resulted in an error, in
  multiple commands: 'zhmc storagegroup add-ports',
  'zhmc storagegroup remove-ports', 'zhmc vstorageresource update',
  'zhmc storagevolume fulfill-fcp'. (`#747 <https://github.com/zhmcclient/zhmccli/issues/747>`_)

**Enhancements:**

* Dev: Started using the trusted publisher concept of Pypi in order to avoid
  dealing with Pypi access tokens. (`#712 <https://github.com/zhmcclient/zhmccli/issues/712>`_)

* Added support for specifying the adapter port as port index as an additional
  alternative to the port name, in the '--port' option of multiple commands:
  'zhmc storagegroup add-ports', 'zhmc storagegroup remove-ports',
  'zhmc vstorageresource update', 'zhmc storagevolume fulfill-fcp'. (`#747 <https://github.com/zhmcclient/zhmccli/issues/747>`_)


Version 1.12.2
^^^^^^^^^^^^^^

Released: 2025-01-12

**Bug fixes:**

* Addressed safety issues up to 2025-01-12.


Version 1.12.1
^^^^^^^^^^^^^^

Released: 2024-12-12

**Bug fixes:**

* Addressed safety issues up to 2024-11-30.

* Fixed the AttributeError exception that occurred when ending an interactive
  LPAR console session. (`#676 <https://github.com/zhmcclient/zhmccli/issues/676>`_)

**Cleanup:**

* Accommodated rollout of Ubuntu 24.04 on GitHub Actions by using ubuntu-22.04
  as the OS image for Python 3.8 based test runs.


Version 1.12.0
^^^^^^^^^^^^^^

Released: 2024-10-10

**Incompatible changes:**

* Dev: Changed 'make install' to install the package in non-editable mode.
  Support for editable mode has been deprecated by pip.

**Bug fixes:**

* Addressed safety issues up to 2024-08-18.

* Dev: Fixed step that creates the release start tag when starting a new version.

* Dev: Fixed new issue 'too-many-positional-arguments' reported by Pylint 3.3.0.

* Test: Upgraded GitHub actions plugin versions to warnings about using deprecated
  node.js version 16.

* Fixed incorrect checks in 'make release_publish' and 'make start_tag'.

* Dev: In the make commands to create/update AUTHORS.md, added a reftag to the
  'git shortlog' command to fix the issue that without a terminal (e.g. in GitHub
  Actions), the command did not display any authors.

* Increased minimum versions of PyYAML to 6.0.2 and pyrsistent to 0.20.0 to fix
  install errors with Python 3.13 on Windows. (`#612 <https://github.com/zhmcclient/zhmccli/issues/612>`_)

* Increased minimum version of zhmcclient to 1.17.0 (and dependent packages
  accordingly) to pick up fixes and functionality. (`#623 <https://github.com/zhmcclient/zhmccli/issues/623>`_)

* Increased minimum version of zhmcclient to 1.18.0 (and dependent packages
  accordingly) to pick up fixes. (`#659 <https://github.com/zhmcclient/zhmccli/issues/659>`_)

* Fixed incorrect check for start branch in 'make start_tag'. (`#662 <https://github.com/zhmcclient/zhmccli/issues/662>`_)

* Test: Fixed the issue that coveralls was not found in the test workflow on MacOS
  with Python 3.9-3.11, by running it without login shell. Added Python 3.11 on
  MacOS to the normal tests. (`#1665 <https://github.com/zhmcclient/zhmccli/issues/1665>`_)

**Enhancements:**

* Added support for and tests on Python 3.13.0-rc.1. (`#612 <https://github.com/zhmcclient/zhmccli/issues/612>`_)

* Dev: Migrated from setup.py to pyproject.toml with setuptools as build backend.
  This provides for automatic determination of the package version without
  having to edit a version file. (`#617 <https://github.com/zhmcclient/zhmccli/issues/617>`_)

* Test: Added support for running the 'ruff' checker via "make ruff" and added
  that to the test workflow. (`#618 <https://github.com/zhmcclient/zhmccli/issues/618>`_)

* Test: Added support for running the 'bandit' checker with a new make target
  'bandit', and added that to the GitHub Actions test workflow. Adjusted
  the code in order to pass the bandit check. (`#619 <https://github.com/zhmcclient/zhmccli/issues/619>`_)

* Test: Added tests for Python 3.13 (final version). (`#620 <https://github.com/zhmcclient/zhmccli/issues/620>`_)

* Added support for building a local docker image. (`#627 <https://github.com/zhmcclient/zhmccli/issues/627>`_)

* Dev: Migrated to using towncrier for managing the change log. (`#632 <https://github.com/zhmcclient/zhmccli/issues/632>`_)

* Dev: Encapsulated the releasing of a version to PyPI into new 'release_branch'
  and 'release_publish' make targets. See the development documentation for
  details. (`#645 <https://github.com/zhmcclient/zhmccli/issues/645>`_)

* Dev: Encapsulated the starting of a new version into new 'start_branch' and
  'start_tag' make targets. See the development documentation for details. (`#645 <https://github.com/zhmcclient/zhmccli/issues/645>`_)

**Cleanup:**

* Fixed new issues reported by new flake8 7.0.0.

* Dev: Relaxed the conditions when safety issues are tolerated:
  Issues in development dependencies are now tolerated in normal and scheduled
  test workflow runs (but not in local make runs and release test workflow runs).
  Issues in installation dependencies are now tolerated in normal test workflow
  runs (but not in local make runs and scheduled/release test workflow runs).

* Dev: Added to the release instructions to roll back fixes for safety issues
  into any maintained stable branches.

* Dev: Added to the release instructions to check and fix dependabot issues,
  and to roll back any fixes into any maintained stable branches.

* Consolidated the names and emails of the authors shown in AUTHORS.md.

* Dev: Dropped the 'make upload' target, because the release to PyPI has
  been migrated to using a publish workflow. (`#645 <https://github.com/zhmcclient/zhmccli/issues/645>`_)


Version 1.11.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.10.1.

Released: 2024-05-18

**Incompatible changes:**

* cpc command dpm-export now adds additional meta information to the export
  data (can be suppressed using --exclude-meta-fields). Export configuration
  files created with this version of zhmc can only be imported using this
  or any newer version of zhmc, too!

* cpc command dpm-import now honours the configuration file content regarding
  the preserve-uris, preserve-wwpns, and adapter-mapping information. That
  information was previously ignored, and always overwritten by zhmc before
  import.

**Bug fixes:**

* Fixed safety issues up to 2024-05-17.

* In the Github Actions test workflow for Python 3.5, 3.6 and 3.7, changed
  macos-latest back to macos-12 because macos-latest got upgraded from macOS 12
  to macOS 14 which no longer supports these Python versions.

* Fixed an error in the 'cpc autostart add' command.

* Dev: Fixed new issue 'possibly-used-before-assignment' in Pylint 3.2.0.

* Docs: Fixed formatting of badges on README page by converting it to
  Markdown. (issue #604)

**Enhancements:**

* Test: Added the option 'ignore-unpinned-requirements: False' to both
  safety policy files because for safety 3.0, the default is to ignore
  unpinned requirements (in requirements.txt).
  Increased safety minimum version to 3.0 because the new option is not
  tolerated by safety 2.x. Safety now runs only on Python >=3.7 because
  that is what safety 3.0 requires.

* Changed safety run for install dependencies to use the exact minimum versions
  of the dependent packages, by moving them into a separate
  minimum-constraints-install.txt file that is included by the existing
  minimum-constraints.txt file.

* The safety run for all dependencies now must succeed when the test workflow
  is run for a release (i.e. branch name 'release\_...').

* Improved performance of 'list' commands by pulling only the properties
  needed for the output, instead of all of them. This reduced the time to list
  CPCs from over 20 seconds to under 1 second on a test system.

* Improved performance of the 'partition list' command on newer HMCs, by using
  the 'additional-properties' query parameter introduced in HMC version 2.16.0.
  This improved the time for listing partitions on a test system with many
  partitions from about 20 seconds to below 3 seconds.

* cpc command dpm-export now prints a summary of the exported configuration
  data.

* cpc command dpm-import now prints summary information regarding the
  preserve-uris, preserve-wwpns, and adapter-mapping fields. It also prints
  a summary of the concrete configuration data that gets passed to the HMC
  for import prior asking for confirmation.


Version 1.10.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.9.3.

Released: 2024-02-13

**Incompatible changes:**

* Dropped support for Python 2.7 and 3.5. These Python versions went out
  of support by the PSF in 2020. If you still use these Python versions
  today, you should seriously consider upgrading to a supported Python
  version.
  As far as the zhmccli package goes, you can still use versions up to
  1.9.x on Python 2.7 and 3.5.

**Bug fixes:**

* Addressed safety issues up to 2024-02-11.

* Increased minimum version of 'prompt-toolkit' package to 3.0.13.

* Fixed missing 'CPC' argument in "zhmc cpc upgrade" command. (issue #487).

* Fixed that lpar ''--defined-capacity' option takes boolean argument.
  (issue #534)

* Docs: Increased minimum Sphinx versions to 7.1.0 on Python 3.8 and to 7.2.0 on
  Python >=3.9 and adjusted dependent package versions in order to fix a version
  incompatibility between sphinxcontrib-applehelp and Sphinx.
  Disabled Sphinx runs on Python <=3.7 in order to no longer having to deal
  with older Sphinx versions. (issue #547)

* Fixed KeyError in "zhmc passwordrule characterrule list" command.
  (issue #552)

* Fixed that the "zhmc user create --like ..." command passed the LDAP and MFA
  related properties from the like user to the new user even for non-LDAP
  and non-MFA users, which was rejected by the HMC. Fixed by omitting LDAP
  related properties for non-LDAP users and MFA-related properties for non-MFA
  users. In addition, omitted 'min-pw-change-time' for non-local users.
  (issue #557)

* Fixed the call to pipdeptree in the test workflow to use 'python -m'
  because otherwise it does not show the correct packages of the virtual env.
  (issue #539)

**Enhancements:**

* Added support for Python 3.12. Had to increase the minimum versions of
  setuptools to 66.1.0 and pip to 23.1.2 in order to address removal of the
  long deprecated pkgutils.ImpImporter in Python 3.12, as well as the
  minimum version of click-spinner to 0.1.10, as well as several
  packages used only for development. (issue #497)

* Help: The options in the help for partition, lpar, and user create/update
  commands have been grouped to be more easily identifiable. This required
  adding the "click-option-group" Python package to the dependencies.

* Increased minimum zhmcclient version to 1.13.4 to pick up fixes and
  functionality. (issues #510, #528)

* Tests: Added an environment variable TESTLOG to enable logging for end2end
  tests. (issue #414)

* Added command group 'resetprofile' for operations on reset activation
  profiles in classic mode CPCs.

* Added command group 'imageprofile' for operations on image activation
  profiles in classic mode CPCs.

* Added command group 'loadprofile' for operations on load activation
  profiles in classic mode CPCs.

* Added most of the remaining missing options to the "zhmc lpar update" command.

* Fixed an error in the "zhmc lpar update" command when updating the
  zAware and SSC master passwords.

* Added support for retrievel of firmware from an FTP server to the
  'cpc/console upgrade' commands. (issue #518)

* Added support for the remaining zAware and SSC related properties for the
  commands:

  - lpar update
  - imageprofile create
  - imageprofile update

* Added support for the 'fenced-book-list' properts in the 'resetprofile
  create' command.

* Test: Added Python 3.8 with latest package levels to normal tests because
  that is now the minimum version to run Sphinx. (related to issue #547)

* Added support for Lpar start command (issue #500)

* Added support for user patterns with a new 'zhmc userpattern' command group.
  (issue #550)

* Added support for installation of single firmware updates on the SE with a
  new 'zhmc cpc install-firmware' command. (issue #528)

* Added support for deletion of uninstalled firmware updates from the SE with a
  new 'zhmc cpc delete-uninstalled-firmware' command. (issue #528)

* Added support for listing firmware levels of SE/CPC and HMC with new
  commands 'zhmc cpc list-firmware' and 'zzhmc console list-firmware'.
  (issue #564)

* Added support for showing/adding/removing crypto adapters and domains on
  partitions with new commands 'zhmc partition show/add/remove-crypto'.
  (issue #105)

* Added support for showing crypto configuration of partitions using a specific
  crypto adapter with a new command 'zhmc adapter show-crypto'.
  (issue #105)

* Added support for zeroizing crypto domains with a new
  command 'zhmc partition zeroize-crypto'. (issue #502)

* Fail partition/lpar list commands if the specified CPC does not exist.
  (issue #514)

* Added support for a new make target 'authors' that generates an AUTHORS.md
  file from the git commit history. Added the invocation of 'make authors' to
  the description of how to release a version in the development
  documentation. (issue #541)

**Cleanup:**

* Fixed copyright statements (issue #542)

* Increased versions of GitHub Actions plugins to increase node.js runtime
  to version 20.


Version 1.9.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.8.1.

Released: 2023-10-13

**Incompatible changes:**

* Installation of this package using "setup.py" is no longer supported.
  Use "pip" instead.

**Bug fixes:**

* Fixed TypeError in ldap show/delete/update commands. (issue #460)

* Fixed safety issues from 2023-08-27.

* Test: Circumvented a pip-check-reqs issue by excluding its version 2.5.0.

**Enhancements:**

* Test: Changed end2end tests to contribute coverage results to same data as
  unit/function tests.

* Added the 'state' and 'physical-channel-status' properties to the output
  of the "adapter list" command. Removed the redundant 'adapter-family' property
  from the output. (issue #472)

* Added 'short-name' and 'reserved-resources' (only when usage options are used)
  columns to the output of the 'partition list' command. (issue #468)

* Added 'description' column to the output of all list commands. (issue #468)

* Added support for missing property options for the 'partition create'
  and 'partition update' commands. These commands now support options for
  all properties of z16 HMCs.

* Added logging to a file as an additional log destination for the --log-dest
  option (issue #415)

**Cleanup:**

* Dev: Increased minimum versins of some development packages and fixed
  Makefile dependencies.


Version 1.8.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.7.1.

Released: 2023-08-04

**Bug fixes:**

* Fixed automatic logoff: If a command (other than 'session create') creates a
  new HMC session, the session is automatically deleted again at the end of the
  command. (issue #421)

* Circumvented the removal of Python 2.7 from the Github Actions plugin
  setup-python, by using the Docker container python:2.7.18-buster instead.

* Addressed safety issues from 6+7/2023, by increasing 'requests' to 2.31.0
  on Python >=3.7, and by increasing other packages only needed for development.

* Increased minimum zhmcclient version to 1.9.1 to pick up fixes for
  'console restart' and PyYAML install issue.

* Excluded certain PyYAML package versions to address the package install error
  that happens due to the recently released Cython 3 when PyYAML has to build
  its wheel archive during install.

**Enhancements:**

* Improved the end2end test cases for session management.

* Increased the minimum version of zhmcclient to 1.8.1 to pick up improvements
  for session management.

* Added a 'zhmc console restart' command which restarts the targeted HMC.
  Options are to force users, and to wait for restart with a timeout.

* Added support for upgrading HMC firmware to the 'zhmc console' command group
  and for upgrading the SE firmware to the 'zhmc cpc' command group with
  a new command 'upgrade'. Increased minimum zhmcclient version to 1.10.0.
  (issue #440)


Version 1.7.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.6.1.

Released: 2023-05-16

**Bug fixes:**

* Changed versions of packages used by zhmc:

  - Increased zhmcclient to 1.8.0 to pick up fixes and functionality
  - Increased jsonschema to 3.0.1, urllib3 to 1.26.5, requests to 2.25.0,
    all for consistency with zhmcclient.

* Test: Fixed test_info.py test that broke with new urllib3 version 2.0.2.

* Fixed RTD docs build issue with OpenSSL by adding RTD config file that
  specifies Ubuntu 22.04 for the OS.

* Fixed the incorrect representation of string values as floating point numbers
  in the table output formats. (issue #391)

* Removed the option '--crypto-number' from the 'zhmc adapter update' command.
  This is not an incompatible change, since it is not possible to change the
  the crypto number of a Crypto Express adapter. (part of issue #108)

**Enhancements:**

* Added 'zhmc unmanaged_cpc' command group for dealing with unmanaged CPCs.

* Added support for changing the crypto type of Crypto Express adapters
  and the type of FICON Express adapters to the 'zhmc adapter update'
  command. (issue #108)

* Added a troubleshooting section to the docs.

* Added a hidden '--pdb' general option for having the zhmc command break right
  before the invocation of the command. This can be used for debugging,
  particularly in end2end tests.

* Added 'zhmc ldap' command group for managing LDAP server definitions.
  (issue #393)

* Added initial support for end2end tests. For details, see the new
  "Running end2end tests" section in the documentation.
  A first end2end testcase for the 'zhmc session' command has been added.

* Added new commands to assign/unassign certificates to/from DPM partitions
  and classic mode LPARs.

* Added new top level command group 'certificate'.

* Added two new commands 'console list-api-features' and 'cpc list-api-features'
  to support the new "API features" concept.


Version 1.6.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.5.1.

Released: 2023-03-27

**Incompatible changes:**

- cpc command dpm-import: the schema used for validating the adapter mapping file
  (issue #362) didn't match the content in the corresponding documentation.
  Both, documentation and schema were modified following the naming used
  in the "Import DPM configuration" WSAPI endpoint specification.

- cpc command dpm-export: the default behavior when exporting the DPM
  configuration has been changed to only include those adapters that are
  referenced by other elements of the exported configuration data.
  A new flag --include-unused-adapters was added to dpm-export to
  allow for running an export that includes all adapters of the CPC. (#369)

**Bug fixes:**

* Added tox and virtualenv to dependencies.

* Fixed TypeError exception in Click package when using 'cpc dpm-export' or
  'cpc dpm-import' commands. (issue #370)

* Increased minimum version of zhmcclient to 1.7.0 to pick up required fixes.

**Enhancements:**

* Added missing environments to weekly full tests (Python 2.7,3.5,3.6 on Windows
  and MacOS).

* Added some critical environments to normal PR tests (Python 3.6/min, 3.10/min).

* Changed to using the 'build' package for building the distribution archives
  instead of 'setup.py' commands, following the recommendation of the Python
  packaging community
  (see https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html).

* Addressed issues reported by safety by increasing package versions. (#349)

* Changed JSON output for dpm-export to be sorted and properly indented (#363)

* Added support for Python 3.11.

**Cleanup:**

* Increased minimum versions of pip, setuptools, wheel to more recent versions.

Version 1.5.0
^^^^^^^^^^^^^

Released: 2023-03-06

**Bug fixes:**

* Test: Fixed install error of Python 2.7, 3.5, 3.6 on Ubuntu in GitHub Actions.

* Pylint: Migrated config file to pylint 2.14; No longer installing Pylint on
  Python 2.7; Enabled running Pylint again on Python 3.5, Increased minimum
  version of Pylint to 2.10.0 on Python 3.5 and higher.

* Fixed that cpc dpm-import operation does not show output details if response
  code is 200. (issue #342)

**Enhancements:**

* Simplified release process by adding a new GitHub Actions workflow publish.yml
  to build and publish to PyPI.

* Docs: Added a section "Setting up firewalls or proxies" that provides
  information which ports to open for accessing the HMC. (issue #335)

* Increased zhmcclient to version 1.6.0 to pick up new functionality.

**Cleanup:**

* Addressed issues in test workflow reported by Github Actions. (issue #336)

* Unpinned Click from <8 for Python >=3.6 (issue #331)


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

* Fixed that --vlan-id could not be omitted in 'zhmc nic create' and
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

* Increased minimum version of zhmcclient to 1.2.1 to pick up several fixes,
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
  accommodate the immutable properties of resource objects.

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
