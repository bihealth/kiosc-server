.. _manual_main:

Welcome to the Kiosc documentation!
========================================

Kiosc is a web application to orchestrate containerized web services and interactive reports across projects and users.
It allows you to create and manage docker containers, organize them into projects and sub-projects, and control who can access the containers in a multi-user setting.
If you are familiar with Kubernetes, Kiosc is an easier alternative for groups with simple needs, such as showcasing the results of data science projects through interactive apps.
In particular, it allows users to autonomously create and organize *ad hoc* web services without being experts in either docker or web administration.
Kiosc takes care of running the container in the appropriate network and letting the users access it, acting as a proxy to the docker containers.
Running and administering Kiosc is as simple as starting a docker container and only requires a single machine.

What Kiosc is and what it is not
--------------------------------

Kiosc is a web interface where users can:

- Authenticate through LDAP, SSO, OIDC, or local accounts
- Download existing docker images and create containers from them
- Organize containers into projects and subprojects
- Access the web services running inside the containers
- Control who else can access their containers 
- Check the status of containers, stop, or restart them

Kiosc is NOT

- A tool to create docker images
- For constraining and scaling resources allocated to containers
- For running Docker images without webserver (you can do that, but you likely won't benefit much from it)
- For directly loading or sharing data (this has to be managed by the Docker image).

.. tip::

    If your group also use `SODAR <https://github.com/bihealth/sodar-server>`__, projects and users can be directly imported from there.


.. note::

   You can find the official version of this documentation at
   `readthedocs.io <https://kiosc-server.readthedocs.io/en/latest/>`_.
   If you view these files on GitHub, beware that their renderer does not
   render the ReStructuredText files correctly and content may be missing.

.. toctree::
    :maxdepth: 2
    :caption: Introduction
    :name: introduction
    :hidden:
    :titlesonly:

    introduction_overview
    Docker concepts <introduction_docker>
    introduction_installation

.. toctree::
    :maxdepth: 2
    :caption: Usage
    :name: usage
    :hidden:
    :titlesonly:

    introduction_interface
    introduction_roles
    introduction_cookbook

.. toctree::
    :maxdepth: 2
    :caption: Apps
    :name: apps
    :hidden:
    :titlesonly:

    apps_containers
    apps_containertemplates
    apps_filesfolders

.. toctree::
    :maxdepth: 2
    :caption: Administration
    :name: administration
    :hidden:
    :titlesonly:

    administration_overview
    administration_commands
    administration_periodic_tasks

.. toctree::
    :maxdepth: 2
    :caption: REST API
    :name: rest_api
    :hidden:
    :titlesonly:

    rest_api_overview
    rest_api_containers

.. toctree::
    :maxdepth: 2
    :caption: Development
    :name: development
    :hidden:
    :titlesonly:

    introduction_development
    code_of_conduct

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
