# Generated by Django 5.2 on 2025-06-14 05:18

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savorybites', '0015_remove_profile_preferred_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
