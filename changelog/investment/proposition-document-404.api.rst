The following endpoints were corrected to return a 404 when a non-existent investment project or proposition was specified:

- ``GET,POST /v3/investment/{project_pk}/proposition/{proposition_pk}/document``
- ``GET,DELETE /v3/investment/{project_pk}/proposition/{proposition_pk}/document/{entity_document_pk}``
- ``GET /v3/investment/{project_pk}/proposition/{proposition_pk}/document/{entity_document_pk}/download``
- ``POST /v3/investment/{project_pk}/proposition/{proposition_pk}/document/{entity_document_pk}/upload-callback``

(Previously, they would only return a 404 in some of the possible cases.)
