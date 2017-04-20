import collections
import itertools
from django.apps import apps
from django.db.models.fields.related import ForeignKey
from . import spec

model_apps = ['company', 'interaction', 'metadata']
models = itertools.chain.from_iterable(
    apps.get_app_config(name).models.values() for name in model_apps
)

def yield_fkeys(Model):
    mapping = spec.get_mapping(Model)
    for field in Model._meta.get_fields():
        if isinstance(field, ForeignKey) and field.column in mapping:
            if len(field.foreign_related_fields) > 1:
                raise Exception('Composite foreign keys are not supported')
            yield field.foreign_related_fields[0].model


def fkey_deps(models):
    if not isinstance(models, set):
        raise Exception('Pass a set of models')
    dependencies = collections.defaultdict(set)
    added = set()
    depth = 0
    # run until we've covered all models
    while len(added) < len(models):
        remaining = filter(lambda x: x not in added, models)
        for Model in remaining:
            model_deps = set(yield_fkeys(Model))
            if model_deps.difference(models):
                msg = '{0} is a dependency of {1} but is not being passed'
                raise Exception(msg.format(model_deps.pop(), Model))
            # if deps are all added to previous (less deep) depths, we are deep
            # enough to add this model; do so
            lesser_deps = set()
            for lesser_depth in range(0, depth):
                lesser_deps = lesser_deps.union(dependencies[lesser_depth])
            if model_deps.issubset(lesser_deps):
                dependencies[depth].add(Model)
                added.add(Model)
        depth += 1
        # bail if it gets too heavy
        if depth > 10:
            raise Exception('fkey deps are too deep')
    return dependencies
