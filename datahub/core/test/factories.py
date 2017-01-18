import uuid

import factory


class TaskInfoFactory(factory.django.DjangoModelFactory):
    """TaskInfo factory."""

    task_id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    name = factory.Sequence(lambda x: 'name-{0}'.format(x))
    changes = {'foo': 'bar'}
    update = True
    db_table = 'hello'

    class Meta:
        model = 'core.TaskInfo'
