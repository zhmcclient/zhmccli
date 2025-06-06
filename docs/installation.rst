.. Copyright 2016,2019,2025 IBM Corp. All Rights Reserved.
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


.. _`Installation`:

Installation
============

This section describes how to install the zhmccli Python package and set up the
HMC.

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _Pypi: http://pypi.python.org/


.. _`Steps`:

Steps
-----

The installation steps are described using Unix/Linux/macOS commands. When
installing on Windows, use the equivalent Windows commands (e.g. "md" instead of
"mkdir").

1.  Install the zhmccli Python package using any of the following approaches:

    * :ref:`Installation using pipx` (recommended approach)
    * :ref:`Installation into a virtual Python environment`
    * :ref:`Installation into a system Python`
    * :ref:`Installation on a system without Internet access`

    You can verify that the zhmccli package and its dependent packages are
    installed correctly by invoking:

    .. code-block:: bash

        $ zhmc --version
        zhmc, version 1.13.0
        zhmcclient, version 1.21.0

2.  Make sure the HMC is set up correctly.

    * The Web Services API is enabled on the HMC
    * The HMC should have a CA-verifiable certificate installed
    * The HMC userid has permission for the Web Services API
    * The HMC userid has the required object and task permissions

    For details, see :ref:`Setting up the HMC`.

3.  Make sure the HMC can be reached from the system that runs the zhmc command.

    When using firewalls or proxies, see :ref:`Setting up firewalls or proxies`.


.. _`Installation using pipx`:

Installation using pipx
-----------------------

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


.. _`Installation into a virtual Python environment`:

Installation into a virtual Python environment
----------------------------------------------

In some cases it may be useful to install zhmccli into your own
`virtual Python environment`_. That avoids the dependency to pipx, but it
requires you to activate the virtual environment every time you want to use the
``zhmc`` command.

There are a number of ways how virtual Python environments can be created. This
documentation describes the use of "virtualenv":

1.  Prerequisite: Install the Python virtualenv package as an OS-level package
    or into the system Python.

    Follow the steps at https://virtualenv.pypa.io/en/latest/installation.html
    to install virtualenv.

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


.. _`Installation into a system Python`:

Installation into a system Python
---------------------------------

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


.. _`Installation on a system without Internet access`:

Installation on a system without Internet access
------------------------------------------------

When installing Python packages using pip or pipx, Internet access is needed to
access the Pypi repository.

If you want to install the zhmccli package on a system that does not have
Internet access, you can do this by first downloading the zhmccli package
and its dependent packages on a download system that does have Internet access.
This also downloads any dependent Python packages. Then, these packages are made
available to the target system. e.g. via a shared file system or by transferring
the files, and then you can install the zhmccli package from these files on the
target system.

Important: The downloaded package files need to be compatible with the OS/HW
platform, Python version and Python implementation that will be used on the
target system. Pip by default uses the current Python and OS/HW platform to
determine these parameters. If the OS/HW platform, Python version or Python
implementation on the download system are not compatible with the target system,
you can use the pip options ``--platform``, ``--python-version`` and
``--implementation`` to select parameters that are compatible with the target
system.

For simplicity, the following example uses a shared file system between the
download and target systems, and has OS/HW platform, Python version and Python
implementation that are compatible between download system and target system.

On the download system:

.. code-block:: bash

    [download]$ python -c "import platform; print(platform.platform())"
    macOS-14.7.2-arm64-arm-64bit

    [download]$ python -c "import platform; print(platform.python_version())"
    3.13.0

    [download]$ python -c "import platform; print(platform.python_implementation())"
    CPython

    [download]$ mkdir download; cd download

    [download]$ python -m pip download zhmccli

    [download]$ ls -1
    PyYAML-6.0.2-cp312-cp312-macosx_11_0_arm64.whl
    . . . (more packages)
    setuptools-80.7.1-py3-none-any.whl
    . . . (more packages)
    zhmccli-1.13.0-py3-none-any.whl
    zhmcclient-1.21.0-py3-none-any.whl

On the target system, with an active virtual Python environment:

.. code-block:: bash

    [target](zhmc)$ python -c "import platform; print(platform.platform())"
    macOS-13.6.3-arm64-arm-64bit

    [target](zhmc)$ python -c "import platform; print(platform.python_version())"
    3.13.1

    [target](zhmc)$ python -c "import platform; print(platform.python_implementation())"
    CPython

    [target](zhmc)$ ls -1
    PyYAML-6.0.2-cp312-cp312-macosx_11_0_arm64.whl
    . . . (more packages)
    setuptools-80.7.1-py3-none-any.whl
    . . . (more packages)
    zhmccli-1.13.0-py3-none-any.whl
    zhmcclient-1.21.0-py3-none-any.whl

    [target](zhmc)$ python -m pip install -f . --no-index zhmccli-1.13.0-py3-none-any.whl

Note: Installation using pipx does not seem to work from a downloaded package
file.


.. _`Setting up the HMC`:

Setting up the HMC
------------------

Usage of the zhmccli package requires that the HMC in question is prepared
accordingly:

* The Web Services API must be enabled on the HMC.

  You can do that in the HMC GUI by selecting "HMC Management" in the left pane,
  then opening the "Configure API Settings" icon on the pain pane,
  then selecting the "Web Services" tab on the page that comes up, and
  finally enabling the Web Services API on that page.

  The above is on a z16 HMC, it may be different on older HMCs.

  If you cannot find this icon, then your userid does not have permission
  for the respective task on the HMC. In that case, there should be some
  other HMC admin you can go to to get the Web Services API enabled.

* The HMC should be configured to use a CA-verifiable certificate. This can be
  done in the HMC task "Certificate Management". See also the :term:`HMC Security`
  book and Chapter 3 "Invoking API operations" in the :term:`HMC API` book.

  For more information, see the
  `Security <https://python-zhmcclient.readthedocs.io/en/latest/security.html>`_
  section in the documentation of the 'zhmcclient' package.

  See :ref:`Using HMC certificates` for how to use HMC certificates with the
  zhmc command.

* The HMC userid that is used by the zhmc command must have the following flag
  enabled:

  - "Allow access to Web Services management interfaces" flag of the user in
    the HMC GUI, or "allow-management-interfaces" property of the user at the
    WS-API.

* In order to be able to perform all commands, the HMC userid that is used by
  the zhmc command must be authorized for the following tasks:

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

* (Optional) If desired, the HMC userid that is used by the zhmc command
  can be restricted to accessing only certain resources managed by the HMC.
  To establish such a restriction, create a custom HMC user role, limit
  resource access for that role accordingly, and associate the HMC userid
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
