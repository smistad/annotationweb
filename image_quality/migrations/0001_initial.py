# Generated by Django 2.2.22 on 2023-03-02 08:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('annotationweb', '0007_auto_20230202_1054'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image_position_x', models.PositiveIntegerField(default=0)),
                ('image_position_y', models.PositiveIntegerField(default=0)),
                ('placeholder_text', models.CharField(default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Rank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=255)),
                ('color', models.CharField(default='', max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Ranking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotationweb.KeyFrameAnnotation')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_quality.Category')),
                ('selection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_quality.Rank')),
            ],
        ),
        migrations.CreateModel(
            name='ImageQualityTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.ImageField(upload_to='')),
                ('task', models.ManyToManyField(to='annotationweb.Task')),
            ],
        ),
        migrations.AddField(
            model_name='category',
            name='iq_task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_quality.ImageQualityTask'),
        ),
        migrations.AddField(
            model_name='category',
            name='rankings',
            field=models.ManyToManyField(to='image_quality.Rank'),
        ),
    ]
