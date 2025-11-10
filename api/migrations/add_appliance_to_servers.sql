-- Migration: Add appliance relationship to server_configs
-- Date: 2025-11-06
-- Description: Add appliance_id and cache storage fields to link servers to LZ migrate projects

-- Add new columns to server_configs table
ALTER TABLE server_configs
ADD COLUMN IF NOT EXISTS appliance_id INTEGER,
ADD COLUMN IF NOT EXISTS cache_storage_account VARCHAR(255),
ADD COLUMN IF NOT EXISTS cache_storage_rg VARCHAR(255);

-- Create index on appliance_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_server_appliance ON server_configs(appliance_id);

-- Add comments for documentation
COMMENT ON COLUMN server_configs.appliance_id IS 'Reference ID to landing zone migrate project appliance';
COMMENT ON COLUMN server_configs.cache_storage_account IS 'Cache storage account name (auto-populated from LZ)';
COMMENT ON COLUMN server_configs.cache_storage_rg IS 'Cache storage resource group (auto-populated from LZ)';

COMMIT;
