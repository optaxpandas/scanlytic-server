# Generated by Django 5.1.6 on 2025-03-02 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0005_alter_table_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='qr',
            name='extracted_data',
        ),
        migrations.AddField(
            model_name='qr',
            name='first_submission_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qr',
            name='harmless',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='last_analysis_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qr',
            name='malicious',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='reputation',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='risk_level',
            field=models.CharField(choices=[('safe', 'Safe'), ('critical', 'Critical'), ('risky', 'Risky')], default='safe', max_length=10),
        ),
        migrations.AddField(
            model_name='qr',
            name='security_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='suspicious',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='total_harmless_votes',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='total_malicious_votes',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='qr',
            name='url',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='qr',
            name='image',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='table',
            name='image',
            field=models.CharField(max_length=255),
        ),
        migrations.DeleteModel(
            name='QRReport',
        ),
    ]
