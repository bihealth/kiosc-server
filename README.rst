SODAR Django Site
^^^^^^^^^^^^^^^^^

.. image:: https://travis-ci.com/bihealth/sodar_django_site.svg?token=BANPpQjiM3fGGTK4nz1z&branch=master
    :target: https://travis-ci.com/bihealth/sodar_django_site

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT

This project contains a minimal `Django 1.11 <https://docs.djangoproject.com/en/1.11/>`_
site template for building `SODAR Core <https://github.com/bihealth/sodar_core>`_
based projects.


Introduction
============

The site is based on one created by the last Django 1.11 release of
`cookiecutter-django <https://github.com/pydanny/cookiecutter-django/tree/1.11.10>`_.
That project has since moved on to Django 2.x which is not yet supported by
SODAR Core. This template site remains in 1.11, while updating base requirements
and omitting things not relevant to SODAR Core based sites.

Included in this project are the critical OS and Python requirements, pre-set
Django settings, a pre-installed SODAR Core framework and some helper scripts.
It is also readily compatible with Selenium UI testing, coverage checking and
continuous integration for Travis-CI and GitLab-CI.

The current version of this site is compatible with
`SODAR Core v0.4.5 <https://github.com/bihealth/sodar_core/tree/v0.4.5>`_.


Installation for Development
============================

For instructions and best practices in Django development, see
`Django 1.11 documentation <https://docs.djangoproject.com/en/1.11/>`_ and
`Two Scoops of Django <https://twoscoopspress.com/products/two-scoops-of-django-1-11>`_.

For SODAR Core concepts and instructions, see
`SODAR Core documentation <https://github.com/bihealth/sodar_core/tree/v0.4.5/docs>`_.

The examples here use virtualenv and pip, but you may also use e.g. conda for
virtual environments and installing packages.

Requirements
------------

- Ubuntu 16.04 Xenial
- Python 3.6+
- Postgres 9.6+

System Installation
-------------------

First you need to install OS dependencies, PostgreSQL 9.6 and Python3.6.

.. code-block:: console

    $ sudo utility/install_os_dependencies.sh
    $ sudo utility/install_python.sh
    $ sudo utility/install_postgres.sh

Database Setup
--------------

Create a PostgreSQL user and a database for your application. In the example,
we use ``sodar_core`` for the database, user name and password. Make sure to
give the user the permission to create further PostgreSQL databases (used for
testing).

.. code-block:: console

    $ sudo su - postgres
    $ psql
    $ CREATE DATABASE sodar_core;
    $ CREATE USER sodar_core WITH PASSWORD 'sodar_core';
    $ GRANT ALL PRIVILEGES ON DATABASE sodar_core to sodar_core;
    $ ALTER USER sodar_core CREATEDB;
    $ \q

You have to add the credentials in the environment variable ``DATABASE_URL``.
For development it is recommended to place this variable in an ``.env`` file and
set ``DJANGO_READ_DOT_ENV_FILE=1`` in your actual environment. See
``config/settings/base.py`` for more information.

.. code-block:: console

    $ export DATABASE_URL='postgres://sodar_core:sodar_core@127.0.0.1/sodar_core'

Project Setup
-------------

Clone the repository, setup and activate the virtual environment. Once in
the environment, install Python requirements for the project:

.. code-block:: console

    $ git clone git+https://github.com/bihealth/sodar_core.git
    $ cd sodar_core
    $ pip install virtualenv
    $ virtualenv -p python3.6 .venv
    $ source .venv/bin/activate
    $ utility/install_python_dependencies.sh

LDAP Setup (Optional)
---------------------

If you will be using LDAP/AD auth on your site, make sure to also run:

.. code-block:: console

    $ sudo utility/install_ldap_dependencies.sh
    $ pip install -r requirements/ldap.txt

Final Setup
-----------

Initialize the database (this will also synchronize django-plugins):

.. code-block:: console

    $ ./manage.py migrate

Create a Django superuser for the example_site:

.. code-block:: console

    $ ./manage.py createsuperuser

Now you should be able to run the server:

.. code-block:: console

    $ ./run.sh

Navigate to `http://0.0.0.0:8000/ <http://0.0.0.0:8000/>`_ and log in to see the
results. The site should be up and running with the default SODAR Core layout.


Developing your Site
====================

Once the installation is successful, you can continue to add your own
SODAR based apps. See
`SODAR Core documentation <https://github.com/bihealth/sodar_core/tree/v0.4.5/docs>`_.
for further instructions.
