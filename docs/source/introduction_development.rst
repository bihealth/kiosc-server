.. _introduction_development:

Development environment
=======================

.. note::

    This chapter is meant for Kiosc developers or administrators who want to install Kiosc manually. Feel free to skip this chapter if you only want to use Kiosc.

If you want to install Kiosc manually or contribute to its development, you will be responsible for installing and making sure that the following services are available:

- The Kiosc django web app
- A celery daemon for distributed background tasks
- A celerybeat process for scheduled recurrent tasks
- A database to store project and container metadata (we recommend PostgreSQL v16)
- Redis (we recommend v8), used as celery broker and generic cache provider

The Kiosc repository provides scripts and Makefile rules to conveniently run the django web app through an ASGI server, as well as the celery daemon and the celerybeat process, but you are still required to install and run the database and redis.
These services can be installed manually as well; we refer the interested reader to the relevant documentation for `PostgreSQL <https://www.postgresql.org/>`__ and `Redis <https://github.com/redis/redis>`__.
However, the same docker compose used for the production deployment can also be used as a development environment which provides just PostgreSQL and Redis.
We describe this setup in detail here.

After cloning the `docker compose repository
<https://github.com/bihealth/kiosc-docker-compose>`__, pass the ``--profile
dev`` argument, so that only the services strictly required by Kiosc will
run [#footnote-make-dev]_.

.. code-block:: console

    $ docker compose --profile dev up

The web server needs to be started separately. To do that, clone the `Kiosc
repository <https://github.com/bihealth/kiosc-server>`__ and follow these
instructions. This document assumes that you are using the latest Ubuntu stable
release (the officially supported operating system), so you may need to adjust
the commands depending on your requirements. We also provide some utility
scripts to simplify the installation process.

First, install the system dependencies.

.. code-block:: console

    $ ./utility/install_os_dependencies.sh
    $ ./utility/install_python.sh

The scripts will install the latest python version officially supported by
Kiosc. In the rest of the document, we will use ``python3.x`` to denote the
Python executable, but please replace ``x`` with the correct version (for
example, use ``python3.13``).

Create a Python virtual environment and install the required packages.

.. code-block:: console

    $ python3.x -m venv .venv
    $ pip install -r requirements.txt
    $ pip install -r requirements/test.txt

If you want to use LDAP, which is optional, you may also need to install its
dependencies:

.. code-block:: console

    $ ./utility/install_ldap_dependencies.sh
    $ pip install -r requirements/ldap.txt

Copy ``env.example`` to ``.env``

.. code-block:: console

    $ cp env.example .env

Set up Django.

.. code-block:: console

    $ ./manage.py migrate
    $ ./manage.py createsuperuser --skip-checks --username admin
    $ ./manage.py geticons
    $ ./manage.py collectstatic

At this point you are ready to run the server. The kiosc-server repository
includes a Makefile to run common commands more conveniently. Thus, you can
run::

    $ make asgi

and point your browser to https://127.0.0.1:8000 to access Kiosc.

Configuration
-------------

The configuration for the development instance is similar to the one :ref:`described
for the production environment <introduction_installation_configuration>`.
However, the ``env.example`` in the kiosc-server repository is more geared
towards development.

.. rubric:: Footnotes

.. [#footnote-make-dev] You may also simply run ``make dev``, using the Makefile
    we provide.
