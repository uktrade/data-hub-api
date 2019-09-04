This directory contains "newsfragments" which are short files that contain a small **ReST**-formatted
text that will be added to the next ``CHANGELOG``.

Make sure to use full sentences with correct case, punctuation and avoid starting with verbs. For example::

    BAD
    Allow people to export search results.
    Added the ability to export search results.

    GOOD
    It's now possible to export search results as a CSV file.


Each file should be named like ``<SLUG>.<TYPE>.rst``, where:

``<SLUG>`` is ignored in the compiled ``CHANGELOG`` but it has to be unique within a changelog folder
and should not contain any full stops. A good candidate would be your branch name.

``<TYPE>`` is one of:

* ``feature``: new features or changes.
* ``bugfix``: fixes a bug.
* ``removal``: removal of deprecated feature. API related news should also have an equivalent .api entry.
* ``deprecation``: feature deprecation. API related news should also have an equivalent .api entry. Include an
  earliest date for the actual removal of the feature when possible, and details of any other relevant upcoming changes.
* ``internal``: internal changes e.g. dependencies updated, test data updated etc.
* ``api``: any changes to the API. Removals and deprecations should also have an equivalent .removal or .deprecation entry.
  Include upcoming changes when possible.
* ``db``: any changes to the database schema.

Newsfragments should be added to the changelog subfolder related to the application but it's okay if
it isn't always possible (e.g. for internal changes).

So for example:

File ``investment/document-upload.feature.rst`` with content::

    New models for evidence documents (endpoints to follow in a future release)

File ``investment/document-upload.db.rst`` with content::

    New tables ``evidence_evidence_document`` and ``evidence_evidence_tag``

``towncrier`` preserves multiple paragraphs and formatting (code blocks, lists, and so on), but for entries
other than ``features`` it is usually better to stick to a single paragraph to keep it concise. You can
run ``towncrier --draft --version dev`` if you want to get a preview of how your change
will look in the final release notes.

When it's time to prepare a release run::

    towncrier --version x.x.x

This will git rm all newsfragments and compile a new ``CHANGELOG.rst``.
Note that towncrier does not push the changes.
