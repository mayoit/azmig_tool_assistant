import { useState } from 'react';
import {
  Box,
  Button,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  Checkbox,
  Collapse,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  CheckCircle as ValidateIcon,
  KeyboardArrowDown as ExpandMoreIcon,
  KeyboardArrowUp as ExpandLessIcon,
} from '@mui/icons-material';
import type { ServerConfig } from '../../types/server.types';
import type { LandingZoneMigrateProject } from '../../types/project.types';

interface EditableServerTableProps {
  servers: ServerConfig[];
  onAddServer: (data: Partial<ServerConfig>) => Promise<void>;
  onUpdateServer: (serverId: number, updates: Partial<ServerConfig>) => Promise<void>;
  onDeleteServer: (serverId: number) => Promise<void>;
  isLoading?: boolean;
  availableSubscriptions?: Array<[string, string]>;  // [id, name] tuples from landing zones
  availableRegions?: string[];        // From project settings
  landingZoneAppliances?: LandingZoneMigrateProject[];  // Available appliances from LZ
}

interface EditingRow {
  target_machine_name: string;
  target_subscription: string;
  target_region: string;
  target_resource_group: string;
  target_vnet: string;
  target_subnet: string;
  appliance_id: number | null;
}

export default function EditableServerTable({
  servers,
  onAddServer,
  onUpdateServer,
  onDeleteServer,
  isLoading = false,
  availableSubscriptions = [],
  availableRegions = [],
  landingZoneAppliances = [],
}: EditableServerTableProps) {
  console.log('[EditableServerTable] Received landingZoneAppliances:', landingZoneAppliances);
  console.log('[EditableServerTable] First appliance:', landingZoneAppliances[0]);
  if (landingZoneAppliances[0]) {
    console.log('[EditableServerTable] First appliance keys:', Object.keys(landingZoneAppliances[0]));
  }
  
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [savingId, setSavingId] = useState<number | 'new' | null>(null);
  const [selectedServers, setSelectedServers] = useState<Set<number>>(new Set());
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [validatingServers, setValidatingServers] = useState<Set<number>>(new Set());
  const [discoveredDetails, setDiscoveredDetails] = useState<Map<number, any>>(new Map());
  
  const [editData, setEditData] = useState<EditingRow>({
    target_machine_name: '',
    target_subscription: '',
    target_region: '',
    target_resource_group: '',
    target_vnet: '',
    target_subnet: '',
    appliance_id: null,
  });

  // Helper function to get subscription name from ID
  const getSubscriptionName = (subscriptionId: string): string => {
    console.log('[getSubscriptionName] Looking up:', subscriptionId);
    console.log('[getSubscriptionName] Available subscriptions:', availableSubscriptions);
    const subscription = availableSubscriptions.find(([id]) => id === subscriptionId);
    const result = subscription ? subscription[1] : subscriptionId;
    console.log('[getSubscriptionName] Result:', result);
    return result;
  };

  // Helper function to find matching appliance based on subscription and region
  const findMatchingAppliance = (subscriptionId: string, region: string): number | null => {
    if (!subscriptionId || !region) return null;

    console.log('[findMatchingAppliance] Input:', { subscriptionId, region });
    console.log('[findMatchingAppliance] Available appliances:', landingZoneAppliances);

    for (let i = 0; i < landingZoneAppliances.length; i++) {
      const lz = landingZoneAppliances[i];
      console.log(`[findMatchingAppliance] Checking appliance ${i}:`, lz);
      
      // Handle both camelCase and snake_case for the zones array property
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const zones = (lz as any).appLandingZones || (lz as any).app_landing_zones;
      console.log(`[findMatchingAppliance] Zones for appliance ${i}:`, zones);
      
      // Check if any app landing zone matches both subscription and region
      // Handle both camelCase and Title Case property names from backend
      const hasMatch = zones?.some(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (appLz: any) => {
          const appLzSubscriptionId = appLz.subscriptionId || appLz['Subscription ID'];
          const appLzRegion = appLz.region || appLz['Region'];
          
          console.log(`[findMatchingAppliance] Zone check:`, {
            appLzSubscriptionId,
            appLzRegion,
            match: appLzSubscriptionId === subscriptionId && appLzRegion?.toLowerCase() === region.toLowerCase()
          });
          
          return (
            appLzSubscriptionId === subscriptionId && 
            appLzRegion?.toLowerCase() === region.toLowerCase()
          );
        }
      );
      
      if (hasMatch) {
        console.log(`[findMatchingAppliance] MATCH FOUND at index ${i}`);
        return i; // Return the index as appliance_id
      }
    }
    
    console.log('[findMatchingAppliance] NO MATCH FOUND');
    return null; // No matching appliance found
  };

  // Helper function to get appliance details from ID/index
  const getApplianceDetails = (applianceId: number | null | undefined) => {
    if (applianceId === null || applianceId === undefined) return null;
    // applianceId is actually the array index
    return landingZoneAppliances[applianceId] || null;
  };

  // Helper function to get matching cache storage for subscription and region
  const getCacheStorageForSubscriptionRegion = (subscriptionId: string, region: string, applianceId: number | null | undefined) => {
    if (applianceId === null || applianceId === undefined) return null;
    const appliance = landingZoneAppliances[applianceId];
    if (!appliance) return null;

    // Handle both camelCase and snake_case for the zones array property
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const zones = (appliance as any).appLandingZones || (appliance as any).app_landing_zones;

    // Find the specific app landing zone that matches subscription and region
    // Handle both camelCase and Title Case property names from backend
    return zones?.find(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (appLz: any) => {
        const appLzSubscriptionId = appLz.subscriptionId || appLz['Subscription ID'];
        const appLzRegion = appLz.region || appLz['Region'];
        
        return (
          appLzSubscriptionId === subscriptionId && 
          appLzRegion?.toLowerCase() === region.toLowerCase()
        );
      }
    );
  };

  const handleStartEdit = (server: ServerConfig) => {
    setEditingId(server.id);
    setEditData({
      target_machine_name: server.target_machine_name || '',
      target_subscription: server.target_subscription || '',
      target_region: server.target_region || '',
      target_resource_group: server.target_resource_group || '',
      target_vnet: server.target_vnet || '',
      target_subnet: server.target_subnet || '',
      appliance_id: server.appliance_id || null,
    });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditData({
      target_machine_name: '',
      target_subscription: '',
      target_region: '',
      target_resource_group: '',
      target_vnet: '',
      target_subnet: '',
      appliance_id: null,
    });
  };

  const handleSaveEdit = async (serverId: number) => {
    if (!editData.target_machine_name.trim()) {
      alert('Target Machine Name is required');
      return;
    }

    // Get appliance and cache storage details
    const appliance = editData.appliance_id !== null ? getApplianceDetails(editData.appliance_id) : null;
    const cacheStorageZone = getCacheStorageForSubscriptionRegion(
      editData.target_subscription,
      editData.target_region,
      editData.appliance_id
    );

    console.log('[handleSaveEdit] appliance object:', appliance);
    console.log('[handleSaveEdit] appliance keys:', appliance ? Object.keys(appliance) : null);

    setSavingId(serverId);
    try {
      await onUpdateServer(serverId, {
        target_machine_name: editData.target_machine_name,
        target_subscription: editData.target_subscription,
        target_region: editData.target_region,
        target_resource_group: editData.target_resource_group,
        target_vnet: editData.target_vnet,
        target_subnet: editData.target_subnet,
        appliance_id: editData.appliance_id,
        // Extract actual names from appliance object - use camelCase properties
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        appliance_name: (appliance as any)?.applianceName || null,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        migrate_project_name: (appliance as any)?.migrateProjectName || null,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        cache_storage_account: (cacheStorageZone as any)?.cacheStorageAccount || (cacheStorageZone as any)?.['Cache Storage Account'],
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        cache_storage_rg: (cacheStorageZone as any)?.cacheStorageResourceGroup || (cacheStorageZone as any)?.['Cache Storage Resource Group'],
      });
      setEditingId(null);
      setEditData({
        target_machine_name: '',
        target_subscription: '',
        target_region: '',
        target_resource_group: '',
        target_vnet: '',
        target_subnet: '',
        appliance_id: null,
      });
    } finally {
      setSavingId(null);
    }
  };

  // Checkbox selection handlers
  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedServers(new Set(servers.map(s => s.id)));
    } else {
      setSelectedServers(new Set());
    }
  };

  const handleSelectServer = (serverId: number) => {
    const newSelected = new Set(selectedServers);
    if (newSelected.has(serverId)) {
      newSelected.delete(serverId);
    } else {
      newSelected.add(serverId);
    }
    setSelectedServers(newSelected);
  };

  const handleToggleExpand = (serverId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(serverId)) {
      newExpanded.delete(serverId);
    } else {
      newExpanded.add(serverId);
    }
    setExpandedRows(newExpanded);
  };

  // Validation function to check if server is discovered
  const handleValidateServers = async () => {
    const serversToValidate = selectedServers.size > 0 
      ? Array.from(selectedServers) 
      : servers.map(s => s.id);

    setValidatingServers(new Set(serversToValidate));

    try {
      // TODO: Replace with actual API call to check discovery status
      // For now, simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock discovered details - replace with actual API response
      const newDiscoveredDetails = new Map(discoveredDetails);
      serversToValidate.forEach(serverId => {
        const server = servers.find(s => s.id === serverId);
        if (server) {
          // Mock data - replace with actual API response
          newDiscoveredDetails.set(serverId, {
            discovered: Math.random() > 0.3, // 70% discovered for demo
            ipAddresses: ['10.0.1.10', '192.168.1.50'],
            nicCount: 2,
            osType: 'Windows Server 2019',
            cpuCores: 4,
            memoryMB: 16384,
            disks: [
              { name: 'C:', sizeGB: 127, type: 'OS' },
              { name: 'D:', sizeGB: 500, type: 'Data' },
              { name: 'E:', sizeGB: 1000, type: 'Data' },
            ]
          });
        }
      });

      setDiscoveredDetails(newDiscoveredDetails);
    } catch (error) {
      console.error('Validation failed:', error);
      alert('Failed to validate servers. Please try again.');
    } finally {
      setValidatingServers(new Set());
    }
  };

  const handleAddNew = () => {
    setIsAddingNew(true);
    setEditData({
      target_machine_name: '',
      target_subscription: '',
      target_region: '',
      target_resource_group: '',
      target_vnet: '',
      target_subnet: '',
      appliance_id: null,
    });
  };

  const handleCancelAddNew = () => {
    setIsAddingNew(false);
    setEditData({
      target_machine_name: '',
      target_subscription: '',
      target_region: '',
      target_resource_group: '',
      target_vnet: '',
      target_subnet: '',
      appliance_id: null,
    });
  };

  const handleSaveNew = async () => {
    if (!editData.target_machine_name.trim()) {
      alert('Target Machine Name is required');
      return;
    }

    // Get appliance and cache storage details
    const appliance = editData.appliance_id !== null ? getApplianceDetails(editData.appliance_id) : null;
    const cacheStorageZone = getCacheStorageForSubscriptionRegion(
      editData.target_subscription,
      editData.target_region,
      editData.appliance_id
    );

    console.log('[handleSaveNew] appliance object:', appliance);
    console.log('[handleSaveNew] appliance keys:', appliance ? Object.keys(appliance) : null);

    setSavingId('new');
    try{
      await onAddServer({
        target_machine_name: editData.target_machine_name,
        target_subscription: editData.target_subscription,
        target_region: editData.target_region,
        target_resource_group: editData.target_resource_group,
        target_vnet: editData.target_vnet,
        target_subnet: editData.target_subnet,
        appliance_id: editData.appliance_id,
        // Extract actual names from appliance object - use camelCase properties
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        appliance_name: (appliance as any)?.applianceName || null,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        migrate_project_name: (appliance as any)?.migrateProjectName || null,
        // Extract cache storage from matched zone
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        cache_storage_account: (cacheStorageZone as any)?.cacheStorageAccount || (cacheStorageZone as any)?.['Cache Storage Account'],
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        cache_storage_rg: (cacheStorageZone as any)?.cacheStorageResourceGroup || (cacheStorageZone as any)?.['Cache Storage Resource Group'],
        // Set defaults for required fields
        target_machine_sku: 'Standard_DS2_v2',
        target_disk_type: 'Premium_LRS',
      });
      setIsAddingNew(false);
      setEditData({
        target_machine_name: '',
        target_subscription: '',
        target_region: '',
        target_resource_group: '',
        target_vnet: '',
        target_subnet: '',
        appliance_id: null,
      });
    } finally {
      setSavingId(null);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Servers</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={validatingServers.size > 0 ? <CircularProgress size={16} /> : <ValidateIcon />}
            onClick={handleValidateServers}
            disabled={validatingServers.size > 0 || servers.length === 0}
          >
            Validate {selectedServers.size > 0 ? `(${selectedServers.size})` : 'All'}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleStartAddNew}
            disabled={isAddingNew || isLoading}
          >
            Add Server
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedServers.size > 0 && selectedServers.size < servers.length}
                  checked={servers.length > 0 && selectedServers.size === servers.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: 50 }}></TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Target Machine Name</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Subscription</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Region</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Appliance</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Target Resource Group</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Target VNet</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Target Subnet</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>VM SKU</TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {/* New server row (shown at top when adding) */}
            {isAddingNew && (
              <TableRow sx={{ bgcolor: 'action.hover' }}>
                <TableCell>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Enter machine name *"
                    value={editData.target_machine_name}
                    onChange={(e) =>
                      setEditData({ ...editData, target_machine_name: e.target.value })
                    }
                    autoFocus
                    disabled={savingId === 'new'}
                  />
                </TableCell>
                <TableCell>
                  <FormControl size="small" fullWidth disabled={savingId === 'new'}>
                    <Select
                      value={editData.target_subscription}
                      onChange={(e) => {
                        const newSubscription = e.target.value;
                        const matchedAppliance = findMatchingAppliance(newSubscription, editData.target_region);
                        setEditData({ 
                          ...editData, 
                          target_subscription: newSubscription,
                          appliance_id: matchedAppliance 
                        });
                      }}
                      displayEmpty
                    >
                      <MenuItem value="">
                        <em>Select subscription</em>
                      </MenuItem>
                      {availableSubscriptions.map(([id, name]) => (
                        <MenuItem key={id} value={id}>
                          {name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </TableCell>
                <TableCell>
                  <FormControl size="small" fullWidth disabled={savingId === 'new'}>
                    <Select
                      value={editData.target_region}
                      onChange={(e) => {
                        const newRegion = e.target.value;
                        const matchedAppliance = findMatchingAppliance(editData.target_subscription, newRegion);
                        setEditData({ 
                          ...editData, 
                          target_region: newRegion,
                          appliance_id: matchedAppliance 
                        });
                      }}
                      displayEmpty
                    >
                      <MenuItem value="">
                        <em>Select region</em>
                      </MenuItem>
                      {availableRegions.map((region) => (
                        <MenuItem key={region} value={region}>
                          {region}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </TableCell>
                <TableCell>
                  {editData.appliance_id !== null && editData.appliance_id !== undefined ? (
                    <Box>
                      <Box sx={{ fontWeight: 500 }}>
                        {(() => {
                          const appliance = getApplianceDetails(editData.appliance_id);
                          // Handle both camelCase and Title Case property names
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          return (appliance as any)?.applianceName || (appliance as any)?.['Appliance Name'] || '-';
                        })()}
                      </Box>
                      <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', mt: 0.5 }}>
                        {(() => {
                          const appliance = getApplianceDetails(editData.appliance_id);
                          if (!appliance) return null;
                          const matchedZone = getCacheStorageForSubscriptionRegion(
                            editData.target_subscription, 
                            editData.target_region, 
                            editData.appliance_id
                          );
                          // Handle both camelCase and Title Case property names
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          const cacheStorage = (matchedZone as any)?.cacheStorageAccount || (matchedZone as any)?.['Cache Storage Account'];
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          const projectName = (appliance as any)?.migrateProjectName || (appliance as any)?.['Migrate Project Name'];
                          return (
                            <Box component="span">
                              Project: {projectName}
                              {cacheStorage && ` | Cache: ${cacheStorage}`}
                            </Box>
                          );
                        })()}
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ color: 'text.disabled', fontStyle: 'italic', fontSize: '0.875rem' }}>
                      Select subscription & region first
                    </Box>
                  )}
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Enter resource group"
                    value={editData.target_resource_group}
                    onChange={(e) =>
                      setEditData({ ...editData, target_resource_group: e.target.value })
                    }
                    disabled={savingId === 'new'}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Enter VNet"
                    value={editData.target_vnet}
                    onChange={(e) => setEditData({ ...editData, target_vnet: e.target.value })}
                    disabled={savingId === 'new'}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Enter subnet"
                    value={editData.target_subnet}
                    onChange={(e) => setEditData({ ...editData, target_subnet: e.target.value })}
                    disabled={savingId === 'new'}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Standard_DS2_v2"
                    value={editData.target_machine_sku || 'Standard_DS2_v2'}
                    onChange={(e) => setEditData({ ...editData, target_machine_sku: e.target.value })}
                    disabled={savingId === 'new'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Save">
                    <span>
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={handleSaveNew}
                        disabled={savingId === 'new'}
                      >
                        {savingId === 'new' ? (
                          <CircularProgress size={20} />
                        ) : (
                          <SaveIcon fontSize="small" />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title="Cancel">
                    <span>
                      <IconButton
                        size="small"
                        onClick={handleCancelAddNew}
                        disabled={savingId === 'new'}
                      >
                        <CancelIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            )}

            {/* Existing servers */}
            {servers.map((server) => {
              const isEditing = editingId === server.id;
              const isSaving = savingId === server.id;
              const isExpanded = expandedRows.has(server.id);
              const isValidating = validatingServers.has(server.id);
              const discoveredData = discoveredDetails.get(server.id);

              return (
                <>
                  <TableRow key={server.id} hover={!isEditing}>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedServers.has(server.id)}
                        onChange={() => handleSelectServer(server.id)}
                        disabled={isEditing}
                      />
                    </TableCell>
                    <TableCell>
                      {discoveredData && discoveredData.discovered && (
                        <IconButton
                          size="small"
                          onClick={() => handleToggleExpand(server.id)}
                        >
                          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      )}
                    </TableCell>
                    <TableCell>
                    {isEditing ? (
                      <TextField
                        size="small"
                        fullWidth
                        value={editData.target_machine_name}
                        onChange={(e) =>
                          setEditData({ ...editData, target_machine_name: e.target.value })
                        }
                        disabled={isSaving}
                      />
                    ) : (
                      server.target_machine_name || '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {isEditing ? (
                      <FormControl size="small" fullWidth disabled={isSaving}>
                        <Select
                          value={editData.target_subscription}
                          onChange={(e) => {
                            const newSubscription = e.target.value;
                            const matchedAppliance = findMatchingAppliance(newSubscription, editData.target_region);
                            setEditData({ 
                              ...editData, 
                              target_subscription: newSubscription,
                              appliance_id: matchedAppliance 
                            });
                          }}
                        >
                          <MenuItem value="">
                            <em>Select subscription</em>
                          </MenuItem>
                          {availableSubscriptions.map(([id, name]) => (
                            <MenuItem key={id} value={id}>
                              {name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    ) : (
                      getSubscriptionName(server.target_subscription) || '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {isEditing ? (
                      <FormControl size="small" fullWidth disabled={isSaving}>
                        <Select
                          value={editData.target_region}
                          onChange={(e) => {
                            const newRegion = e.target.value;
                            const matchedAppliance = findMatchingAppliance(editData.target_subscription, newRegion);
                            setEditData({ 
                              ...editData, 
                              target_region: newRegion,
                              appliance_id: matchedAppliance 
                            });
                          }}
                        >
                          <MenuItem value="">
                            <em>Select region</em>
                          </MenuItem>
                          {availableRegions.map((region) => (
                            <MenuItem key={region} value={region}>
                              {region}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    ) : (
                      server.target_region || '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {isEditing ? (
                      editData.appliance_id !== null && editData.appliance_id !== undefined ? (
                        <Box>
                          <Box sx={{ fontWeight: 500 }}>
                            {(() => {
                              const appliance = getApplianceDetails(editData.appliance_id);
                              // Handle both camelCase and Title Case property names
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any
                              return (appliance as any)?.applianceName || (appliance as any)?.['Appliance Name'] || '-';
                            })()}
                          </Box>
                          <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', mt: 0.5 }}>
                            {(() => {
                              const appliance = getApplianceDetails(editData.appliance_id);
                              if (!appliance) return null;
                              const matchedZone = getCacheStorageForSubscriptionRegion(
                                editData.target_subscription, 
                                editData.target_region, 
                                editData.appliance_id
                              );
                              // Handle both camelCase and Title Case property names
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any
                              const cacheStorage = (matchedZone as any)?.cacheStorageAccount || (matchedZone as any)?.['Cache Storage Account'];
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any
                              const projectName = (appliance as any)?.migrateProjectName || (appliance as any)?.['Migrate Project Name'];
                              return (
                                <Box component="span">
                                  Project: {projectName}
                                  {cacheStorage && ` | Cache: ${cacheStorage}`}
                                </Box>
                              );
                            })()}
                          </Box>
                        </Box>
                      ) : (
                        <Box sx={{ color: 'text.disabled', fontStyle: 'italic', fontSize: '0.875rem' }}>
                          Select subscription & region first
                        </Box>
                      )
                    ) : (
                      <Box>
                        <Box>{server.appliance_name || '-'}</Box>
                        {server.appliance_id !== null && server.appliance_id !== undefined && (
                          <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', mt: 0.5 }}>
                            Project: {server.migrate_project_name || '-'}
                            {server.cache_storage_account && ` | Cache: ${server.cache_storage_account}`}
                          </Box>
                        )}
                      </Box>
                    )}
                  </TableCell>
                  <TableCell>
                    {isEditing ? (
                      <TextField
                        size="small"
                        fullWidth
                        value={editData.target_resource_group}
                        onChange={(e) =>
                          setEditData({ ...editData, target_resource_group: e.target.value })
                        }
                        disabled={isSaving}
                      />
                    ) : (
                      server.target_resource_group || '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {isEditing ? (
                      <TextField
                        size="small"
                        fullWidth
                        value={editData.target_vnet}
                        onChange={(e) =>
                          setEditData({ ...editData, target_vnet: e.target.value })
                        }
                        disabled={isSaving}
                      />
                    ) : (
                      server.target_vnet || '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {isEditing ? (
                      <TextField
                        size="small"
                        fullWidth
                        value={editData.target_subnet}
                        onChange={(e) =>
                          setEditData({ ...editData, target_subnet: e.target.value })
                        }
                        disabled={isSaving}
                      />
                    ) : (
                      server.target_subnet || '-'
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {isEditing ? (
                      <>
                        <Tooltip title="Save">
                          <span>
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleSaveEdit(server.id)}
                              disabled={isSaving}
                            >
                              {isSaving ? (
                                <CircularProgress size={20} />
                              ) : (
                                <SaveIcon fontSize="small" />
                              )}
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="Cancel">
                          <span>
                            <IconButton
                              size="small"
                              onClick={handleCancelEdit}
                              disabled={isSaving}
                            >
                              <CancelIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </>
                    ) : (
                      <>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleStartEdit(server)}
                            disabled={editingId !== null || isAddingNew}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Are you sure you want to delete server "${server.target_machine_name}"?`
                                )
                              ) {
                                onDeleteServer(server.id);
                              }
                            }}
                            disabled={editingId !== null || isAddingNew}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}

            {/* Empty state */}
            {servers.length === 0 && !isAddingNew && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Box sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary" gutterBottom>
                      No servers configured yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Click "Add Server" to create your first server configuration
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            )}

            {/* Loading state */}
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <CircularProgress sx={{ my: 3 }} />
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
