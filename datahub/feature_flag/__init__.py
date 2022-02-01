"""
Feature flag functionality.

Feature flags are used to control whether a piece of new functionality is visible
to a user. They're usually used to hide functionality from users when it's not yet
ready to be used.

They can be added and toggled via the admin site and are exposed by a view
so the front end can check that status of each flag.

They're also sometimes checked in the back end, but this is less common.
"""
