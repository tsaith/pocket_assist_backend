#!/bin/bash

# Check if the parameter is passed
if [ $# -eq 0 ]; then
  echo "Usage: $(basename "$0") <MIGRATION_NAME>"
  echo ""
  echo "Example:"
  echo "  $(basename "$0") add_users_table"
  echo "  $(basename "$0") modify_chatbots_table"
  exit 1
fi

# Get the migration name parameter
MIGRATION_NAME=$1

# Execute the supabase db diff command
echo "Generating migration file: $MIGRATION_NAME..."
npx supabase db diff -f "$MIGRATION_NAME" --schema auth,public
