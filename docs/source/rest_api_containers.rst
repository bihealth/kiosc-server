.. _rest_api_containers:

Containers
==========

.. contents::

Create Container
----------------

Create container in a project.

=========  ===========================================
URL        /containers/api/create/<PROJECT_SODAR_UUID>
Method     ``POST``
Data type  JSON dictionary
=========  ===========================================

**Example cURL**::

    curl -X POST -H "Content-Type: application/json" -H "Authorization: token 1234567890abcdef" --data '{"title": "Nginx echo headers", "repository": "brndnmtthws/nginx-echo-headers", "tag": "latest"}' https://kiosc.bihealth.org/containers/api/create/00000000-0000-0000-0000-000000000000

Delete Container
----------------

Delete container from a project given a container SODAR UUID.

======  =============================================
URL     /containers/api/delete/<CONTAINER_SODAR_UUID>
Method  ``DELETE``
======  =============================================

**Example cURL**::

    curl -X DELETE -H "Authorization: token 1234567890abcdef" http://kiosc.bihealth.org/containers/api/delete/cccccccc-cccc-cccc-cccc-cccccccccccc

List Containers
---------------

List all containers available in a project.

======  ====================================
URL     /containers/api/<PROJECT_SODAR_UUID>
Method  ``GET``
======  ====================================

**Example cURL**::

    curl -H "Authorization: token 1234567890abcdef" http://kiosc.bihealth.org/containers/api/00000000-0000-0000-0000-000000000000

Container Details
-----------------

Show details and logs of a given container.

======  =============================================
URL     /containers/api/detail/<CONTAINER_SODAR_UUID>
Method  ``GET``
======  =============================================

**Example cURL**::

    curl -H "Authorization: token 1234567890abcdef" http://kiosc.bihealth.org/containers/api/detail/cccccccc-cccc-cccc-cccc-cccccccccccc

Start Container
---------------

Start a given container.

======  =============================================
URL     /containers/api/start/<CONTAINER_SODAR_UUID>
Method  ``GET``
======  =============================================

**Example cURL**::

    curl -H "Authorization: token 1234567890abcdef" http://kiosc.bihealth.org/containers/api/start/cccccccc-cccc-cccc-cccc-cccccccccccc

Stop Container
--------------

Stop a given container.

======  ===========================================
URL     /containers/api/stop/<CONTAINER_SODAR_UUID>
Method  ``GET``
======  ===========================================

**Example cURL**::

    curl -H "Authorization: token 1234567890abcdef" http://kiosc.bihealth.org/containers/api/stop/cccccccc-cccc-cccc-cccc-cccccccccccc

