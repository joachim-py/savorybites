# Generated by Django 5.2 on 2025-06-12 10:38

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savorybites', '0011_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
