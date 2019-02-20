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

.. _`Introduction`:

Introduction
============


.. _`What this package provides`:

What this package provides
--------------------------

The zhmccli package provides a CLI written in pure Python that interacts with
the Hardware Management Console (HMC) of `IBM Z`_ or `LinuxONE`_ machines. The
goal of this package is to provide an easy-to-use command line interface
for operators.

.. _IBM Z: http://www.ibm.com/systems/z/
.. _LinuxONE: http://www.ibm.com/systems/linuxone/

The zhmccli package uses the API provided by the zhmcclient package, which
interacts with the Web Services API of the HMC. It supports management of the
lifecycle and configuration of various platform resources, such as partitions,
CPU, memory, virtual switches, I/O adapters, and more.


.. _`Supported environments`:

Supported environments
----------------------

The zhmccli package is supported in these environments:

* Operating systems: Linux, Windows, OS-X

* Python versions: 2.7, 3.4, and higher 3.x

* HMC versions: 2.11.1 and higher


.. _`Installation`:

Installation
------------

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _Pypi: http://pypi.python.org/

The easiest way to install the zhmccli package is by using Pip. Pip ensures
that any dependent Python packages also get installed.

Pip will install the packages into your currently active Python environment
(that is, your system Python or a virtual Python environment you have set up).

It is beneficial to set up a `virtual Python environment`_ for your project,
because that leaves your system Python installation unchanged, it does not
require ``sudo`` rights, and last but not least it gives you better control
about the installed packages and their versions.

Installation of latest released version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command installs the latest released version of the zhmccli
package from `Pypi`_ into the currently active Python environment:

.. code-block:: text

    $ pip install zhmccli

Installation of latest development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to install the latest development level of the zhmccli package
instead for some reason, you can install directly from the ``master`` branch
of its Git repository.

The following command installs the latest development level of the zhmccli
package into the currently active Python environment:

.. code-block:: text

    $ pip install git+https://github.com/zhmcclient/zhmccli.git@master

Installation on a system without Internet access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In both cases described above, Internet access is needed to access these
repositories.

If you want to install the zhmccli package on a system that does not have
Internet access, you can do this by first downloading the zhmccli package
and its dependent packages on a download system that does have Internet access,
making these packages available to the target system, and installing on the
target system from the downloaded packages.

For simplicity, the following example uses a shared file system between the
download and target systems (but that is not a requirement; you can also copy
the downloaded files to the target system):

.. code-block:: text

    [download]$ pip download zhmccli

    [download]$ ls zhmccli*
    zhmccli-0.18.0-py2.py3-none-any.whl

    [target]$ ls zhmccli*
    zhmccli-0.18.0-py2.py3-none-any.whl

    [target]$ pip install -f . --no-index zhmccli-0.18.0-py2.py3-none-any.whl

Verification of the installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can verify that the zhmccli package and its dependent packages are
installed correctly by invoking:

.. code-block:: bash

    $ zhmc --version
    0.18.0


.. _`Setting up the HMC`:

Setting up the HMC
------------------

Usage of the zhmccli package requires that the HMC in question is prepared
accordingly:

1. The Web Services API must be enabled on the HMC.

2. The HMC user ID that will be used by the zhmccli package must be authorized
   for the following tasks:

   * Use of the Web Services API.

   When using CPCs in DPM mode:

   * Start (a CPC in DPM mode)
   * Stop (a CPC in DPM mode)
   * New Partition
   * Delete Partition
   * Partition Details
   * Start Partition
   * Stop Partition
   * Dump Partition
   * PSW Restart (a Partition)
   * Create HiperSockets Adapter
   * Delete HiperSockets Adapter
   * Adapter Details
   * Manage Adapters
   * Export WWPNs

   When using CPCs in classic mode (or ensemble mode):

   * Activate (an LPAR)
   * Deactivate (an LPAR)
   * Load (an LPAR)
   * Customize/Delete Activation Profiles
   * CIM Actions ExportSettingsData

3. (Optional) If desired, the HMC user ID that will be used by the zhmccli
   can be restricted to accessing only certain resources managed by the HMC.
   To establish such a restriction, create a custom HMC user role, limit
   resource access for that role accordingly, and associate the HMC user ID
   with that role.

   The zhmccli package needs object-access permission for the following
   resources:

   * CPCs to be accessed

   For CPCs in DPM mode:

   * Partitions to be accessed
   * Adapters to be accessed

   For CPCs in classic mode (or ensemble mode):

   * LPARs to be accessed

For details, see the :term:`HMC Operations Guide`.

A step-by-step description for a similar use case can be found in chapter 11,
section "Enabling the System z HMC to work the Pacemaker STONITH Agent", in the
:term:`KVM for IBM z Systems V1.1.2 System Administration` book.


.. _`Examples`:

Examples
--------

The following example lists the machines (CPCs) managed by an HMC:

.. code-block:: text

    $ hmc_host="<IP address or hostname of the HMC>"
    $ hmc_userid="<userid on that HMC>"
    $ zhmc -h $hmc_host -u $hmc_userid cpc list
    Enter password (for user <hmc_user> at HMC <hmc_host>): .......
    +----------+------------------+
    | name     | status           |
    |----------+------------------|
    | P000S67B | service-required |
    +----------+------------------+


.. _`Versioning`:

Versioning
----------

This documentation applies to version |release| of the zhmccli package. You
can also see that version in the top left corner of this page.

The zhmccli package uses the rules of `Semantic Versioning 2.0.0`_ for its
version.

.. _Semantic Versioning 2.0.0: http://semver.org/spec/v2.0.0.html

The package version can be shown using:

.. code-block:: text

    $ zhmc --version
    0.18.0

This documentation may have been built from a development level of the
package. You can recognize a development version of this package by the
presence of a ".devD" suffix in the version string. Development versions are
pre-versions of the next assumed version that is not yet released. For example,
version 0.18.1.dev25 is development pre-version #25 of the next version to be
released after 0.18.0. Version 0.18.1 is an `assumed` next version, because the
`actually released` next version might as well be 0.19.0 or even 1.0.0.


.. _`Compatibility`:

Compatibility
-------------

In this package, compatibility is always seen from the perspective of the user
of the CLI. Thus, a backwards compatible new version of this package means
that the user can safely upgrade to that new version without encountering
compatibility issues in the CLI that is invoked.

This package uses the rules of `Semantic Versioning 2.0.0`_ for compatibility
between package versions, and for :ref:`deprecations <Deprecations>`.

The public API of this package that is subject to the semantic versioning
rules (and specificically to its compatibility rules) is the API described in
this documentation.

Violations of these compatibility rules are described in section
:ref:`Change log`.


.. _`Deprecations`:

Deprecations
------------

TODO: Verify how deprecation warnings are shown in the CLI.

Deprecated functionality is marked accordingly in this documentation and in the
:ref:`Change log`, and is made visible at runtime by issuing Python warnings of
type :exc:`~py:exceptions.DeprecationWarning` (see :mod:`py:warnings` for
details).

Since Python 2.7, :exc:`~py:exceptions.DeprecationWarning` warnings are
suppressed by default. They can be shown for example in any of these ways:

* by specifying the Python command line option:

  ``-W default``

* by invoking Python with the environment variable:

  ``PYTHONWARNINGS=default``

* by issuing in your Python program:

  .. code-block:: python

      warnings.filterwarnings(action='default', category=DeprecationWarning)

It is recommended that users of this package run their test code with
:exc:`~py:exceptions.DeprecationWarning` warnings being shown, so they become
aware of any use of deprecated functionality.

It is even possible to raise an exception instead of issuing a warning message
upon the use of deprecated functionality, by setting the action to ``'error'``
instead of ``'default'``.


.. _`Reporting issues`:

Reporting issues
----------------

If you encounter any problem with this package, or if you have questions of any
kind related to this package (even when they are not about a problem), please
open an issue in the `zhmccli issue tracker`_.

.. _zhmccli issue tracker: https://github.com/zhmcclient/zhmccli/issues


.. _`License`:

License
-------

This package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://raw.githubusercontent.com/zhmcclient/zhmccli/master/LICENSE
