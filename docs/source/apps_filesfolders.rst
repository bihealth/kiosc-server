.. _apps_filesfolders:

Small Files
===========

Kiosc has activated an app provided by SODAR Core that allows the
user to upload files of smaller size (several MB, but not GB).

Those files then can be accessed by the containers created. For this
to work, a dropdown menu of files uploaded to a project is provided
during container creation that allows to insert an internal
link to that file into the ``command`` field. This link can only be
accessed by containers that are associated running inside the same
project the files is associated with.

The intention is that the application running inside of the container
uses links to load the files anyway, and those links now can be replaced
with internal links to files that are uploaded to Kiosc. This also
requires the application inside the container to accept links as file
source, another way to provide the file is not possible.


