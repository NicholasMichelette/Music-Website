# Generated by Django 3.1.6 on 2021-04-01 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommender', '0002_auto_20210401_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='artist',
            name='follows',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='musicdata',
            name='likes',
            field=models.IntegerField(default=0),
        ),
    ]
