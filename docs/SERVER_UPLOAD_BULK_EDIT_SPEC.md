# Server Upload & Bulk Edit Specification

## Overview
Enhanced server management with intelligent auto-population of Migrate Project Name based on Target Subscription and configurable migration settings.

---

## 1. CSV Upload Schema

### Required Columns (from sample_servers_validation.csv)
```csv
Target Machine,Target Region,Target Subscription,Target RG,Target VNet,Target Subnet,Target Machine SKU,Target Disk Type
```

### Example Row
```csv
D-DC1-QVIEW03,uksouth,b645b354-11fb-4f23-b006-856c378dd73a,u-uks-tradevtest-migration-rg-01,u-uks-tra-vnet-01,Qlik,Standard_DS1_v2,Premium_LRS
```

### Auto-Populated Column (NOT in CSV)
- **Migrate Project Name**: Automatically determined by matching `Target Subscription` to an Application Landing Zone subscription within the project's migrate projects

---

## 2. Data Model Changes

### 2.1 ServerConfig Table Enhancement
**File**: `api/models.py` (line ~194)

**Add Column**:
```python
migrate_project_name = Column(String(255), nullable=True)
```

**Purpose**: Store the migrate project name that corresponds to the target subscription. This enables tracking which Azure Migrate project and appliance will handle this server's migration.

**Migration**:
```bash
alembic revision --autogenerate -m "add_migrate_project_to_servers"
alembic upgrade head
```

### 2.2 Project Migration Settings
**Location**: `Project.metadata_json.migration_settings`

**Schema**:
```json
{
  "migration_settings": {
    "allowed_regions": [
      "uksouth",
      "ukwest",
      "eastus",
      "westus",
      "northeurope",
      "westeurope"
    ],
    "allowed_vm_skus": [
      "Standard_DS1_v2",
      "Standard_DS2_v2",
      "Standard_D2s_v3",
      "Standard_D4s_v3",
      "Standard_E2s_v3"
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

**Purpose**: Define allowed values for bulk edit dropdowns and server configuration validation.

---

## 3. Business Logic Rules

### Rule 1: Migrate Project Name Auto-Population

**When**: User uploads CSV or edits Target Subscription field

**Logic**:
1. Extract `Target Subscription` value from server config
2. Query `project.lz_migrate_projects` array
3. For each migrate project, check if `appLandingZones` array contains a zone with matching `subscriptionId`
4. If match found:
   - Set `migrate_project_name` = migrate project's `migrateProjectName`
   - Store associated metadata (appliance name, type, recovery vault) for display
5. If no match found:
   - Set `migrate_project_name` = NULL
   - Show validation warning: "Target Subscription {id} not found in any Application Landing Zone"

**Example**:
```typescript
// Given project with lz_migrate_projects:
[
  {
    migrateProjectName: "p-az1-migrate04",
    applianceName: "appliance-ukeast-01",
    applianceType: "VMware",
    appLandingZones: [
      {
        subscriptionId: "b645b354-11fb-4f23-b006-856c378dd73a",
        region: "uksouth",
        cacheStorageAccount: "uukstramigrate01",
        cacheStorageResourceGroup: "u-uks-tradevtest-migration-rg-01"
      }
    ]
  }
]

// Server with target_subscription = "b645b354-11fb-4f23-b006-856c378dd73a"
// → migrate_project_name auto-set to "p-az1-migrate04"
```

### Rule 2: Target Region Source

**Priority Order**:
1. **From Migration Settings** (if configured): Use `project.metadata_json.migration_settings.allowed_regions`
2. **From Landing Zones** (fallback): Extract unique regions from `project.lz_migrate_projects[*].appLandingZones[*].region`
3. **Free Text** (last resort): Allow manual entry if neither above is available

**Bulk Edit Dropdown**:
```tsx
const regionOptions = 
  project.metadata_json?.migration_settings?.allowed_regions || 
  [...new Set(project.lz_migrate_projects?.flatMap(mp => 
    mp.appLandingZones.map(zone => zone.region)
  ))];
```

### Rule 3: Target Subscription Validation

**Constraint**: Target Subscription MUST match one of the Application Landing Zone subscriptions

**Validation**:
```typescript
function isValidTargetSubscription(subscriptionId: string, project: Project): boolean {
  return project.lz_migrate_projects?.some(mp => 
    mp.appLandingZones.some(zone => zone.subscriptionId === subscriptionId)
  ) ?? false;
}
```

**Error Message**: "Target Subscription must be one of the configured Application Landing Zones. Available: {list of subscription IDs}"

### Rule 4: VM SKU & Disk Type Defaults

**Optional Fields**: User can bulk edit these even if not originally specified

**Source Priority**:
1. **From Migration Settings** (preferred): Use `project.metadata_json.migration_settings.allowed_vm_skus` and `allowed_disk_types`
2. **System Defaults** (fallback): Use hardcoded defaults from `api/utils/default_migration_settings.py`

**Default Values**:
```python
DEFAULT_VM_SKUS = [
    'Standard_DS1_v2',
    'Standard_DS2_v2',
    'Standard_DS3_v2',
    'Standard_D2s_v3',
    'Standard_D4s_v3',
    'Standard_D8s_v3',
    'Standard_E2s_v3',
    'Standard_E4s_v3',
]

DEFAULT_DISK_TYPES = [
    'Premium_LRS',
    'Standard_LRS',
    'StandardSSD_LRS',
    'UltraSSD_LRS',
]
```

### Rule 5: Bulk Edit Behavior

**Only Update Non-Empty Fields**: If a field is left blank in the bulk edit modal, the existing value is preserved

**Example**:
```typescript
// User selects 3 servers and fills only:
// - Target Region: "uksouth"
// - Target Subscription: "b645b354-11fb-4f23-b006-856c378dd73a"
// (leaves VNet, Subnet, SKU, Disk Type blank)

// Result: Only region and subscription are updated
// Migrate Project Name is auto-updated to "p-az1-migrate04"
// Other fields (VNet, Subnet, SKU, Disk Type) keep their original values
```

---

## 4. User Workflows

### Workflow 1: CSV Upload with Auto-Population

```
User uploads CSV file
    │
    ▼
System parses CSV
    │
    ▼
For each row:
    │
    ├─► Extract Target Subscription
    │
    ├─► Lookup Migrate Project
    │   │
    │   ├─► Match found → Set migrate_project_name
    │   │
    │   └─► No match → Set NULL + add warning
    │
    └─► Insert/Update ServerConfig in database
    │
    ▼
Show Import Summary:
  ✓ 5 servers created
  ⚠ 2 servers have invalid subscriptions
  ℹ Migrate Projects: p-az1-migrate04 (5)
```

### Workflow 2: Bulk Edit Region & Subscription

```
User selects 10 servers
    │
    ▼
Click "Bulk Edit" button
    │
    ▼
Bulk Edit Modal opens:
    │
    ├─► Target Region dropdown
    │   └─► Options from migration_settings OR landing zones
    │
    ├─► Target Subscription dropdown
    │   └─► Options from app landing zones
    │
    ├─► Other fields (VNet, Subnet, SKU, Disk Type)
    │
    └─► User selects:
        - Region: "uksouth"
        - Subscription: "b645b354-..."
        │
        ▼
System auto-populates:
    - Migrate Project Name: "p-az1-migrate04"
    - Shows appliance: "appliance-ukeast-01"
    - Shows recovery vault: "vault-migrate-uksouth"
    │
    ▼
User clicks "Update 10 Servers"
    │
    ▼
Backend updates all 10 servers
    │
    ▼
Toast: "✓ 10 servers updated"
```

### Workflow 3: Single Server Edit with Subscription Change

```
User clicks Edit icon on server row
    │
    ▼
ServerDetailsModal opens:
    │
    ├─► Show all fields (read-write)
    │
    ├─► Migrate Project Name field (read-only, grayed out)
    │   └─► Current value: "p-az1-migrate04"
    │
    └─► User changes Target Subscription dropdown
        │
        ▼
    System detects change:
        │
        ├─► Lookup new migrate project
        │
        └─► Update Migrate Project Name field (auto)
            │
            ├─► Show new appliance name below
            │
            └─► Show new recovery vault name
        │
        ▼
User clicks "Save"
    │
    ▼
Backend updates server + migrate_project_name
    │
    ▼
Toast: "✓ Server updated"
Table row refreshes with new data
```

---

## 5. Component Specifications

### 5.1 ServerUploadZone Component

**File**: `frontend/src/components/servers/ServerUploadZone.tsx`

**Props**:
```typescript
interface ServerUploadZoneProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
  uploadProgress: number; // 0-100
  project: Project; // For validation
}
```

**Features**:
- Drag-and-drop zone (react-dropzone)
- Accept: `.csv`, `.xlsx`, `.xls`
- CSV Header Validation:
  - Required: Target Machine, Target Region, Target Subscription, Target RG, Target VNet, Target Subnet, Target Machine SKU, Target Disk Type
  - Show error if any column missing
- Client-side Preview:
  - Parse first 10 rows
  - Show table with columns
  - Highlight invalid subscriptions in red
  - Show which Migrate Project will be assigned (green checkmark)
- Upload Progress:
  - Linear progress bar
  - Percentage (0-100%)
  - Upload speed (KB/s)
  - ETA (seconds)
- Cancel Upload button

**UI**:
```tsx
<Box
  sx={{
    border: '2px dashed',
    borderColor: isDragActive ? 'primary.main' : 'grey.300',
    borderRadius: 2,
    p: 4,
    textAlign: 'center',
    cursor: 'pointer',
    bgcolor: isDragActive ? 'action.hover' : 'background.paper',
  }}
>
  <CloudUploadIcon sx={{ fontSize: 64, color: 'text.secondary' }} />
  <Typography variant="h6">
    {isDragActive ? 'Drop file here' : 'Drag & drop CSV file'}
  </Typography>
  <Typography variant="body2" color="text.secondary">
    or click to browse
  </Typography>
  
  {isUploading && (
    <Box sx={{ mt: 2 }}>
      <LinearProgress variant="determinate" value={uploadProgress} />
      <Typography variant="caption">
        Uploading... {uploadProgress}% ({uploadSpeed} KB/s, ETA: {eta}s)
      </Typography>
    </Box>
  )}
</Box>
```

### 5.2 BulkEditModal Component

**File**: `frontend/src/components/servers/BulkEditModal.tsx`

**Props**:
```typescript
interface BulkEditModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (updates: Partial<ServerConfig>) => void;
  selectedServerIds: number[];
  project: Project; // For dropdown options
}
```

**Form Fields**:
```tsx
<Grid container spacing={2}>
  {/* Target Region - Smart Dropdown */}
  <Grid item xs={12} sm={6}>
    <FormControl fullWidth>
      <InputLabel>Target Region</InputLabel>
      <Select
        value={formData.target_region}
        onChange={handleRegionChange}
      >
        <MenuItem value="">Keep current</MenuItem>
        {regionOptions.map(region => (
          <MenuItem key={region} value={region}>{region}</MenuItem>
        ))}
      </Select>
      <FormHelperText>
        {regionOptions.length > 0 
          ? 'From migration settings' 
          : 'From landing zone regions'}
      </FormHelperText>
    </FormControl>
  </Grid>

  {/* Target Subscription - From App Landing Zones */}
  <Grid item xs={12} sm={6}>
    <FormControl fullWidth>
      <InputLabel>Target Subscription</InputLabel>
      <Select
        value={formData.target_subscription}
        onChange={handleSubscriptionChange}
      >
        <MenuItem value="">Keep current</MenuItem>
        {appLandingZoneSubscriptions.map(sub => (
          <MenuItem key={sub.id} value={sub.id}>
            {sub.id} ({sub.region})
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  </Grid>

  {/* Auto-Populated Migrate Project Name */}
  {autoPopulatedMigrateProject && (
    <Grid item xs={12}>
      <Alert severity="info" icon={<CheckCircleIcon />}>
        <AlertTitle>Migrate Project Auto-Selected</AlertTitle>
        <strong>{autoPopulatedMigrateProject.name}</strong>
        <br />
        Appliance: {autoPopulatedMigrateProject.applianceName}
        <br />
        Recovery Vault: {autoPopulatedMigrateProject.recoveryVaultName}
      </Alert>
    </Grid>
  )}

  {/* Target Resource Group */}
  <Grid item xs={12} sm={6}>
    <TextField
      fullWidth
      label="Target Resource Group"
      value={formData.target_resource_group}
      onChange={(e) => setFormData({ ...formData, target_resource_group: e.target.value })}
      placeholder="Leave empty to keep current"
    />
  </Grid>

  {/* Target VNet */}
  <Grid item xs={12} sm={6}>
    <TextField
      fullWidth
      label="Target VNet"
      value={formData.target_vnet}
      onChange={(e) => setFormData({ ...formData, target_vnet: e.target.value })}
      placeholder="Leave empty to keep current"
    />
  </Grid>

  {/* Target Subnet */}
  <Grid item xs={12} sm={6}>
    <TextField
      fullWidth
      label="Target Subnet"
      value={formData.target_subnet}
      onChange={(e) => setFormData({ ...formData, target_subnet: e.target.value })}
      placeholder="Leave empty to keep current"
    />
  </Grid>

  {/* Target VM SKU - Smart Dropdown */}
  <Grid item xs={12} sm={6}>
    <FormControl fullWidth>
      <InputLabel>Target VM SKU</InputLabel>
      <Select
        value={formData.target_machine_sku}
        onChange={(e) => setFormData({ ...formData, target_machine_sku: e.target.value })}
      >
        <MenuItem value="">Keep current</MenuItem>
        {vmSkuOptions.map(sku => (
          <MenuItem key={sku} value={sku}>{sku}</MenuItem>
        ))}
      </Select>
      <FormHelperText>
        {vmSkuOptions.length > 0 
          ? 'From migration settings' 
          : 'System defaults'}
      </FormHelperText>
    </FormControl>
  </Grid>

  {/* Target Disk Type - Smart Dropdown */}
  <Grid item xs={12} sm={6}>
    <FormControl fullWidth>
      <InputLabel>Target Disk Type</InputLabel>
      <Select
        value={formData.target_disk_type}
        onChange={(e) => setFormData({ ...formData, target_disk_type: e.target.value })}
      >
        <MenuItem value="">Keep current</MenuItem>
        <MenuItem value="Premium_LRS">Premium LRS</MenuItem>
        <MenuItem value="Standard_LRS">Standard LRS</MenuItem>
        <MenuItem value="StandardSSD_LRS">Standard SSD LRS</MenuItem>
        <MenuItem value="UltraSSD_LRS">Ultra SSD LRS</MenuItem>
      </Select>
    </FormControl>
  </Grid>
</Grid>
```

**Dialog Actions**:
```tsx
<DialogActions>
  <Button onClick={onClose}>Cancel</Button>
  <Button
    variant="contained"
    onClick={handleSubmit}
    disabled={Object.values(formData).every(v => !v)} // Disable if all fields empty
  >
    Update {selectedServerIds.length} Servers
  </Button>
</DialogActions>
```

### 5.3 ServerTable Component

**File**: `frontend/src/components/servers/ServerTable.tsx`

**Columns**:
1. **Checkbox** - Row selection (multi-select)
2. **Target Machine** - Sortable, filterable
3. **Target Region** - Sortable, filterable
4. **Target Subscription** - Truncated (first 8 chars + ...), tooltip shows full ID
5. **Target RG** - Sortable
6. **VNet / Subnet** - Combined display "{vnet} / {subnet}"
7. **SKU** - Sortable, filterable
8. **Disk Type** - Sortable, filterable
9. **Migrate Project Name** - Sortable, filterable, **NEW COLUMN**
10. **Actions** - Edit/Delete icons

**Bulk Action Toolbar** (shows when rows selected):
```tsx
{selectedRowIds.length > 0 && (
  <Box sx={{ p: 2, bgcolor: 'action.selected' }}>
    <Typography variant="body2" sx={{ display: 'inline', mr: 2 }}>
      {selectedRowIds.length} selected
    </Typography>
    <Button
      size="small"
      onClick={() => setIsBulkEditOpen(true)}
      startIcon={<EditIcon />}
    >
      Bulk Edit
    </Button>
    <Button
      size="small"
      onClick={handleBulkDelete}
      startIcon={<DeleteIcon />}
      color="error"
    >
      Delete Selected
    </Button>
    <Button
      size="small"
      onClick={handleExportSelected}
      startIcon={<FileDownloadIcon />}
    >
      Export Selected
    </Button>
  </Box>
)}
```

### 5.4 MigrationSettingsEditor Component

**File**: `frontend/src/components/projects/MigrationSettingsEditor.tsx`

**Purpose**: Configure allowed regions, VM SKUs, and disk types for the project

**Location**: New tab in ProjectDetailsPage.tsx → "Migration Settings"

**Form**:
```tsx
<Box sx={{ p: 3 }}>
  <Typography variant="h6" gutterBottom>
    Migration Configuration
  </Typography>
  <Divider sx={{ mb: 3 }} />

  {/* Allowed Regions */}
  <Box sx={{ mb: 3 }}>
    <Typography variant="subtitle1" gutterBottom>
      Allowed Target Regions
    </Typography>
    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
      Select which Azure regions servers can be migrated to. Used in bulk edit dropdowns.
    </Typography>
    <Autocomplete
      multiple
      options={AZURE_REGIONS} // Predefined list
      value={settings.allowed_regions}
      onChange={(_, newValue) => handleChange('allowed_regions', newValue)}
      renderInput={(params) => (
        <TextField {...params} label="Regions" placeholder="Add region" />
      )}
      renderTags={(value, getTagProps) =>
        value.map((option, index) => (
          <Chip label={option} {...getTagProps({ index })} />
        ))
      }
    />
  </Box>

  {/* Allowed VM SKUs */}
  <Box sx={{ mb: 3 }}>
    <Typography variant="subtitle1" gutterBottom>
      Allowed VM SKUs
    </Typography>
    <Autocomplete
      multiple
      freeSolo
      options={DEFAULT_VM_SKUS}
      value={settings.allowed_vm_skus}
      onChange={(_, newValue) => handleChange('allowed_vm_skus', newValue)}
      renderInput={(params) => (
        <TextField {...params} label="VM SKUs" placeholder="Add SKU" />
      )}
    />
  </Box>

  {/* Allowed Disk Types */}
  <Box sx={{ mb: 3 }}>
    <Typography variant="subtitle1" gutterBottom>
      Allowed Disk Types
    </Typography>
    <Autocomplete
      multiple
      options={DEFAULT_DISK_TYPES}
      value={settings.allowed_disk_types}
      onChange={(_, newValue) => handleChange('allowed_disk_types', newValue)}
      renderInput={(params) => (
        <TextField {...params} label="Disk Types" placeholder="Add type" />
      )}
    />
  </Box>

  <Button variant="contained" onClick={handleSave}>
    Save Migration Settings
  </Button>
</Box>
```

---

## 6. API Endpoints

### 6.1 Bulk Update Servers

**Endpoint**: `PUT /api/v1/projects/{project_id}/servers/bulk`

**Request Body**:
```json
{
  "server_ids": [1, 2, 3, 4, 5],
  "updates": {
    "target_region": "uksouth",
    "target_subscription": "b645b354-11fb-4f23-b006-856c378dd73a"
  }
}
```

**Response**:
```json
{
  "updated_count": 5,
  "updated_servers": [
    {
      "id": 1,
      "target_machine_name": "D-DC1-QVIEW03",
      "target_region": "uksouth",
      "target_subscription": "b645b354-11fb-4f23-b006-856c378dd73a",
      "migrate_project_name": "p-az1-migrate04"
    }
  ]
}
```

**Implementation**:
```python
@router.put("/projects/{project_id}/servers/bulk")
async def bulk_update_servers(
    project_id: int,
    bulk_update: ServerBulkUpdate,
    db: Session = Depends(get_db)
):
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get servers
    servers = db.query(ServerConfig).filter(
        ServerConfig.id.in_(bulk_update.server_ids),
        ServerConfig.project_id == project_id
    ).all()
    
    if not servers:
        raise HTTPException(status_code=404, detail="No servers found")
    
    # Update each server
    updated_servers = []
    for server in servers:
        # Apply updates (only non-null fields)
        if bulk_update.updates.target_region:
            server.target_region = bulk_update.updates.target_region
        if bulk_update.updates.target_subscription:
            server.target_subscription = bulk_update.updates.target_subscription
            # Auto-populate migrate_project_name
            migrate_project = find_migrate_project_by_subscription(
                project.metadata_json.get('lz_migrate_projects', []),
                bulk_update.updates.target_subscription
            )
            if migrate_project:
                server.migrate_project_name = migrate_project['migrateProjectName']
        if bulk_update.updates.target_resource_group:
            server.target_resource_group = bulk_update.updates.target_resource_group
        # ... other fields
        
        server.updated_at = datetime.utcnow()
        updated_servers.append(server)
    
    db.commit()
    
    return {
        "updated_count": len(updated_servers),
        "updated_servers": updated_servers
    }
```

### 6.2 Update Single Server

**Endpoint**: `PUT /api/v1/servers/{server_id}`

**Request Body** (all fields optional):
```json
{
  "target_region": "uksouth",
  "target_subscription": "b645b354-11fb-4f23-b006-856c378dd73a",
  "target_resource_group": "u-uks-tradevtest-migration-rg-01"
}
```

**Response**:
```json
{
  "id": 1,
  "target_machine_name": "D-DC1-QVIEW03",
  "target_region": "uksouth",
  "target_subscription": "b645b354-11fb-4f23-b006-856c378dd73a",
  "target_resource_group": "u-uks-tradevtest-migration-rg-01",
  "migrate_project_name": "p-az1-migrate04",
  "updated_at": "2025-11-04T10:30:00Z"
}
```

### 6.3 Get/Update Migration Settings

**Endpoint**: `GET /api/v1/projects/{project_id}/migration-settings`

**Response**:
```json
{
  "allowed_regions": ["uksouth", "ukwest", "eastus"],
  "allowed_vm_skus": ["Standard_DS1_v2", "Standard_DS2_v2"],
  "allowed_disk_types": ["Premium_LRS", "Standard_LRS"]
}
```

**Endpoint**: `PUT /api/v1/projects/{project_id}/migration-settings`

**Request Body**: Same as GET response

**Implementation**:
```python
@router.get("/projects/{project_id}/migration-settings")
async def get_migration_settings(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    settings = project.metadata_json.get('migration_settings', {})
    
    # Return defaults if not set
    if not settings:
        settings = {
            'allowed_regions': DEFAULT_REGIONS,
            'allowed_vm_skus': DEFAULT_VM_SKUS,
            'allowed_disk_types': DEFAULT_DISK_TYPES,
        }
    
    return settings

@router.put("/projects/{project_id}/migration-settings")
async def update_migration_settings(
    project_id: int,
    settings: MigrationSettings,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update metadata_json
    if not project.metadata_json:
        project.metadata_json = {}
    
    project.metadata_json['migration_settings'] = settings.dict()
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return project.metadata_json['migration_settings']
```

---

## 7. Utility Functions

### 7.1 Migrate Project Lookup

**File**: `frontend/src/utils/migrateProjectLookup.ts`

```typescript
import type { LandingZoneMigrateProject } from '../types/project.types';

export interface MigrateProjectInfo {
  migrateProjectName: string;
  applianceName: string;
  applianceType?: string;
  recoveryVaultName: string;
  migrateResourceGroup: string;
  migrateProjectSubscription: string;
}

/**
 * Find migrate project by matching target subscription to app landing zone
 * @param targetSubscription - The subscription ID from server config
 * @param migrateProjects - Array of migrate projects from project.lz_migrate_projects
 * @returns MigrateProjectInfo if found, null otherwise
 */
export function getMigrateProjectBySubscription(
  targetSubscription: string,
  migrateProjects: LandingZoneMigrateProject[]
): MigrateProjectInfo | null {
  if (!migrateProjects || migrateProjects.length === 0) {
    return null;
  }

  for (const migrateProject of migrateProjects) {
    // Check if any app landing zone matches the target subscription
    const matchingZone = migrateProject.appLandingZones?.find(
      (zone) => zone.subscriptionId === targetSubscription
    );

    if (matchingZone) {
      return {
        migrateProjectName: migrateProject.migrateProjectName,
        applianceName: migrateProject.applianceName,
        applianceType: migrateProject.applianceType,
        recoveryVaultName: migrateProject.recoveryVaultName,
        migrateResourceGroup: migrateProject.migrateResourceGroup,
        migrateProjectSubscription: migrateProject.migrateProjectSubscription,
      };
    }
  }

  return null;
}

/**
 * Get all available target subscriptions from app landing zones
 * @param migrateProjects - Array of migrate projects
 * @returns Array of subscription IDs with their regions
 */
export function getAvailableTargetSubscriptions(
  migrateProjects: LandingZoneMigrateProject[]
): Array<{ id: string; region: string; migrateProjectName: string }> {
  if (!migrateProjects || migrateProjects.length === 0) {
    return [];
  }

  const subscriptions: Array<{ id: string; region: string; migrateProjectName: string }> = [];

  for (const migrateProject of migrateProjects) {
    if (migrateProject.appLandingZones) {
      for (const zone of migrateProject.appLandingZones) {
        subscriptions.push({
          id: zone.subscriptionId,
          region: zone.region,
          migrateProjectName: migrateProject.migrateProjectName,
        });
      }
    }
  }

  return subscriptions;
}
```

### 7.2 Backend Lookup Utility

**File**: `api/utils/migrate_project_lookup.py`

```python
from typing import Optional, Dict, Any, List

def find_migrate_project_by_subscription(
    lz_migrate_projects: List[Dict[str, Any]],
    target_subscription: str
) -> Optional[Dict[str, Any]]:
    """
    Find migrate project by matching target subscription to app landing zone.
    
    Args:
        lz_migrate_projects: List of migrate project configs from project.metadata_json
        target_subscription: The subscription ID from server config
        
    Returns:
        Migrate project dict if found, None otherwise
    """
    if not lz_migrate_projects:
        return None
    
    for migrate_project in lz_migrate_projects:
        app_landing_zones = migrate_project.get('appLandingZones', [])
        
        for zone in app_landing_zones:
            if zone.get('subscriptionId') == target_subscription:
                return {
                    'migrateProjectName': migrate_project.get('migrateProjectName'),
                    'applianceName': migrate_project.get('applianceName'),
                    'applianceType': migrate_project.get('applianceType'),
                    'recoveryVaultName': migrate_project.get('recoveryVaultName'),
                    'migrateResourceGroup': migrate_project.get('migrateResourceGroup'),
                    'migrateProjectSubscription': migrate_project.get('migrateProjectSubscription'),
                }
    
    return None
```

---

## 8. Testing Scenarios

### Test Case 1: CSV Upload with Valid Subscription
**Given**: CSV with Target Subscription = "b645b354-11fb-4f23-b006-856c378dd73a"  
**And**: Project has migrate project "p-az1-migrate04" with matching app landing zone  
**When**: User uploads CSV  
**Then**: Server is created with `migrate_project_name` = "p-az1-migrate04"  
**And**: No validation warnings

### Test Case 2: CSV Upload with Invalid Subscription
**Given**: CSV with Target Subscription = "invalid-subscription-id"  
**And**: No migrate project has matching app landing zone  
**When**: User uploads CSV  
**Then**: Server is created with `migrate_project_name` = NULL  
**And**: Validation warning: "Target Subscription invalid-subscription-id not found in any Application Landing Zone"

### Test Case 3: Bulk Edit with Subscription Change
**Given**: 5 servers with target_subscription = "sub-A"  
**And**: All have migrate_project_name = "project-A"  
**When**: User selects all 5 servers and bulk edits target_subscription to "sub-B"  
**Then**: All 5 servers are updated with new subscription  
**And**: All 5 servers have migrate_project_name = "project-B" (auto-updated)

### Test Case 4: Bulk Edit with Empty Fields
**Given**: 3 servers with different regions and SKUs  
**When**: User bulk edits and only fills Target Subscription field  
**Then**: Only target_subscription is updated  
**And**: Regions and SKUs remain unchanged  
**And**: migrate_project_name is updated based on new subscription

### Test Case 5: Migration Settings Override
**Given**: Project has migration_settings.allowed_regions = ["uksouth", "ukwest"]  
**When**: User opens Bulk Edit Modal  
**Then**: Target Region dropdown shows only "uksouth" and "ukwest"  
**And**: Helper text shows "From migration settings"

### Test Case 6: Migration Settings Fallback
**Given**: Project has NO migration_settings configured  
**But**: Has app landing zones in regions "uksouth", "eastus"  
**When**: User opens Bulk Edit Modal  
**Then**: Target Region dropdown shows "uksouth" and "eastus"  
**And**: Helper text shows "From landing zone regions"

---

## 9. Implementation Checklist

### Phase 1: Data Model & Backend (Days 1-2)
- [ ] Add `migrate_project_name` column to `ServerConfig` model
- [ ] Create Alembic migration
- [ ] Add `migration_settings` schema to Project model
- [ ] Create default migration settings utility
- [ ] Implement `find_migrate_project_by_subscription` backend utility
- [ ] Create `PUT /projects/{id}/migration-settings` endpoint
- [ ] Create `PUT /projects/{id}/servers/bulk` endpoint
- [ ] Create `PUT /servers/{id}` endpoint
- [ ] Update CSV upload endpoint to auto-populate migrate_project_name

### Phase 2: Frontend Components (Days 3-5)
- [ ] Install dependencies (react-dropzone, @tanstack/react-table, xlsx, file-saver)
- [ ] Create `migrateProjectLookup.ts` utility
- [ ] Create `MigrationSettingsEditor.tsx` component
- [ ] Add "Migration Settings" tab to ProjectDetailsPage
- [ ] Create `ServerUploadZone.tsx` with CSV validation
- [ ] Create `ServerTable.tsx` with TanStack Table (add Migrate Project Name column)
- [ ] Create `BulkEditModal.tsx` with smart dropdowns
- [ ] Create `ServerDetailsModal.tsx` with auto-population
- [ ] Update ServersPage to use new components

### Phase 3: Testing & Polish (Days 6-7)
- [ ] Test CSV upload with valid/invalid subscriptions
- [ ] Test bulk edit with subscription change
- [ ] Test bulk edit with empty fields (partial updates)
- [ ] Test migration settings editor (save/load)
- [ ] Test column visibility toggle
- [ ] Add confirmation dialogs for delete operations
- [ ] Add toast notifications for all operations
- [ ] Test responsive design on mobile/tablet
- [ ] Add empty state illustration
- [ ] Add skeleton loading states

---

## 10. Edge Cases & Error Handling

### Edge Case 1: Migrate Project Not Found
**Scenario**: User sets Target Subscription to valid ID, but no migrate project configured  
**Behavior**: Set `migrate_project_name` = NULL, show warning toast  
**UI**: Display warning icon in table row for that server

### Edge Case 2: Multiple Migrate Projects Match
**Scenario**: Two migrate projects have app landing zones with same subscription  
**Behavior**: Use the first match (deterministic order)  
**Log**: Warning to backend logs

### Edge Case 3: Subscription Deleted from Landing Zone
**Scenario**: Server has target_subscription that was previously valid, but app landing zone removed  
**Behavior**: migrate_project_name becomes stale (still shows old value)  
**Solution**: Add validation warning icon, suggest user re-select subscription

### Edge Case 4: No Migration Settings Configured
**Scenario**: Project has no migration_settings and no landing zones  
**Behavior**: Dropdowns show empty list, allow free text input as fallback  
**UI**: Show helper text: "Configure migration settings in Project Details"

### Edge Case 5: CSV with Missing Migrate Project Column
**Scenario**: User uploads old CSV without Migrate Project Name column  
**Behavior**: Auto-populate column based on Target Subscription (expected)  
**UI**: No error, system handles gracefully

---

**Document Version**: 1.0  
**Last Updated**: November 4, 2025  
**Status**: Ready for Implementation
