import collections
from korben import config, services


def fkey_deps(metadata):
    dependencies = collections.defaultdict(set)
    added = set()
    # tables with no fkeys
    for table_name in metadata.tables:
        if len(metadata.tables[table_name].foreign_keys) == 0:
            dependencies[0].add(table_name)
            added.add(table_name)
    depth = 1
    # run until we've covered all tables
    while len(added) < len(metadata.tables):
        remaining = filter(
            lambda x: x[0] not in added,  # table_name isn't added
            metadata.tables.items()
        )
        for table_name, table in remaining:
            table_deps = set([
                fkey.column.table.name for fkey in table.foreign_keys
            ])
            # if deps are all added, we are deep enough for this table; add it
            if table_deps.issubset(added.union({table_name})):
                dependencies[depth].add(table_name)
                added.add(table_name)
        depth += 1
        # bail if it gets too heavy
        if depth > 10:
            raise Exception('fkey deps are too deep')
    return dependencies


def primary_key(table):
    'Return name of primary key for given table, raises if pkey is composite'
    if len(table.primary_key.columns) > 1:
        raise Exception('Composite primary keys are not supported')
    return next(col.name for col in table.primary_key.columns.values())
