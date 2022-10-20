# Generated by Django 4.1.1 on 2022-10-07 09:23

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_watchlist_unique watcher-listing'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='current_price',
        ),
        migrations.AddField(
            model_name='listing',
            name='watchers',
            field=models.ManyToManyField(blank=True, related_name='watchlist', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='WatchList',
        ),
    ]