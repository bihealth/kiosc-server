.. _introduction_development:

Development environment
=======================

.. note::

    This chapter is meant for Kiosc developers, feel free to skip this chapter if you only want to use Kiosc.

The same docker compose used for the production deployment can also be used
as a development environment. After cloning the `docker compose repository
<https://github.com/bihealth/kiosc-docker-compose>`__, pass the `--profile
dev`` argument, so that only the services strictly required by Kiosc will run.
Manually setting up the database and scheduler is not described in this manual.

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

The configuration for the development instance is similar to the one `described
for the production environment <introduction_installation_configuration>`__.
However, the ``env.example`` in the kiosc-server repository is more geared
towards development.
