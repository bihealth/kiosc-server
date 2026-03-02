.. _introduction_interface:

Interface
=========

When accessing the Kiosc web interface, one is greeted
with the Kiosc logo and a login form. You need to have an
account with Kiosc or the LDAP must be configured to be
able to log in with your institute account. Approach your
system administrator about that matter if you are unsure.

.. image:: figures/introduction/interface/login.png
  :alt: Login


Projects List
-------------

Once logged in, you will see an overview of all the projects
you are assigned to, alike SODAR. If you do expect to have
access to a project you do not have access to, ask the leader or
delegate of that project to grant you access to that project.
If the Kiosc instance is linked to a SODAR instance, the access
is set in SODAR and must then be synchronized to Kiosc by the
administrator.

.. image:: figures/introduction/interface/home.png
  :alt: Home


Managing Containers and Container Templates
-------------------------------------------

To be able to access the Kiosc apps, click on a project. On the
left-hand side you will have access to multiple apps, three
of them are of interest:

1. **Containers** for creating and controlling Docker containers.
2. **Container Template** for creating templates for Docker containers.
3. **Small Files** for uploading smaller files that the containers can then access.

.. image:: figures/introduction/interface/project_overview.png
  :alt: Project overview

Additionally, in the top-right corner is a drop-down menu for account settings and
site apps. This gives access to the site-wide container template app. This hosts
container templates that are accessible site-wide and not project-wide.

.. image:: figures/introduction/interface/settings_menu.png
  :alt: Settings menu


Searching Containers and Logs
-----------------------------

At the center of the top bar you will find the search box. You
can use it to search objects such as containers, small files,
site events, and log entries. Searching in KIOSC follows the same
principles as in SODAR Core (you can read more about it `here
<https://sodar-core.readthedocs.io/en/latest/app_projectroles_usage.html#search>`__).
Briefly, you can enter search terms but also restrict the results to
certain object types and limit the search to a particular project. Search is
best explained by example, so here are a few strings that you can enter in the
search box along with an explanation of what they do.

``seapiper``
  search all projects, files, timeline events, containers, and logs that contain
  the string "seapiper"

``seapiper type:container``
  search all *containers* with "seapiper" in the title, description, or
  repository

``proteomics type:container``
  search all *containers* with "proteomics" in the title, description, or
  repository

``seapiper type:containerbackgroundjob``
  search all *container background jobs* related to "seapiper" containers

``seapiper type:containerlogentry``
  search all *container log entries* containing the string "seapiper"

``error type:containerlogentry project:0f0556cf-0e9f-4923-b2b9-49e573b893f0``
  search for errors in log entries for the project with UUID
  ``0f0556cf-0e9f-4923-b2b9-49e573b893f0``

For complex searches involving multiple terms you can press the *Advanced
Search* button to the left of the search box.
