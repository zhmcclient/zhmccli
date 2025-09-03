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

.. _`Appendix`:

Appendix
========

This section contains information that is referenced from other sections,
and that does not really need to be read in sequence.


.. _`Troubleshooting`:

Troubleshooting
---------------

The `zhmcclient Troubleshooting <https://python-zhmcclient.readthedocs.io/en/stable/appendix.html#troubleshooting>`_
section also applies to the zhmccli project.

There are no additional zhmccli-specific troubleshooting hints at the moment.


.. _`Glossary`:

Glossary
--------

This documentation uses a few special terms:

.. glossary::

   HMC
      Hardware Management Console; the node the zhmcclient talks to.

   session-id
      an opaque string returned by the HMC as the result of a successful
      logon, for use by subsequent operations instead of credential data.
      The HMC gives each newly created session-id a lifetime of 10 hours, and
      expires it after that.


.. _`Bibliography`:

Bibliography
------------

.. glossary::

   HMC API
       `IBM SC27-2646-00, IBM Z Hardware Management Console Web Services API (Version 2.17.0) <https://www.ibm.com/docs/ko/module_1721331501652/pdf/SC27-2646-00.pdf>`_

   HMC Security
       `IBM SC28-7061-00, IBM Z Hardware Management Console Security (Version 2.17.0) <https://www.ibm.com/docs/ko/module_1721331501652/pdf/SC28-7061-00.pdf>`_

   HMC Help
       `IBM Z Hardware Management Console Help (Version 2.17.0) <https://www.ibm.com/docs/en/help-ibm-hmc-z17>`
