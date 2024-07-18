from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0025_update_projects_with_referred_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='investmentproject',
            name='status',
            field=models.CharField(choices=[('ongoing', 'Ongoing'), ('delayed', 'Delayed'), ('dormant', 'Dormant'), ('lost', 'Lost'), ('abandoned', 'Abandoned'), ('won', 'Won')], default='ongoing', max_length=255),
        ),
    ]
