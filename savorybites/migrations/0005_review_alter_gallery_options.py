# Generated by Django 5.2 on 2025-05-19 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savorybites', '0004_gallery'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=100)),
                ('customer_occupation', models.CharField(max_length=100)),
                ('rating', models.CharField(choices=[('1', '1 Star'), ('2', '2 Stars'), ('3', '3 Stars'), ('4', '4 Stars'), ('5', '5 Stars')], default='3', max_length=15)),
                ('comment', models.TextField()),
                ('review_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='gallery',
            options={'verbose_name_plural': 'Gallery'},
        ),
    ]
