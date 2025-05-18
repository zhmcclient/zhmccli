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
