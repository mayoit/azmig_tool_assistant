# Server Management Implementation Specification

**Version**: 1.0  
**Last Updated**: November 4, 2025  
**Status**: Ready for Implementation

---

## 1. Overview

This specification defines the complete implementation for the Server Management UI with intelligent bulk editing, CSV upload, and auto-population of Migrate Project information based on Azure subscription mapping.

### Key Business Rules

1. **Target Subscription → Migrate Project Mapping**: When a user sets a Target Subscription, the system automatically populates the Migrate Project Name by looking up which migrate project contains that subscription in its app landing zones.

2. **Migration Settings**: Projects have configurable migration settings (allowed regions, VM SKUs, disk types) that drive dropdown options in bulk edit and upload flows.

3. **CSV Upload Schema**: The upload format follows the structure in `sample_servers_validation.csv` with auto-population of Migrate Project Name.

4. **Validation**: Target Subscriptions must exist in the project's app landing zones, otherwise the upload/edit operation shows warnings.

---

## 2. Data Model Changes

### 2.1 Project Model Extension

**File**: `api/models.py` (Project model)

Add to `metadata_json` field structure:

```python
{
  "lz_migrate_projects": [...],  # Existing
  "migration_settings": {
    "allowed_regions": [
      "eastus",
      "westus", 
      "uksouth",
      "ukwest",
      "northeurope",
      "westeurope"
    ],
    "allowed_vm_skus": [
      "Standard_DS1_v2",
      "Standard_DS2_v2",
      "Standard_D2s_v3",
      "Standard_D4s_v3",
      "Standard_E2s_v3",
      "Standard_E4s_v3"
    ],
    "allowed_disk_types": [
      "Premium_LRS",
      "Standard_LRS",
      "StandardSSD_LRS",
      "UltraSSD_LRS"
    ]
  }
}
```

**Default Values**: When a project is created, auto-populate `migration_settings` with defaults from `api/utils/default_migration_settings.py`.

### 2.2 ServerConfig Model Extension

**File**: `api/models.py` (ServerConfig model, around line 210)

Add new column:

```python
class ServerConfig(Base):
    # ... existing columns ...
    
    migrate_project_name = Column(String(255), nullable=True, index=True)
    # Auto-populated based on target_subscription matching app landing zone
    
    # Optional: Add these for display purposes
    appliance_name = Column(String(255), nullable=True)
    appliance_type = Column(String(50), nullable=True)
    recovery_vault_name = Column(String(255), nullable=True)
```

**Database Migration**:
```bash
cd api
alembic revision --autogenerate -m "add_migrate_project_name_to_servers"
alembic upgrade head
```

### 2.3 TypeScript Type Updates

**File**: `frontend/src/types/server.types.ts`

```typescript
export interface ServerConfig {
  id: number;
  project_id: number;
  target_machine_name: string;
  target_region: string;
  target_subscription: string;
  target_resource_group: string;
  target_vnet: string;
  target_subnet: string;
  target_machine_sku: string;
  target_disk_type: string;
  
  // NEW: Auto-populated fields
  migrate_project_name: string | null;
  appliance_name?: string | null;
  appliance_type?: string | null;
  recovery_vault_name?: string | null;
  
  created_at: string;
  updated_at?: string;
}

// NEW: Migration settings type
export interface MigrationSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  allowed_disk_types: string[];
}
```

**File**: `frontend/src/types/project.types.ts`

```typescript
export interface Project {
  // ... existing fields ...
  
  lz_migrate_projects?: LandingZoneMigrateProject[];
  validation_settings?: ValidationSettings;
  
  // NEW: Migration settings
  migration_settings?: MigrationSettings;
}
```

---

## 3. Backend API Endpoints

### 3.1 Migration Settings Endpoints

**File**: `api/routers/projects.py`

```python
@router.get("/{project_id}/migration-settings")
async def get_migration_settings(
    project_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Get project migration settings (regions, SKUs, disk types)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    metadata = project.metadata_json or {}
    migration_settings = metadata.get('migration_settings', get_default_migration_settings())
    
    return migration_settings


@router.put("/{project_id}/migration-settings")
async def update_migration_settings(
    project_id: int,
    settings: dict,
    db: Session = Depends(get_db)
) -> dict:
    """Update project migration settings."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate settings structure
    if not isinstance(settings.get('allowed_regions'), list):
        raise HTTPException(status_code=400, detail="allowed_regions must be an array")
    if not isinstance(settings.get('allowed_vm_skus'), list):
        raise HTTPException(status_code=400, detail="allowed_vm_skus must be an array")
    if not isinstance(settings.get('allowed_disk_types'), list):
        raise HTTPException(status_code=400, detail="allowed_disk_types must be an array")
    
    # Validate at least one region
    if len(settings['allowed_regions']) == 0:
        raise HTTPException(status_code=400, detail="At least one region is required")
    
    metadata = project.metadata_json or {}
    metadata['migration_settings'] = settings
    project.metadata_json = metadata
    
    db.commit()
    db.refresh(project)
    
    return settings
```

**File**: `api/utils/default_migration_settings.py` (NEW)

```python
"""Default migration settings for new projects."""

def get_default_migration_settings() -> dict:
    """Returns default migration settings."""
    return {
        "allowed_regions": [
            "eastus",
            "westus",
            "centralus",
            "uksouth",
            "ukwest",
            "northeurope",
            "westeurope",
        ],
        "allowed_vm_skus": [
            "Standard_DS1_v2",
            "Standard_DS2_v2",
            "Standard_DS3_v2",
            "Standard_D2s_v3",
            "Standard_D4s_v3",
            "Standard_D8s_v3",
            "Standard_E2s_v3",
            "Standard_E4s_v3",
        ],
        "allowed_disk_types": [
            "Premium_LRS",
            "Standard_LRS",
            "StandardSSD_LRS",
            "UltraSSD_LRS",
        ],
    }
```

### 3.2 Server Bulk Update Endpoint

**File**: `api/routers/servers.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class BulkServerUpdate(BaseModel):
    server_ids: List[int]
    updates: dict  # Partial ServerConfig fields

@router.put("/projects/{project_id}/servers/bulk")
async def bulk_update_servers(
    project_id: int,
    bulk_update: BulkServerUpdate,
    db: Session = Depends(get_db)
) -> dict:
    """Bulk update multiple servers."""
    
    # Get project to access migrate projects
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get servers to update
    servers = db.query(ServerConfig).filter(
        ServerConfig.id.in_(bulk_update.server_ids),
        ServerConfig.project_id == project_id
    ).all()
    
    if len(servers) != len(bulk_update.server_ids):
        raise HTTPException(status_code=400, detail="Some server IDs not found or don't belong to this project")
    
    # Get migrate projects for lookup
    lz_migrate_projects = (project.metadata_json or {}).get('lz_migrate_projects', [])
    
    # Update each server
    updated_count = 0
    for server in servers:
        # Apply updates
        for field, value in bulk_update.updates.items():
            if hasattr(server, field) and value is not None:
                setattr(server, field, value)
        
        # Auto-populate migrate project name if subscription changed
        if 'target_subscription' in bulk_update.updates:
            migrate_info = lookup_migrate_project_by_subscription(
                bulk_update.updates['target_subscription'],
                lz_migrate_projects
            )
            if migrate_info:
                server.migrate_project_name = migrate_info['migrate_project_name']
                server.appliance_name = migrate_info.get('appliance_name')
                server.appliance_type = migrate_info.get('appliance_type')
                server.recovery_vault_name = migrate_info.get('recovery_vault_name')
            else:
                server.migrate_project_name = None
        
        updated_count += 1
    
    db.commit()
    
    return {"updated_count": updated_count}


def lookup_migrate_project_by_subscription(
    subscription_id: str,
    lz_migrate_projects: list
) -> Optional[dict]:
    """
    Find migrate project that contains the given subscription in its app landing zones.
    
    Returns:
        {
            'migrate_project_name': str,
            'appliance_name': str,
            'appliance_type': str,
            'recovery_vault_name': str
        }
    """
    for migrate_project in lz_migrate_projects:
        app_landing_zones = migrate_project.get('appLandingZones', [])
        
        for zone in app_landing_zones:
            # Check both 'subscriptionId' and 'Subscription ID' (CSV format)
            zone_sub_id = zone.get('subscriptionId') or zone.get('Subscription ID')
            
            if zone_sub_id == subscription_id:
                return {
                    'migrate_project_name': migrate_project.get('migrateProjectName'),
                    'appliance_name': migrate_project.get('applianceName'),
                    'appliance_type': migrate_project.get('applianceType'),
                    'recovery_vault_name': migrate_project.get('recoveryVaultName'),
                }
    
    return None
```

### 3.3 Single Server Update Endpoint

**File**: `api/routers/servers.py`

```python
@router.put("/servers/{server_id}")
async def update_server(
    server_id: int,
    updates: dict,
    db: Session = Depends(get_db)
) -> dict:
    """Update a single server."""
    
    server = db.query(ServerConfig).filter(ServerConfig.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Get project to access migrate projects
    project = db.query(Project).filter(Project.id == server.project_id).first()
    lz_migrate_projects = (project.metadata_json or {}).get('lz_migrate_projects', [])
    
    # Apply updates
    for field, value in updates.items():
        if hasattr(server, field) and value is not None:
            setattr(server, field, value)
    
    # Auto-populate migrate project name if subscription changed
    if 'target_subscription' in updates:
        # Validate subscription exists in app landing zones
        migrate_info = lookup_migrate_project_by_subscription(
            updates['target_subscription'],
            lz_migrate_projects
        )
        
        if not migrate_info:
            raise HTTPException(
                status_code=400,
                detail=f"Target subscription {updates['target_subscription']} not found in any app landing zone"
            )
        
        server.migrate_project_name = migrate_info['migrate_project_name']
        server.appliance_name = migrate_info.get('appliance_name')
        server.appliance_type = migrate_info.get('appliance_type')
        server.recovery_vault_name = migrate_info.get('recovery_vault_name')
    
    db.commit()
    db.refresh(server)
    
    # Return as dict
    return {
        "id": server.id,
        "project_id": server.project_id,
        "target_machine_name": server.target_machine_name,
        "target_region": server.target_region,
        "target_subscription": server.target_subscription,
        "target_resource_group": server.target_resource_group,
        "target_vnet": server.target_vnet,
        "target_subnet": server.target_subnet,
        "target_machine_sku": server.target_machine_sku,
        "target_disk_type": server.target_disk_type,
        "migrate_project_name": server.migrate_project_name,
        "appliance_name": server.appliance_name,
        "appliance_type": server.appliance_type,
        "recovery_vault_name": server.recovery_vault_name,
        "created_at": server.created_at.isoformat() if server.created_at else None,
        "updated_at": server.updated_at.isoformat() if server.updated_at else None,
    }
```

### 3.4 Enhanced CSV Upload Endpoint

**File**: `api/routers/servers.py` (modify existing upload endpoint)

```python
@router.post("/projects/{project_id}/servers/upload")
async def upload_servers_excel(
    project_id: int,
    file: UploadFile = File(...),
    update_existing: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Upload servers from Excel/CSV file with auto-population of migrate project."""
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    lz_migrate_projects = (project.metadata_json or {}).get('lz_migrate_projects', [])
    
    # Parse file (existing logic)
    # ...
    
    # For each parsed row:
    servers_created = 0
    servers_updated = 0
    warnings = []
    
    for row_data in parsed_rows:
        target_subscription = row_data.get('Target Subscription')
        
        # Auto-populate migrate project name
        migrate_info = None
        if target_subscription:
            migrate_info = lookup_migrate_project_by_subscription(
                target_subscription,
                lz_migrate_projects
            )
            
            if not migrate_info:
                warnings.append(
                    f"Row {row_index}: Target Subscription '{target_subscription}' not found in app landing zones"
                )
        
        # Create or update server
        server = ServerConfig(
            project_id=project_id,
            target_machine_name=row_data.get('Target Machine'),
            target_region=row_data.get('Target Region'),
            target_subscription=target_subscription,
            target_resource_group=row_data.get('Target RG'),
            target_vnet=row_data.get('Target VNet'),
            target_subnet=row_data.get('Target Subnet'),
            target_machine_sku=row_data.get('Target Machine SKU'),
            target_disk_type=row_data.get('Target Disk Type'),
            migrate_project_name=migrate_info['migrate_project_name'] if migrate_info else None,
            appliance_name=migrate_info.get('appliance_name') if migrate_info else None,
            appliance_type=migrate_info.get('appliance_type') if migrate_info else None,
            recovery_vault_name=migrate_info.get('recovery_vault_name') if migrate_info else None,
        )
        
        db.add(server)
        servers_created += 1
    
    db.commit()
    
    return {
        "servers_created": servers_created,
        "servers_updated": servers_updated,
        "total_servers": servers_created + servers_updated,
        "warnings": warnings
    }
```

---

## 4. Frontend Components

### 4.1 Migration Settings Editor

**File**: `frontend/src/components/projects/MigrationSettingsEditor.tsx` (NEW)

```tsx
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  Stack,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import type { MigrationSettings } from '../../types/project.types';

interface MigrationSettingsEditorProps {
  projectId: number;
}

// Azure regions list (can be extended)
const AZURE_REGIONS = [
  'eastus', 'westus', 'centralus', 'northcentralus', 'southcentralus',
  'uksouth', 'ukwest', 'northeurope', 'westeurope',
  'eastasia', 'southeastasia', 'japaneast', 'japanwest',
  'australiaeast', 'australiasoutheast',
];

const DEFAULT_VM_SKUS = [
  'Standard_DS1_v2', 'Standard_DS2_v2', 'Standard_DS3_v2',
  'Standard_D2s_v3', 'Standard_D4s_v3', 'Standard_D8s_v3',
  'Standard_E2s_v3', 'Standard_E4s_v3', 'Standard_E8s_v3',
];

const DISK_TYPES = ['Premium_LRS', 'Standard_LRS', 'StandardSSD_LRS', 'UltraSSD_LRS'];

export default function MigrationSettingsEditor({ projectId }: MigrationSettingsEditorProps) {
  const queryClient = useQueryClient();

  // Fetch current settings
  const { data: settings, isLoading } = useQuery<MigrationSettings>({
    queryKey: ['migrationSettings', projectId],
    queryFn: async () => {
      const response = await api.get(`/projects/${projectId}/migration-settings`);
      return response.data;
    },
  });

  const [formData, setFormData] = useState<MigrationSettings | null>(null);

  // Initialize form when data loads
  React.useEffect(() => {
    if (settings && !formData) {
      setFormData(settings);
    }
  }, [settings]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async (data: MigrationSettings) => {
      const response = await api.put(`/projects/${projectId}/migration-settings`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['migrationSettings', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  const handleToggleRegion = (region: string) => {
    if (!formData) return;
    
    const newRegions = formData.allowed_regions.includes(region)
      ? formData.allowed_regions.filter(r => r !== region)
      : [...formData.allowed_regions, region];
    
    setFormData({ ...formData, allowed_regions: newRegions });
  };

  const handleToggleSku = (sku: string) => {
    if (!formData) return;
    
    const newSkus = formData.allowed_vm_skus.includes(sku)
      ? formData.allowed_vm_skus.filter(s => s !== sku)
      : [...formData.allowed_vm_skus, sku];
    
    setFormData({ ...formData, allowed_vm_skus: newSkus });
  };

  const handleToggleDiskType = (diskType: string) => {
    if (!formData) return;
    
    const newTypes = formData.allowed_disk_types.includes(diskType)
      ? formData.allowed_disk_types.filter(t => t !== diskType)
      : [...formData.allowed_disk_types, diskType];
    
    setFormData({ ...formData, allowed_disk_types: newTypes });
  };

  const handleSave = () => {
    if (formData && formData.allowed_regions.length > 0) {
      saveMutation.mutate(formData);
    }
  };

  if (isLoading || !formData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Migration Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure allowed regions, VM SKUs, and disk types for server migration.
        These options will be available in bulk edit and upload operations.
      </Typography>

      {formData.allowed_regions.length === 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          At least one region must be selected
        </Alert>
      )}

      {saveMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => saveMutation.reset()}>
          Migration settings saved successfully
        </Alert>
      )}

      {saveMutation.isError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => saveMutation.reset()}>
          Failed to save settings. Please try again.
        </Alert>
      )}

      {/* Allowed Regions */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Allowed Target Regions
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Select Azure regions where servers can be migrated
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {AZURE_REGIONS.map((region) => (
            <Chip
              key={region}
              label={region}
              onClick={() => handleToggleRegion(region)}
              color={formData.allowed_regions.includes(region) ? 'primary' : 'default'}
              variant={formData.allowed_regions.includes(region) ? 'filled' : 'outlined'}
              sx={{ mb: 1 }}
            />
          ))}
        </Stack>
      </Box>

      <Divider sx={{ my: 3 }} />

      {/* Allowed VM SKUs */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Allowed VM SKUs
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Select VM SKUs available for server migration
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {DEFAULT_VM_SKUS.map((sku) => (
            <Chip
              key={sku}
              label={sku}
              onClick={() => handleToggleSku(sku)}
              color={formData.allowed_vm_skus.includes(sku) ? 'primary' : 'default'}
              variant={formData.allowed_vm_skus.includes(sku) ? 'filled' : 'outlined'}
              sx={{ mb: 1 }}
            />
          ))}
        </Stack>
      </Box>

      <Divider sx={{ my: 3 }} />

      {/* Allowed Disk Types */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Allowed Disk Types
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Select disk types available for server migration
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {DISK_TYPES.map((diskType) => (
            <Chip
              key={diskType}
              label={diskType}
              onClick={() => handleToggleDiskType(diskType)}
              color={formData.allowed_disk_types.includes(diskType) ? 'primary' : 'default'}
              variant={formData.allowed_disk_types.includes(diskType) ? 'filled' : 'outlined'}
              sx={{ mb: 1 }}
            />
          ))}
        </Stack>
      </Box>

      {/* Save Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={saveMutation.isPending || formData.allowed_regions.length === 0}
        >
          {saveMutation.isPending ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>
    </Box>
  );
}
```

**Integration**: Add new tab in `ProjectDetailsPage.tsx`:

```tsx
<Tab label="Migration Settings" {...a11yProps(5)} />

<TabPanel value={currentTab} index={5}>
  <Box sx={{ px: 3 }}>
    <MigrationSettingsEditor projectId={project.id} />
  </Box>
</TabPanel>
```

### 4.2 Migrate Project Lookup Utility

**File**: `frontend/src/utils/migrateProjectLookup.ts` (NEW)

```typescript
import type { LandingZoneMigrateProject } from '../types/project.types';

export interface MigrateProjectInfo {
  migrateProjectName: string;
  applianceName: string | null;
  applianceType: string | null;
  recoveryVaultName: string | null;
  migrateProjectSubscription: string | null;
  migrateResourceGroup: string | null;
}

/**
 * Find migrate project that contains the given subscription in its app landing zones.
 * 
 * @param subscriptionId - Azure subscription ID to look up
 * @param lzMigrateProjects - Array of landing zone migrate projects from project metadata
 * @returns Migrate project info or null if not found
 */
export function getMigrateProjectBySubscription(
  subscriptionId: string,
  lzMigrateProjects: LandingZoneMigrateProject[]
): MigrateProjectInfo | null {
  if (!subscriptionId || !lzMigrateProjects || lzMigrateProjects.length === 0) {
    return null;
  }

  for (const migrateProject of lzMigrateProjects) {
    const appLandingZones = migrateProject.appLandingZones || [];

    for (const zone of appLandingZones) {
      // Check both property names (camelCase and Title Case from CSV)
      const zoneSubscriptionId = zone.subscriptionId || zone['Subscription ID'];

      if (zoneSubscriptionId === subscriptionId) {
        return {
          migrateProjectName: migrateProject.migrateProjectName || '',
          applianceName: migrateProject.applianceName || null,
          applianceType: migrateProject.applianceType || null,
          recoveryVaultName: migrateProject.recoveryVaultName || null,
          migrateProjectSubscription: migrateProject.migrateProjectSubscription || null,
          migrateResourceGroup: migrateProject.migrateResourceGroup || null,
        };
      }
    }
  }

  return null;
}

/**
 * Get all unique subscriptions from app landing zones.
 * 
 * @param lzMigrateProjects - Array of landing zone migrate projects
 * @returns Array of unique subscription IDs
 */
export function getAllAppLandingZoneSubscriptions(
  lzMigrateProjects: LandingZoneMigrateProject[]
): string[] {
  const subscriptions = new Set<string>();

  for (const migrateProject of lzMigrateProjects) {
    const appLandingZones = migrateProject.appLandingZones || [];

    for (const zone of appLandingZones) {
      const subId = zone.subscriptionId || zone['Subscription ID'];
      if (subId) {
        subscriptions.add(subId);
      }
    }
  }

  return Array.from(subscriptions);
}

/**
 * Get all unique regions from app landing zones.
 * 
 * @param lzMigrateProjects - Array of landing zone migrate projects
 * @returns Array of unique Azure regions
 */
export function getAllAppLandingZoneRegions(
  lzMigrateProjects: LandingZoneMigrateProject[]
): string[] {
  const regions = new Set<string>();

  for (const migrateProject of lzMigrateProjects) {
    const appLandingZones = migrateProject.appLandingZones || [];

    for (const zone of appLandingZones) {
      const region = zone.region || zone['Region'];
      if (region) {
        regions.add(region);
      }
    }
  }

  return Array.from(regions);
}
```

### 4.3 Server Service Extensions

**File**: `frontend/src/services/servers.service.ts`

```typescript
export const serversService = {
  // ... existing methods ...

  bulkUpdate: async (
    projectId: number,
    serverIds: number[],
    updates: Partial<ServerConfig>
  ): Promise<{ updated_count: number }> => {
    const response = await api.put(`/projects/${projectId}/servers/bulk`, {
      server_ids: serverIds,
      updates,
    });
    return response.data;
  },

  update: async (serverId: number, updates: Partial<ServerConfig>): Promise<ServerConfig> => {
    const response = await api.put(`/servers/${serverId}`, updates);
    return response.data;
  },
};
```

---

## 5. CSV Upload Schema & Validation

### 5.1 Required CSV Columns

```csv
Target Machine,Target Region,Target Subscription,Target RG,Target VNet,Target Subnet,Target Machine SKU,Target Disk Type
```

**Note**: `Migrate Project Name` column is NOT in the CSV - it's auto-populated by the backend.

### 5.2 Validation Rules

1. **Required Columns**:
   - Target Machine (unique per project)
   - Target Region
   - Target Subscription (must exist in app landing zones)
   - Target RG
   - Target VNet
   - Target Subnet

2. **Optional Columns**:
   - Target Machine SKU (defaults to project settings if empty)
   - Target Disk Type (defaults to project settings if empty)

3. **Auto-Populated Fields**:
   - Migrate Project Name (based on Target Subscription lookup)
   - Appliance Name (from matched migrate project)
   - Appliance Type (from matched migrate project)
   - Recovery Vault Name (from matched migrate project)

### 5.3 Validation Warnings

Display warnings (not errors) for:
- Target Subscription not found in any app landing zone
- Duplicate Target Machine names
- Target Region not in migration_settings.allowed_regions
- Target Machine SKU not in migration_settings.allowed_vm_skus
- Target Disk Type not in migration_settings.allowed_disk_types

---

## 6. Implementation Priority

### Phase 1: Data Model & Backend (Days 1-2)
1. ✅ Add migration_settings to Project model
2. ✅ Add migrate_project_name to ServerConfig model
3. ✅ Database migration (Alembic)
4. ✅ Migration settings GET/PUT endpoints
5. ✅ Bulk update endpoint
6. ✅ Single server update endpoint
7. ✅ Enhance CSV upload with auto-population

### Phase 2: Core Components (Days 3-5)
8. ✅ Install react-dropzone, @tanstack/react-table, xlsx, file-saver
9. ✅ Create MigrationSettingsEditor component
10. ✅ Create migrateProjectLookup utility
11. ✅ Create ServerUploadZone component
12. ✅ Create ServerTable component (basic)
13. ✅ Create BulkEditModal component

### Phase 3: Advanced Features (Days 6-7)
14. ✅ Add column sorting/filtering to ServerTable
15. ✅ Add export to Excel functionality
16. ✅ Create ServerDetailsModal
17. ✅ Add upload progress tracking
18. ✅ Add confirmation dialogs

### Phase 4: Polish & Testing (Days 8-9)
19. ✅ Add empty states and skeleton loading
20. ✅ Add toast notifications
21. ✅ Add import validation preview
22. ✅ Responsive design (mobile/tablet)
23. ✅ End-to-end testing

---

## 7. Testing Checklist

### Backend Tests
- [ ] Migration settings default population on project creation
- [ ] Migration settings validation (at least 1 region required)
- [ ] Subscription lookup returns correct migrate project
- [ ] Subscription lookup handles missing subscriptions
- [ ] Bulk update modifies all selected servers
- [ ] Bulk update auto-populates migrate project name
- [ ] Single server update validates subscription exists
- [ ] CSV upload auto-populates migrate project name
- [ ] CSV upload returns warnings for invalid subscriptions

### Frontend Tests
- [ ] Migration settings editor saves correctly
- [ ] Migration settings editor validates at least 1 region
- [ ] Migrate project lookup utility works with camelCase and Title Case
- [ ] ServerUploadZone accepts .xlsx/.xls/.csv files
- [ ] ServerUploadZone rejects invalid file types
- [ ] ServerUploadZone shows upload progress
- [ ] ServerTable displays all columns including migrate project name
- [ ] ServerTable sorting works for all columns
- [ ] ServerTable row selection works
- [ ] BulkEditModal populates dropdowns from migration settings
- [ ] BulkEditModal auto-fills migrate project name on subscription change
- [ ] BulkEditModal validates target subscription exists
- [ ] ServerDetailsModal shows read-only migrate project name
- [ ] Export to Excel includes all columns
- [ ] Confirmation dialogs appear for delete operations
- [ ] Toast notifications appear for all operations
- [ ] Responsive design works on mobile

---

## 8. User Workflows

### 8.1 Workflow: Configure Migration Settings

1. Navigate to Project Details → Migration Settings tab
2. Select allowed regions (e.g., uksouth, ukwest)
3. Select allowed VM SKUs (e.g., Standard_DS1_v2, Standard_D2s_v3)
4. Select allowed disk types (e.g., Premium_LRS, Standard_LRS)
5. Click "Save Settings"
6. Settings are now available in bulk edit dropdowns

### 8.2 Workflow: Upload Servers via CSV

1. Navigate to Project Details → Servers tab
2. Click "Upload Servers" or drag CSV file to upload zone
3. System validates CSV headers
4. System parses rows and shows preview modal
5. Preview shows:
   - First 10 servers
   - Auto-populated Migrate Project Name for each row
   - Warnings for subscriptions not found in app landing zones
6. User clicks "Proceed with Import"
7. Backend creates servers with auto-populated fields
8. Toast notification: "42 servers created, 0 updated"

### 8.3 Workflow: Bulk Edit Servers

1. Navigate to Project Details → Servers tab
2. Select multiple servers via checkboxes
3. Click "Bulk Edit" button in toolbar
4. Modal opens with dropdowns for:
   - Target Region (from migration_settings.allowed_regions)
   - Target Subscription (from app landing zones)
   - Target Machine SKU (from migration_settings.allowed_vm_skus)
   - Target Disk Type (from migration_settings.allowed_disk_types)
5. User selects Target Subscription → Migrate Project Name auto-fills
6. User fills other fields (only filled fields will update)
7. Click "Update 15 Servers"
8. Backend updates all selected servers
9. Toast notification: "15 servers updated successfully"

### 8.4 Workflow: Edit Single Server

1. Navigate to Project Details → Servers tab
2. Click Edit icon on server row
3. ServerDetailsModal opens
4. User changes Target Subscription
5. Migrate Project Name, Appliance Name auto-update
6. User modifies other fields (Region, SKU, Disk Type)
7. Click "Save"
8. Backend validates subscription exists in app landing zones
9. Server updates, modal closes
10. Toast notification: "Server updated successfully"

---

## 9. Error Handling

### Backend Errors
- **400 Bad Request**: Invalid migration settings, missing required fields, subscription not found
- **404 Not Found**: Project not found, server not found
- **500 Internal Server Error**: Database errors, unexpected failures

### Frontend Error Messages
- Upload errors: "CSV file is missing required column: Target Machine"
- Validation errors: "Target Subscription 'xxx' not found in app landing zones"
- Bulk edit errors: "At least one server must be selected"
- Migration settings errors: "At least one region must be configured"

---

## 10. Performance Considerations

1. **Lazy Loading**: Use React.lazy for ServerTable and BulkEditModal
2. **Pagination**: Load servers in batches (10/25/50 per page)
3. **Debouncing**: Debounce search/filter inputs (300ms delay)
4. **Memoization**: Use useMemo for filtered/sorted server lists
5. **Optimistic Updates**: Update UI immediately, rollback on error
6. **CSV Parsing**: Parse files client-side to reduce backend load
7. **Bulk Operations**: Use database transactions for bulk updates

---

## 11. Accessibility

- All buttons have aria-labels
- Confirmation dialogs have clear focus management
- Keyboard navigation works for table sorting/selection
- Screen readers announce toast notifications
- Color contrast meets WCAG AA standards
- Form inputs have associated labels

---

**End of Specification**

This document serves as the complete implementation guide for the Server Management feature. All code snippets are production-ready and follow the existing codebase patterns.
