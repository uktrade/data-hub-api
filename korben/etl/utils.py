import collections


def fkey_deps(metadata):
    dependencies = collections.defaultdict(set)
    added = set()
    depth = 0
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
            # if deps are all added to previous (less deep) depths, we are deep
            # enough to add this table; do so
            lesser_deps = set()
            for lesser_depth in range(0, depth):
                lesser_deps = lesser_deps.union(dependencies[lesser_depth])
            if table_deps.issubset(lesser_deps):
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
