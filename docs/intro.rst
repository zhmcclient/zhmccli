.. Copyright 2016,2019 IBM Corp. All Rights Reserved.
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

* Python versions: 3.8 and higher

* HMC versions: 2.11.1 and higher


.. _`Installation`:

Installation
------------

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _Pypi: http://pypi.python.org/

Installation using pipx
~~~~~~~~~~~~~~~~~~~~~~~

The recommended way to use the zhmccli Python package is by installing it with
pipx.

Pipx creates a `virtual Python environment`_ under the covers and installs the
zhmccli Python package into that environment and makes the ``zhmc`` command
available in a directory that is in the PATH. The ``zhmc`` command will be
available that way, regardless of whether or not you have a virtual Python
environment active (that you may need for other purposes).

1.  Prerequisite: Install pipx as an OS-level package

    Follow the steps at https://pipx.pypa.io/stable/installation/ to install
    pipx as an OS-level package to your local system.

2.  Without having any virtual Python environment active, install zhmccli using
    pipx

    To install the latest released version of zhmccli:

    .. code-block:: bash

        $ pipx install zhmccli

    To install a specific released version of zhmccli, e.g. 1.2.0:

    .. code-block:: bash

        $ pipx install zhmccli==1.2.0

    To install a specific development branch of zhmccli, e.g. master:

    .. code-block:: bash

        $ pipx install git+https://github.com/zhmcclient/zhmccli.git@master

    To install zhmccli with a non-default Python version, e.g. 3.10:

    .. code-block:: bash

        $ pipx install zhmccli --python python3.10

Installation into a virtual Python environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases it may be useful to install zhmccli into your own
`virtual Python environment`_. That avoids the dependency to pipx, but it
requires you to activate the virtual environment every time you want to use the
``zhmc`` command.

There is a number of ways how virtual Python environments can be created. This
documentation describes the use of "virtualenv":

1.  Prerequisite: Install virtualenv into system Python:

    .. code-block:: bash

        $ pip install virtualenv

2.  Create and activate a virtual Python environment:

    .. code-block:: bash

        $ virtualenv ~/.virtualenvs/zhmc
        $ source ~/.virtualenvs/zhmc/bin/activate

3.  Install zhmccli into the virtual Python environment:

    To install the latest released version of zhmccli so that it uses your
    default Python version:

    .. code-block:: bash

        (zhmc) $ pip install zhmccli

    To install a specific released version of zhmccli, e.g. 1.2.0:

    .. code-block:: bash

        (zhmc) $ pip install zhmccli==1.2.0

    To install a specific development branch of zhmccli, e.g. master:

    .. code-block:: bash

        (zhmc) $ pip install git+https://github.com/zhmcclient/zhmccli.git@master

Installation into a system Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your system Python version(s) are installed using OS-level packages for all the
Python functionality.

Adding packages to your system Python using Python packages from Pypi may create
issues. This is why recent
versions of pip raise a warning when attempting to install into the system
Python. Even if you install a Python package from Pypi into your user's space,
this may create issues.

The main issue is that the more Python packages you install into the system
Python, the more likely there will be incompatible Python package dependencies.

Another issue is when you replace OS-level packages with Python packages.

In order to avoid these issues, you should install zhmccli into the system
Python only in cases where the system has a well-defined scope and you have
full control over the set of OS-level and Python-level packages, for example
when building a Docker container.

Installation on a system without Internet access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When installing Python packages using pip or pipx, Internet access is needed to
access the Pypi repository.

If you want to install the zhmccli package on a system that does not have
Internet access, you can do this by first downloading the zhmccli package
and its dependent packages on a download system that does have Internet access,
making these packages available to the target system, and installing on the
target system from the downloaded packages, as described in the previous
sections.

For simplicity, the following example uses a shared file system between the
download and target systems (but that is not a requirement; you can also copy
the downloaded files to the target system):

.. code-block:: bash

    [download]$ pip download zhmccli

    [download]$ ls zhmccli*
    zhmccli-1.12.1-py3-none-any.whl

    [target]$ ls zhmccli*
    zhmccli-1.12.1-py3-none-any.whl

When installing using pipx:

.. code-block:: bash

    [target]$ pipx install zhmccli-1.12.1-py3-none-any.whl

When installing using pip:

.. code-block:: bash

    [target]$ pip install -f . --no-index zhmccli-1.12.1-py3-none-any.whl

Verification of the installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can verify that the zhmccli package and its dependent packages are
installed correctly by invoking:

.. code-block:: bash

    $ zhmc --version
    zhmc, version 1.12.1
    zhmcclient, version 1.19.1


Running in a Docker container
-----------------------------

If you want to run the zhmc command in a Docker container instead of installing
it into a Python environment, you can create the container as follows, using
the Dockerfile provided in the Git repository.

* Clone the Git repository and switch to the clone's root directory:

  .. code-block:: bash

      $ git clone https://github.com/zhmcclient/zhmccli
      $ cd zhmccli

* Build a local Docker image as follows:

  .. code-block:: bash

      $ make docker

  This builds a container image named ``zhmc:latest`` in your local Docker
  environment.

* Run the local Docker image as follows to get help for the zhmc command:

  .. code-block:: bash

      $ docker run --rm zhmc

When running it in the container, the zhmc command cannot be used in
:ref:`interactive mode`.


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


.. _`Setting up firewalls or proxies`:

Setting up firewalls or proxies
-------------------------------

If you have to configure firewalls or proxies between the client system and
the HMC, the following ports need to be opened:

* 6794 (TCP) - for the HMC API HTTP server
* 61612 (TCP) - for the HMC API message broker via JMS over STOMP

For details, see sections "Connecting to the API HTTP server" and
"Connecting to the API message broker" in the :term:`HMC API` book.


.. _`Examples`:

Examples
--------

The following example lists the names of the machines (CPCs) managed by an HMC:

.. code-block:: bash

    $ hmc_host="<IP address or hostname of the HMC>"
    $ hmc_userid="<userid on that HMC>"
    $ zhmc -h $hmc_host -u $hmc_userid cpc list --names-only
    Enter password (for user ... at HMC ...): .......
    +----------+
    | name     |
    |----------+
    | P000S67B |
    +----------+


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
    zhmc, version 1.12.1
    zhmcclient, version 1.19.1

This documentation may have been built from a development level of the
package. You can recognize a development version of this package by the
presence of the string ".dev" in the version.


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
