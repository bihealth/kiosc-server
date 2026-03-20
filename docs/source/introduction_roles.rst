.. _introduction_roles:

Roles
=====

Any multi-user system needs a way to control who has access to the various resources.
In Kiosc, each user can be assigned a role for a specific project; depending on their role, users will have different read and/or write access to the project resources.
This chapter will clarify what each role is allowed to do within Kiosc.

.. tip::

    Kiosc uses the same role system as `SODAR <https://sodar-core.readthedocs.io/en/latest/app_projectroles_basics.html>`__. If you are already familiar with that, understanding this page will be easier.

There are many ways to get a role in a project.
First, if you created the project, you will typically have the *owner* role.
Project owners can add users to the current project by clicking on "Members" in the left side menu bar.
When new members are invited, they are also assigned a specific role, chosen by the owner.
The two main apps, Containers and Container Templates, define different resources and control access to them independently, hence they are described separately here.
Permissions will be described with a matrix that shows the roles on the rows and the possible actions along the columns.

.. contents::
   :local:

Containers
----------

=============  =============  ======  ==========  =====  =========  ====
Role           Create/Update  Delete  Start       Stop   (Un)pause  View
=============  =============  ======  ==========  =====  =========  ====
Administrator  OK             OK      OK          OK     OK         OK
Owner          OK             OK      OK          OK     OK         OK
Delegate       OK             OK      OK          OK     OK         OK
Contributor    OK             OK      OK          OK     OK         OK
Guest                                 (OK)\ [#]_                    OK
=============  =============  ======  ==========  =====  =========  ====

.. [#] *Guests can't start the container directly, but do so indirectly by requesting to view a not running container.*

Container Templates
-------------------

Project-wide
^^^^^^^^^^^^

=============  =============  ======  ====================  ====
Role           Create/Update  Delete  Copy\ [#]_/Duplicate  View
=============  =============  ======  ====================  ====
Administrator  OK             OK      OK                    OK
Owner          OK             OK      OK                    OK
Delegate       OK             OK      OK                    OK
Contributor    OK             OK      OK                    OK
Guest                                                       OK
=============  =============  ======  ====================  ====

.. [#] *Copy project-wide or site-wide templates.*

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
