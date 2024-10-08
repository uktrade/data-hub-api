# Generated by Django 4.2.15 on 2024-09-25 10:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0013_auto_20210922_1706'),
        ('omis_payment', '0009_auto_20210816_1601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='order.order'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='order.order'),
        ),
    ]
