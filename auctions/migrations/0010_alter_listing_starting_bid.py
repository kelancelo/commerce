# Generated by Django 4.1.1 on 2022-10-09 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0009_rename_photo_listing_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='starting_bid',
            field=models.PositiveIntegerField(),
        ),
    ]
