# Generated by Django 5.0.4 on 2024-05-24 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction', '0004_alter_participant_new_price_alter_product_min_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session_date',
            name='date',
            field=models.TimeField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='sub_category',
            name='name',
            field=models.DateField(max_length=100, null=True),
        ),
    ]