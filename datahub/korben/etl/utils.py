import collections
from . import spec


def fkey_deps(metadata):
    dependencies = collections.defaultdict(set)
    added = set()
    depth = 0
    # run until we've covered all tables
    tables = {
        name: table for name, table in metadata.tables.items()
        if name in spec.DJANGO_LOOKUP
    }
    while len(added) < len(tables):
        remaining = filter(
            lambda x: x[0] not in added,  # table_name isn't added
            tables.items()
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
