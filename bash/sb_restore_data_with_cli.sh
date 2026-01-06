CONNECTION_STRING="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
BACKUP_DIR="supabase/backup"

# Restore data only
psql \
  --single-transaction \
  --variable ON_ERROR_STOP=1 \
  --command 'SET session_replication_role = replica' \
  --file $BACKUP_DIR/data.sql \
  --dbname $CONNECTION_STRING


# Restore roles, schema, and data
#psql \
#  --single-transaction \
#  --variable ON_ERROR_STOP=1 \
#  --file $BACKUP_DIR/roles.sql \
#  --file $BACKUP_DIR/schema.sql \
#  --command 'SET session_replication_role = replica' \
#  --file $BACKUP_DIR/data.sql \
#  --dbname $CONNECTION_STRING