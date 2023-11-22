# Generated by Django 4.2.4 on 2023-10-04 05:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopapp', '0010_creator_remove_product_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creator',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shopapp.product'),
        ),
    ]