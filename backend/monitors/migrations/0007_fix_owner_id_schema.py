
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('monitors', '0006_agency_plan_monitortask_ticket_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitors_agency' AND column_name='owner_id') THEN
                    ALTER TABLE monitors_agency ADD COLUMN owner_id varchar(100);
                    RAISE NOTICE 'Added owner_id column';
                END IF;
            END
            $$;
            """,
            reverse_sql="ALTER TABLE monitors_agency DROP COLUMN IF EXISTS owner_id;"
        ),
    ]
