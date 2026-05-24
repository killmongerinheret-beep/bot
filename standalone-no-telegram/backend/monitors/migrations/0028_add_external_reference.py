"""
Migration to add external_reference and created_via fields to MonitorTask
Allows linking tasks to external systems (Google Sheets, Bokun, etc.)
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitors', '0027_add_google_sheet_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitortask',
            name='external_reference',
            field=models.CharField(
                max_length=100,
                null=True,
                blank=True,
                db_index=True,
                help_text='External reference ID (e.g., REQ-001 from Google Sheets, Bokun booking ID)'
            ),
        ),
        migrations.AddField(
            model_name='monitortask',
            name='created_via',
            field=models.CharField(
                max_length=50,
                default='manual',
                help_text='How this task was created: manual, telegram, google_sheets, bokun, api'
            ),
        ),
    ]
