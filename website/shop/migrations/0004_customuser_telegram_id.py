# Generated by Django 5.1.6 on 2025-03-12 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_order_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='telegram_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Telegram ID'),
        ),
    ]
