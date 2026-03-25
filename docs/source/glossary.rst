.. _glossary:


Glossary
========

.. glossary::

Kiosc terms
^^^^^^^^^^^

    Kiosc
        A self-hosted web site for publishing and managing containerized web apps.

    Django app
        Kiosc is built using the `Django <https://djangoproject.com>`__
        framework and it consists of several `apps
        <https://docs.djangoproject.com/en/5.2/ref/applications/>`__. These apps
        can be classified as project-specific (accessible only when you are
        inside a project) or site-wide (which are always accessible and are not
        tied to any projects).

        - Project-specific apps:

          - Containers
          - Container templates
          - Files and folders
          - Timeline
          - Background jobs

        - Site-wide apps:

          - Container list
          - Container templates

    Web app
        An interactive web page. In Kiosc, we focus on web apps
        for exploratory data analysis or results visualization.
        Examples of web apps supported in Kiosc are `Shiny
        <https://shiny.posit.co/>`__, `Dash <https://dash.plotly.com/>`__,
        `seaPiper <https://bihealth.github.io/seaPiper/>`__, `CELLxGENE
        <https://cellxgene.cziscience.com/>`__, and `ScElvis
        <https://scelvis.readthedocs.io/en/latest/>`__.

SODAR terms
^^^^^^^^^^^

    `SODAR <https://github.com/bihealth/sodar>`__
        System for Omics Data Access and Retrieval. An omics research data
        management system which is the origin of the reusable SODAR Core
        framework.

    `SODAR Core <https://github.com/bihealth/sodar-core>`__
        Core framework and reusable apps originally built for the SODAR project.

    Peer Site
        A SODAR Core based web site which mirrors one or more projects also
        mirrored on the currently active site. This allows linking to remote
        projects on other sites where the user would have access.

    Source Site
        SODAR Core based web site which mirrors project metadata and access
        control to "target" sites.

    Target Site
        SODAR Core based web site which mirrors project metadata and access
        control from a "source" site.

Docker terms
^^^^^^^^^^^^

    `Docker <https://www.docker.com>`__
        A program for creating images and running containers.

    Docker Container
        An application that runs in a controlled and isolated environment.

    Docker Image
        A package (think of it as a ZIP archive) that contains a recipe for
        creating a container.

    Docker Compose
        A program for running multiple containers so that they can interact with
        each other. Can be used to run Kiosc.
