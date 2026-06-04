from django.db import migrations


def fix_admin_log_fk(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        r"""
DO $$
DECLARE
    conname text;
BEGIN
    -- find any FK on django_admin_log.user_id that references auth_user
    SELECT tc.constraint_name INTO conname
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.constraint_schema = kcu.constraint_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name AND ccu.constraint_schema = tc.constraint_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = 'django_admin_log'
      AND kcu.column_name = 'user_id'
      AND ccu.table_name = 'auth_user'
    LIMIT 1;

    IF conname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE django_admin_log DROP CONSTRAINT %I', conname);
    END IF;

    -- create FK to users_user if it does not already exist
    PERFORM 1 FROM information_schema.table_constraints tc
    WHERE tc.table_name = 'django_admin_log' AND tc.constraint_type = 'FOREIGN KEY'
      AND EXISTS (
          SELECT 1 FROM information_schema.key_column_usage kcu
          WHERE kcu.constraint_name = tc.constraint_name AND kcu.column_name = 'user_id'
      );

    -- Add constraint referencing the custom user model
    BEGIN
        EXECUTE 'ALTER TABLE django_admin_log ADD CONSTRAINT django_admin_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES users_user(id) DEFERRABLE INITIALLY DEFERRED';
    EXCEPTION WHEN duplicate_object THEN
        -- constraint already exists, ignore
        NULL;
    END;
END$$;
"""
    )


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fix_admin_log_fk, migrations.RunPython.noop),
    ]
