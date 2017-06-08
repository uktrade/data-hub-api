#!/bin/bash -xe
# Auth tests have to be run using the pytest live_server fixture. The live server is spawned in the background in a different thread
# For some obscure reason all the tests that run after the auth ones get stuck into using this different thread process
# which doesn't have any access to the testing db hence there are no fixtures and the tests fail.
# The solution is to run the auth tests independently.
pytest --ds=config.settings.test -k liveserver
