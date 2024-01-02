# Generated by Django 3.2.23 on 2023-12-30 06:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0027_alter_userrequest_eventid'),
    ]

    operations = [
        migrations.AddField(
            model_name='userresponse',
            name='eventId',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schedule.event'),
        ),
        migrations.AlterField(
            model_name='userresponse',
            name='userData',
            field=models.DateField(default='2023-01-14', null=True),
        ),
    ]