-- Add appliance_name and migrate_project_name columns to server_configs
-- These store the actual names instead of relying on array index lookups

ALTER TABLE server_configs
ADD COLUMN IF NOT EXISTS appliance_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS migrate_project_name VARCHAR(255);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_server_appliance_name ON server_configs(appliance_name);
CREATE INDEX IF NOT EXISTS idx_server_migrate_project ON server_configs(migrate_project_name);

-- Migrate existing data: populate names from appliance_id if possible
-- This is a placeholder - actual migration would need to look up the names from metadata_json
COMMENT ON COLUMN server_configs.appliance_id IS 'Deprecated: Use appliance_name instead';
