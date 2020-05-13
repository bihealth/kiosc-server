=========
CHANGELOG
=========

-----------------
HEAD (unreleased)
-----------------

End-User Summary
================

- More complete display of image details.
- Fix for repository user name / password change.
- Fix permissions for viewing log results.
- Allowing non-superusers (contributors and above) to pull images (#1).
- Disabling autocomplete in user/password fields for image (#3).
- Allow clearing of credentials (#4).

Full Change List
================

- Displaying image ID on docker app detail page.
- Fixing saving of password and repository login in general.
- Fixing favicon.
- Setting default admin user.
- Properly installing versioneer.
- Fix ``rules.py`` for users to view background jobs.
- Fixing problem with environment creation.
- Hopefully fixing periodic tasks.
- Bumping Docker timeout.
- Fixing websocket proxying.
- Nightly pruning of unused objects (#6).
- Updating SODAR Core dependencies.
- Fixing bug in ulimit setting (#9).
- Properly handle containers stopping/failing outside of Kiosc control (#5).
- Allowing non-superusers (contributors and above) to pull images (#1).
- Disabling autocomplete in user/password fields for image (#3).
- Allow clearing of credentials (#4).
- Adding Sentry support (#11).
- Upgrading SODAR-core to v0.8.1.

------
v0.1.0
------

Initial release.
Everything is new!
