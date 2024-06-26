# Generated by Django 4.2.11 on 2024-05-22 15:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0043_alter_win_sector'),
    ]

    operations = [
        migrations.AlterField(
            model_name='win',
            name='hq_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='wins', to='export_win.hqteamregionorpost', verbose_name='HQ team, Region or Post'),
        ),
    ]
