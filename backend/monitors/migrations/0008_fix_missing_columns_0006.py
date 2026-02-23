
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('monitors', '0007_fix_owner_id_schema'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- Fix Agency.plan
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitors_agency' AND column_name='plan') THEN
                    ALTER TABLE monitors_agency ADD COLUMN plan varchar(20) DEFAULT 'free' NOT NULL;
                    RAISE NOTICE 'Added plan column to monitors_agency';
                END IF;

                -- Fix MonitorTask.ticket_id
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitors_monitortask' AND column_name='ticket_id') THEN
                    ALTER TABLE monitors_monitortask ADD COLUMN ticket_id varchar(255) NULL;
                    CREATE INDEX monitors_monitortask_ticket_id_idx ON monitors_monitortask(ticket_id);
                    RAISE NOTICE 'Added ticket_id column to monitors_monitortask';
                END IF;

                -- Fix MonitorTask.ticket_label
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitors_monitortask' AND column_name='ticket_label') THEN
                    ALTER TABLE monitors_monitortask ADD COLUMN ticket_label varchar(255) NULL;
                    RAISE NOTICE 'Added ticket_label column to monitors_monitortask';
                END IF;

                -- Fix MonitorTask.ticket_name
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitors_monitortask' AND column_name='ticket_name') THEN
                    ALTER TABLE monitors_monitortask ADD COLUMN ticket_name varchar(300) NULL;
                    RAISE NOTICE 'Added ticket_name column to monitors_monitortask';
                END IF;

                -- Fix MonitorTask.tier
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitors_monitortask' AND column_name='tier') THEN
                    ALTER TABLE monitors_monitortask ADD COLUMN tier varchar(20) DEFAULT 'monitor' NOT NULL;
                    RAISE NOTICE 'Added tier column to monitors_monitortask';
                END IF;
            END
            $$;
            """,
            reverse_sql="""
            ALTER TABLE monitors_agency DROP COLUMN IF EXISTS plan;
            ALTER TABLE monitors_monitortask DROP COLUMN IF EXISTS ticket_id;
            ALTER TABLE monitors_monitortask DROP COLUMN IF EXISTS ticket_label;
            ALTER TABLE monitors_monitortask DROP COLUMN IF EXISTS ticket_name;
            ALTER TABLE monitors_monitortask DROP COLUMN IF EXISTS tier;
            """
        ),
    ]
