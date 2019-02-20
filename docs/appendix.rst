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

.. _`Appendix`:

Appendix
========

This section contains information that is referenced from other sections,
and that does not really need to be read in sequence.


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
       The Web Services API of the z Systems Hardware Management Console, described in the following books:

   HMC API 2.11.1
       `IBM SC27-2616, z Systems Hardware Management Console Web Services API (Version 2.11.1) <https://www-01.ibm.com/support/docview.wss?uid=isg238ba3e47697d87e385257967006ab34e>`_

   HMC API 2.12.0
       `IBM SC27-2617, z Systems Hardware Management Console Web Services API (Version 2.12.0) <https://www-01.ibm.com/support/docview.wss?uid=isg29b97f40675618ba085257a6a00777bea>`_

   HMC API 2.12.1
       `IBM SC27-2626, z Systems Hardware Management Console Web Services API (Version 2.12.1) <https://www-01.ibm.com/support/docview.wss?uid=isg23ddb93b38680a72f85257ba600515aa7>`_

   HMC API 2.13.0
       `IBM SC27-2627, z Systems Hardware Management Console Web Services API (Version 2.13.0) <https://www-01.ibm.com/support/docview.wss?uid=isg27fa57a5a8a5297b185257de7004e7144>`_

   HMC API 2.13.1
       `IBM SC27-2634, z Systems Hardware Management Console Web Services API (Version 2.13.1) <https://www-01.ibm.com/support/docview.wss?uid=isg2cb468b15654ca89b85257f7200746c16>`_

   HMC Operations Guide
       The operations guide of the z Systems Hardware Management Console, described in the following books:

   HMC Operations Guide 2.11.1
       `IBM SC28-6905, System z Hardware Management Console Operations Guide (Version 2.11.1) <https://www-01.ibm.com/support/docview.wss?uid=isg2f287015984420833852578ff0067d8f9>`_

   HMC Operations Guide 2.13.1
       `IBM z Systems Hardware Management Console Operations Guide (Version 2.13.1) <https://www-01.ibm.com/support/docview.wss?uid=isg20351070eb1b67cd985257f7000487d13>`_

   KVM for IBM z Systems V1.1.2 System Administration
       `IBM SC27-8237, KVM for IBM z Systems V1.1.2 System Administration <https://www.ibm.com/support/knowledgecenter/SSNW54_1.1.2/com.ibm.kvm.v112.kvmlp/KVM.htm>`_


.. include:: changes.rst
