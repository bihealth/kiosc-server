.. image:: https://img.shields.io/github/v/release/bihealth/kiosc
    :target: https://github.com/bihealth/kiosc-server/releases
    :alt: GitHub Release
.. image:: https://readthedocs.org/projects/kiosc-server/badge/?version=latest
    :target: https://kiosc-server.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/badge/License-MIT-green.svg
    :target: https://opensource.org/licenses/MIT
.. image:: https://coveralls.io/repos/github/bihealth/kiosc-server/badge.svg
    :target: https://coveralls.io/github/bihealth/kiosc-server


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
- Docker and Docker Compose (see `here <https://docs.docker.com>`__ for documentation)

---------------
Getting Started
---------------

The recommended way to install Kiosc is through Docker Compose.
Note that the Docker Compose file lives in a `separate repository <https://github.com/bihealth/kiosc-docker-compose>`__.
For a quick start, run these commands::

    git clone https://github.com/bihealth/kiosc-docker-compose.git
    cd kiosc-docker-compose
    bash init.sh
    cp env.example .env

Manually modify the settings, environment variables, and secret keys in the .env file as described in the `manual <https://kiosc-server.readthedocs.io/en/latest/introduction_installation.html#configuration>`__, then continue with::

    docker compose --profile deploy up -d
    docker compose exec -it kiosc-web ./manage.py createsuperuser

Follow the interactive instructions on the console to create the admin user, then point your browser to https://localhost (if you get a security warning from the browser, it is normal and expected, so you can safely circumvent the warning).

After logging in with the superuser credentials you just created, you should see an empty Kiosc home page.
At this point, you can proceed in many ways, depending on your needs.
Some of the things you can do are briefly described below.
For further instructions and alternative installation methods, read the `installation chapter <https://kiosc-server.readthedocs.io/en/latest/introduction_installation.html>`__ of the manual.

-----
Usage
-----

Create a "Hello World" project with a toy app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Running the following command in the terminal will create a top-level category, create a project within that category, and set up a demo of a `Shiny app <https://rocker-project.org/images/versioned/shiny.html>`__.
You can use this app as a smoke test for the success of the installation.

::

    docker compose exec -it kiosc-web ./manage.py createtoyapp

Manually create a top-level category
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Kiosc, every project must belong to a category.
Only the superuser is allowed to create and add members to top-level categories, while regular users can create projects inside categories where they are owners.
To create a category, click on the "Create Category" button in the left menu.
Afterwards, you'll be able to modify the members of the category or create subprojects within it, again from the left-side menu.
When you are inside a project, you will see additional entries in the left-side menu; clicking on the "Containers" button will bring you to a list view of the current containers in the project, from where you can also create new ones.

Set up local user accounts
^^^^^^^^^^^^^^^^^^^^^^^^^^

Kiosc supports centralized authentication methods, including LDAP and SSO (check out the `configuration instructions <https://kiosc-server.readthedocs.io/en/latest/introduction_installation.html#configuration>`__).
However, if you are setting up a small and local installation for your colleagues, you may simply want to create a few local accounts.
If you are comfortable with the command line, this can be done by running the following command::

    docker compose exec -ti kiosc-web ./manage.py shell -c 'User.objects.create_user("<username>", "<email>", "<password>")'

Where you should replace the fields within ``<angle brackets>`` with the relevant values.

Creating user accounts can also be done from the admin web interface: navigate to https://localhost/admin/users and click "Add".

Using the web interface
^^^^^^^^^^^^^^^^^^^^^^^

The best way to learn Kiosc is by exploring the web interface.
Check out the `manual <https://kiosc-server.readthedocs.io/en/latest/>`__ for detailed iformation about all the components.
If you get stuck, recall that Kiosc is a `Django <https://www.djangoproject.com>`__ site based on the `SODAR-Core <https://github.com/bihealth/sodar-core>`__ framework, so you can often find help on the dedicated support channels for these projects.
For Kiosc-specific problems, please use the `issue tracker <https://github.com/bihealth/kiosc-server/issues>`__ or contact the authors directly.

-----------
At a Glance
-----------

- License: MIT
- Dependencies / Tech Stack

  - Python >=3.11
  - Django 5.2
  - SODAR Core 1.3
  - PostgreSQL >=16
