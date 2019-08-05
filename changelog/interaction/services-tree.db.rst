The following columns were added to ``metadata_service`` table to transform flat services list into a tree structure:
 - segment (character varying(255)) not null
 - level (integer) not null
 - lft (integer) not null
 - parent_id (uuid)
 - rght (integer) not null
 - tree_id (integer) not null

Columns ``level``, ``lft``, ``rght``, ``tree_id`` are being used by ``django-mptt`` library to manage the tree structure.

The ``parent_id`` field points at the parent service.

At present only the leaf nodes are being used as interaction's service foreign keys.
