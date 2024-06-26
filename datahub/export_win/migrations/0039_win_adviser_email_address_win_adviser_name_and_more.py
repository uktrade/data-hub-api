# Generated by Django 4.2.10 on 2024-05-02 08:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0141_auto_20240222_1534'),
        ('export_win', '0038_alter_winadviser_options_win_migrated_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='win',
            name='adviser_email_address',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Adviser email address'),
        ),
        migrations.AddField(
            model_name='win',
            name='adviser_name',
            field=models.CharField(blank=True, help_text='This is the name of the adviser who created the Win', max_length=128, verbose_name='Adviser name'),
        ),
        migrations.AlterField(
            model_name='breakdown',
            name='year',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='win',
            name='adviser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='wins', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='win',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='wins', to='company.company'),
        ),
        migrations.AlterField(
            model_name='win',
            name='lead_officer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lead_officer_wins', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='winadviser',
            name='adviser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='win_advisers', to=settings.AUTH_USER_MODEL),
        ),
    ]
