.. _introduction_roles:

Roles
=====

Kiosc provides the same roles as SODAR Core as it is based on this framework.
However, this section will clarify what each role is allowed to do within Kiosc.

.. contents::

Containers
----------

=============  =============  ======  =====  =====  =========  ====
Role           Create/Update  Delete  Start  Stop   (Un)pause  View
=============  =============  ======  =====  =====  =========  ====
Administrator  OK             OK      OK     OK     OK         OK
Owner          OK             OK      OK     OK     OK         OK
Delegate       OK             OK      OK     OK     OK         OK
Contributor    OK             OK      OK     OK     OK         OK
Guest                                 (OK)*                    OK
=============  =============  ======  =====  =====  =========  ====

\* *Guests can't start the container directly, but do so indirectly by requesting to view a not running container.*

Container Templates
-------------------

Project-wide
^^^^^^^^^^^^

=============  =============  ======  ===============  ====
Role           Create/Update  Delete  Copy*/Duplicate  View
=============  =============  ======  ===============  ====
Administrator  OK             OK      OK               OK
Owner          OK             OK      OK               OK
Delegate       OK             OK      OK               OK
Contributor    OK             OK      OK               OK
Guest                                                  OK
=============  =============  ======  ===============  ====

\* *Copy project-wide or site-wide templates.*

Site-wide
^^^^^^^^^

=============  =============  ======  =========  ====
Role           Create/Update  Delete  Duplicate  View
=============  =============  ======  =========  ====
Administrator  OK             OK      OK         OK
Owner                                            OK
Delegate                                         OK
Contributor                                      OK
Guest                                            OK
=============  =============  ======  =========  ====
