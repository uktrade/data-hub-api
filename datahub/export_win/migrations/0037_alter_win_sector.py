# Generated by Django 4.2.10 on 2024-04-05 12:12

from django.db import migrations
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0036_hvc_2024_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='win',
            name='sector',
            field=mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='wins', to='metadata.sector'),
        ),
    ]