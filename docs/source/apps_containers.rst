.. _apps_containers:

Containers
==========

Container objects hold the information to create and afterwards to control the underlying
Docker containers. All information the user enters is used during the creation of the
container (when the container is "started"). They also hold information
about the current state and include the logs reported by any process associated
with the container.

.. contents::

Overview
--------

Find the ``Containers`` icon in the left-hand menu to open the Container
app. This will list all available containers and offers the menus to
create new containers, control and delete containers and show details including
its logs.

Detail
------

Click on the title of a container to access its details and the logs.

Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can specify environment variables using JSON syntax (the
``environment`` text area in the container update form). Top-level
JSON names become the environmental variables visible by the app launched
in the container.

```
{
"id":"My container",
"list":[ "A", "B", "C" ]
}
```

Given the above example, two environment variables will be defined: `id`
and `list`.  The contents of `id` will be `My container`; the contents of
`list` will be `[ 'A', 'B', 'C' ]`. Note that the double quotes will be
changed to single quotes!

These variables can then be used in the web app of the
container, and can be used to specify e.g. data source for the container
web app.

Environment & Environment Secret Keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Names of sensitive variables can be entered in the "Environment Secret Keys" field. 

If you have set an ``environment`` and registered ``environment_secret_keys``,
the value of the corresponding items in the environment dictionary are displayed in Kiosc
as ``<masked>``, indicating that they are available to the system but
are not displayed for security reasons. However, they will still be visible
in plain in the container environment.

State
^^^^^

The current state is presented and highlighted:

- **initial**, indicating that the database object has been created but no actual Docker container exists yet.
- **running**
- **failed**, indicating that something went wrong
- **exited**
- **paused**

If there is a small bell icon next to the state, this indicates
that the last user action and the current state of the Docker container
do not match.

Last action
^^^^^^^^^^^

The last action performed on the container of any user is displayed, if available.
If there is an inconsistency found between the actual Docker state and the last
user action (indicated by the bell icon right to the state), a cron job running
every few minutes tries to perform the last known issued user action. The first
number next to the action is a counter, indicating how many times it tried to re-perform the action,
with the maximal limit indicated by the second number.

Date of latest Docker log
^^^^^^^^^^^^^^^^^^^^^^^^^

When a Docker log has been fetched in the past, this date indicates the
timestamp of the latest Docker log and synchronisation of the Docker
state. Docker logs are not displayed immediately in the log file but
fetched by a background process every few minutes. This line is missing
when there are no fetched Docker logs.

Logs
^^^^

The log window combines logs from multiple sources. The structure of a log entry is::

    [YYYY-MM-DD HH:MM:SS <LOG_LEVEL> <USER>] (<PROCESS>) <MESSAGE>

For example::

    [2021-09-08 22:57:26 INFO anonymous] (Task) Syncing last registered container state (running) with current Docker state (exited)

Processes
"""""""""

Currently the following sources can contribute to the log:

- **Task:** Logs reported by automatically running background tasks. Usually they are issued by ``anonymous``.
- **Docker:** Logs reported by Docker for this container. They are fetched every half minute, so they might not appear immediately.
- **Action:** Any action the user issues on the container.
- **Proxy:** Issued when accessing the proxy.
- **Object:** Issued when changes in the database object are made that represents the Container in Kiosc.

Create
------

Click the ``Create Container`` button to enter the form for creating
a new container object. This does not create a Docker container yet but
only gathers information. The actual Docker container is created when
starting the container.

Container Templates
^^^^^^^^^^^^^^^^^^^

To make use of the container templates, select a template from the
top-hand dropdown menu and click ``Get``. This will populate all form fields
that are set in the template with you create form. Anything you already
entered will be overwritten. The prefix ``[Site-wide]`` or ``[Project-wide]``
indicates whether this template is either a site-wide or a project-wide
template.

...

Container path
^^^^^^^^^^^^^^^^^^^

[ XXX: explain why one would want to set up the container path ]

Timeout [s]
^^^^^^^^^^^^^^^^^^^

[ XXX: explain what this is used for by kiosc; the description is "Interval
in seconds for any Docker action to be performed." but that is not helpful ]

Heartbeat URL
^^^^^^^^^^^^^^^^^^^

The heartbeat URL can be used to check whether the container app runs
correctly. [ XXX: describe how this URL should look like – relative to
kiosc? relative to docker? (e.g. localhost:8080, or
kiosc.bihealth.org/containers/proxy/xxxxxx/heartbeat.html ?)]

Max retries
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Maximal number of retries for an action in case of failure. If an action
(e.g. starting container) fails, it will be retried this many times.

Inactivity Threshold [days]
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Number of days the container is allowed to run without proxy access.

[ XXX: describe what happens when the threshold is done. Is it stopped?
paused? ]

Controls
--------

The ``Controls`` dropdown menu (cog icon) comprises
multiple actions that can be issued on a container,
displayed depending on the state the container is currently in.
In the details page this menu is presented by the cog icon + ``Controls``,
while in the list this is presented by the cog icon only.

Start
^^^^^

Create a container from a Docker image and start it.  If the image isn't
yet cached, it is pulled from the specified repository.  An existing
container is always wiped before performing the starting action.

Internally, the following cadence is performed::

    docker rm
    docker pull
    docker create
    docker run

The state should be **running** when performed successfully.

Stop
^^^^

Stop a running Docker container. Only available when Docker container state is reported as running.

Internally, a ``docker stop`` is performed.

The state should be **exited** when performed successfully.

Pause
^^^^^

Pause a running Docker container. Only available when Docker container state is reported as running.

Internally, a ``docker pause`` is performed.

The state should be **paused** when performed successfully.

Unpause
^^^^^^^

Unpause a paused Docker container. Only available when Docker container state is reported as paused.

A ``docker unpause`` is performed.

The state should be **running** when performed successfully.

Restart
^^^^^^^

Restart a running container. Only available when Docker container state is reported as running.

Internally, the following cadence is performed::

    docker stop
    docker rm
    docker pull
    docker create
    docker start

(It's NOT a ``docker restart`` as the name would suggest.)

The state should be **running** when performed successfully.

Update
^^^^^^

This leads to the form to update the setting of the current container.
Please note that values of items in the ``environment`` dictionary are
displayed as ``<masked>`` if listed in the ``environment_secret_keys``.
When left as ``<masked>``, the value itself will not change. To set a
new value, simply change the value.

If the Docker container state is reported as running, a restart as
described above will be performed to account for the changes.

Delete
^^^^^^

This makes sure that the associated Docker container is not running
and stops it if necessary, and deletes the Docker container as well
as the database object. This action can't be undone.
