.. image:: https://readthedocs.org/projects/kiosc-server/badge/?version=latest
    :target: https://kiosc-server.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/badge/License-MIT-green.svg
    :target: https://opensource.org/licenses/MIT


=====
Kiosc
=====

Kiosc is a web application to orchestrate containerized web services and
interactive reports across projects and users. It allows you to create and
manage Docker containers, organize them into categories and projects, and
control who can access the containers in a multi-user setting. If you are
familiar with Kubernetes, Kiosc is an easier alternative for simple yet scalable
use cases, such as showcasing the results of data science projects through
interactive apps.

------------
Requirements
------------

- A machine for hosting Kiosc and the web apps it manages
- Docker and Docker Compose

---------------
Getting Started
---------------

The recommended way to install Kiosc is through Docker Compose.
For a quick start, run these commands::

    git clone https://github.com/bihealth/kiosc-docker-compose.git
    cd kiosc-docker-compose
    bash init.sh
    cp env.example .env

Manually modify the settings, environment variables, and secret keys in the .env file, then continue with::

    docker compose --profile deploy up -d
    docker compose exec -it kiosc-web ./manage.py createsuperuser

Follow the interactive instructions to create the admin user, then point your browser to https://localhost:443.

Note that the Docker Compose file lives in a `separate repository <https://github.com/bihealth/kiosc-docker-compose>`__.
For further instructions and alternative installation methods, read the `installation chapter <https://kiosc-server.readthedocs.io/en/latest/introduction_installation.html>`__ of the manual.

-----
Usage
-----

Kiosc is a web application written in the Django framework.
Check out the `manual <https://kiosc-server.readthedocs.io/en/latest/>`__ to learn how it works.

-----------
At a Glance
-----------

- License: MIT
- Dependencies / Tech Stack

  - Python >=3.11
  - Django 5.2
  - SODAR Core 1.3
  - PostgreSQL >=16
