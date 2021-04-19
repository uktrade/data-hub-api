from django.conf import settings
from django.db import migrations


def populate_user_feature_flags(apps, schema_editor):
    """
    Add the personalised dashboard feature flag.
    """
    UserFeatureFlag = apps.get_model('feature_flag', 'UserFeatureFlag')
    UserFeatureFlag.objects.create(code='personalised-dashboard')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feature_flag', '0002_user_feature_flag'),
    ]

    operations = [
        migrations.RunPython(populate_user_feature_flags, migrations.RunPython.noop)
    ]
