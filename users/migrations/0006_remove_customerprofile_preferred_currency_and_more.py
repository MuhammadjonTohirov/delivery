# Generated by Django 5.2.3 on 2025-06-15 17:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_customerprofile_preferred_currency_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customerprofile',
            name='preferred_currency',
        ),
        migrations.RemoveField(
            model_name='restaurantprofile',
            name='preferred_currency',
        ),
    ]
