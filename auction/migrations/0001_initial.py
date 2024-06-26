# Generated by Django 5.0.1 on 2024-05-05 13:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Member_fee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fee', models.CharField(max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pay', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('temp', models.IntegerField(null=True)),
                ('name', models.CharField(max_length=100, null=True)),
                ('min_price', models.IntegerField(null=True)),
                ('images', models.FileField(null=True, upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Session_date',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.CharField(max_length=30, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=30, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dob', models.DateField(null=True)),
                ('address', models.CharField(max_length=100, null=True)),
                ('contact', models.CharField(max_length=10, null=True)),
                ('image', models.FileField(null=True, upload_to='')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('membership', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.member_fee')),
            ],
        ),
        migrations.CreateModel(
            name='Aucted_Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('winner', models.CharField(max_length=100, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.member')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.product')),
            ],
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('new_price', models.IntegerField(null=True)),
                ('aucted_product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.aucted_product')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.member')),
                ('payment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.payment')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.product')),
                ('result', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.result')),
            ],
        ),
        migrations.CreateModel(
            name='Send_Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message1', models.TextField(null=True)),
                ('date', models.CharField(max_length=30, null=True)),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Session_Time',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.CharField(max_length=30, null=True)),
                ('date', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.session_date')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='session',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.session_time'),
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.status'),
        ),
        migrations.CreateModel(
            name='Sub_Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.category')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auction.sub_category'),
        ),
    ]
