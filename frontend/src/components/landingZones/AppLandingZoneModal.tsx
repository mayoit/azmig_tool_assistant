import { useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  FormHelperText,
  CircularProgress,
  Alert,
  FormControlLabel,
  Checkbox,
  TextField,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery } from '@tanstack/react-query';
import azureResourcesService from '../../services/azureResources';

const appLandingZoneSchema = z.object({
  subscriptionId: z.string().min(1, 'Subscription is required'),
  subscriptionName: z.string().optional(),  // Display name for dropdown
  region: z.string().min(1, 'Region is required'),
  cacheStorageAccount: z.string().min(1, 'Cache Storage Account is required'),
  cacheStorageResourceGroup: z.string().min(1, 'Cache Storage Resource Group is required'),
  isNewResource: z.boolean(),
  allowedSkus: z.array(z.string()).optional(),
});

type AppLandingZoneFormData = z.infer<typeof appLandingZoneSchema>;

interface ProjectSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  disk_types: string[];
  redundancy_types: string[];
}

interface AppLandingZoneModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: AppLandingZoneFormData) => void;
  initialData?: AppLandingZoneFormData | null;
  projectName: string;
  projectSettings?: ProjectSettings | null;
  projectId: number;
  isAuthenticated: boolean;
}

export default function AppLandingZoneModal({
  open,
  onClose,
  onSubmit,
  initialData,
  projectName,
  projectSettings,
  projectId,
  isAuthenticated,
}: AppLandingZoneModalProps) {
  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<AppLandingZoneFormData>({
    resolver: zodResolver(appLandingZoneSchema),
    defaultValues: {
      subscriptionId: '',
      subscriptionName: '',
      region: '',
      cacheStorageAccount: '',
      cacheStorageResourceGroup: '',
      allowedSkus: [],
      isNewResource: false,
    },
  });

  // Watch form values for cascading dropdowns and isNewResource flag
  const watchedSubscription = watch('subscriptionId');
  const watchedCacheResourceGroup = watch('cacheStorageResourceGroup');
  const watchedIsNewResource = watch('isNewResource');

  const availableRegions = projectSettings?.allowed_regions || [];
  const availableSkus = projectSettings?.allowed_vm_skus || [];
  
  // Fallback regions if project settings not configured
  const defaultRegions = ['uksouth', 'ukwest', 'eastus', 'westus', 'northeurope', 'westeurope'];
  const regionsToShow = availableRegions.length > 0 ? availableRegions : defaultRegions;
  const skusToShow = availableSkus.length > 0 ? availableSkus : [];

  // Fetch Azure subscriptions
  const { data: subscriptions = [], isLoading: loadingSubscriptions, error: subscriptionsError } = useQuery({
    queryKey: ['azure-subscriptions', projectId],
    queryFn: () => {
      console.log('🔍 Fetching subscriptions for project:', projectId);
      return azureResourcesService.getSubscriptions(projectId);
    },
    enabled: isAuthenticated && open && !watchedIsNewResource,
  });

  // Debug: Log subscription query state
  useEffect(() => {
    console.log('📊 Subscription Query State:', {
      isAuthenticated,
      open,
      enabled: isAuthenticated && open,
      loading: loadingSubscriptions,
      subscriptionsCount: subscriptions.length,
      error: subscriptionsError,
    });
  }, [isAuthenticated, open, loadingSubscriptions, subscriptions, subscriptionsError]);

  // Fetch resource groups for cache storage RG dropdown
  const { data: resourceGroups = [], isLoading: loadingResourceGroups } = useQuery({
    queryKey: ['azure-resource-groups', projectId, watchedSubscription],
    queryFn: () => azureResourcesService.getResourceGroups(projectId, watchedSubscription),
    enabled: isAuthenticated && !!watchedSubscription && !watchedIsNewResource,
  });

  // Fetch storage accounts for cache storage account dropdown
  const { data: storageAccounts = [], isLoading: loadingStorageAccounts } = useQuery({
    queryKey: ['azure-storage-accounts', projectId, watchedSubscription, watchedCacheResourceGroup],
    queryFn: () => azureResourcesService.getStorageAccounts(projectId, watchedSubscription, watchedCacheResourceGroup),
    enabled: isAuthenticated && !!watchedSubscription && !!watchedCacheResourceGroup && !watchedIsNewResource,
  });

  useEffect(() => {
    if (open) {
      reset(
        initialData || {
          subscriptionId: '',
          subscriptionName: '',
          region: '',
          cacheStorageAccount: '',
          cacheStorageResourceGroup: '',
          allowedSkus: [],
          isNewResource: false,
        }
      );
    }
  }, [open, initialData, reset]);

  const handleFormSubmit = (data: AppLandingZoneFormData) => {
    onSubmit(data);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Add Application Landing Zone - {projectName}</DialogTitle>
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Authentication Warning */}
            {!isAuthenticated && (
              <Alert severity="warning">
                Please configure Azure authentication in the Overview tab before adding landing zones.
              </Alert>
            )}

            {/* Subscription Fetch Error */}
            {subscriptionsError && (
              <Alert severity="error">
                Failed to fetch Azure subscriptions: {subscriptionsError.message}
                <br />
                <small>Check browser console for details.</small>
              </Alert>
            )}

            {/* Debug Info - Remove after testing */}
            {isAuthenticated && subscriptions.length === 0 && !loadingSubscriptions && !subscriptionsError && (
              <Alert severity="info">
                Debug: Authentication OK, but no subscriptions returned from API.
                Check backend logs and Azure credentials.
              </Alert>
            )}

            {/* Mark as New Resource Checkbox */}
            <Controller
              name="isNewResource"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={field.value || false}
                      onChange={(e) => field.onChange(e.target.checked)}
                    />
                  }
                  label="Mark as new resource (resources don't exist in Azure yet - validation will be skipped)"
                />
              )}
            />

            {/* Info Alert when isNewResource is checked */}
            {watchedIsNewResource && (
              <Alert severity="info">
                This landing zone is marked as new. You can manually enter resource identifiers below.
                Validation will be skipped for this landing zone.
              </Alert>
            )}

            {/* Subscription Dropdown or TextField */}
            <Controller
              name="subscriptionId"
              control={control}
              render={({ field }) =>
                watchedIsNewResource ? (
                  <TextField
                    {...field}
                    label="Azure Subscription ID *"
                    fullWidth
                    error={!!errors.subscriptionId}
                    helperText={errors.subscriptionId?.message || 'Enter the subscription ID manually'}
                  />
                ) : (
                  <FormControl fullWidth error={!!errors.subscriptionId} disabled={!isAuthenticated}>
                    <InputLabel id="subscription-label">Azure Subscription *</InputLabel>
                    <Select
                      value={field.value}
                      onChange={(e) => {
                        const selectedSub = subscriptions.find(s => s.subscription_id === e.target.value);
                        field.onChange(e.target.value);
                        // Also update the subscriptionName field
                        if (selectedSub) {
                          const formValues = watch();
                          reset({
                            ...formValues,
                            subscriptionId: e.target.value,
                            subscriptionName: selectedSub.display_name,
                          });
                        }
                      }}
                      labelId="subscription-label"
                      label="Azure Subscription *"
                      disabled={!isAuthenticated || loadingSubscriptions}
                    >
                      {loadingSubscriptions ? (
                        <MenuItem disabled value="">
                          <CircularProgress size={20} sx={{ mr: 1 }} /> Loading subscriptions...
                        </MenuItem>
                      ) : subscriptions.length === 0 ? (
                        <MenuItem disabled value="">
                          <em>No subscriptions found</em>
                        </MenuItem>
                      ) : (
                        subscriptions.map((sub) => (
                          <MenuItem key={sub.subscription_id} value={sub.subscription_id}>
                            {sub.display_name}
                          </MenuItem>
                        ))
                      )}
                    </Select>
                    {errors.subscriptionId && (
                      <FormHelperText>{errors.subscriptionId.message}</FormHelperText>
                    )}
                  </FormControl>
                )
              }
            />

            {/* Region Dropdown */}
            <Controller
              name="region"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.region}>
                  <InputLabel id="region-label">Region *</InputLabel>
                  <Select
                    {...field}
                    labelId="region-label"
                    label="Region *"
                  >
                    {regionsToShow.map((region) => (
                      <MenuItem key={region} value={region}>
                        {region}
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.region && (
                    <FormHelperText>{errors.region.message}</FormHelperText>
                  )}
                  {regionsToShow.length === defaultRegions.length && (
                    <FormHelperText>
                      Using default regions. Configure custom regions in Settings tab.
                    </FormHelperText>
                  )}
                </FormControl>
              )}
            />

            {/* Cache Storage Resource Group Dropdown or TextField */}
            <Controller
              name="cacheStorageResourceGroup"
              control={control}
              render={({ field }) =>
                watchedIsNewResource ? (
                  <TextField
                    {...field}
                    label="Cache Storage Resource Group *"
                    fullWidth
                    error={!!errors.cacheStorageResourceGroup}
                    helperText={errors.cacheStorageResourceGroup?.message || 'Enter the resource group name manually'}
                  />
                ) : (
                  <FormControl 
                    fullWidth 
                    error={!!errors.cacheStorageResourceGroup}
                    disabled={!watchedSubscription}
                  >
                    <InputLabel id="cache-rg-label">Cache Storage Resource Group *</InputLabel>
                    <Select
                      {...field}
                      labelId="cache-rg-label"
                      label="Cache Storage Resource Group *"
                      disabled={!watchedSubscription || loadingResourceGroups}
                    >
                      {loadingResourceGroups ? (
                        <MenuItem disabled value="">
                          <CircularProgress size={20} sx={{ mr: 1 }} /> Loading resource groups...
                        </MenuItem>
                      ) : resourceGroups.length === 0 ? (
                        <MenuItem disabled value="">
                          <em>{watchedSubscription ? 'No resource groups found' : 'Select a subscription first'}</em>
                        </MenuItem>
                      ) : (
                        resourceGroups.map((rg) => (
                          <MenuItem key={rg.name} value={rg.name}>
                            {rg.name}
                          </MenuItem>
                        ))
                      )}
                    </Select>
                    {errors.cacheStorageResourceGroup && (
                      <FormHelperText>{errors.cacheStorageResourceGroup.message}</FormHelperText>
                    )}
                  </FormControl>
                )
              }
            />

            {/* Cache Storage Account Dropdown or TextField */}
            <Controller
              name="cacheStorageAccount"
              control={control}
              render={({ field }) =>
                watchedIsNewResource ? (
                  <TextField
                    {...field}
                    label="Cache Storage Account *"
                    fullWidth
                    error={!!errors.cacheStorageAccount}
                    helperText={errors.cacheStorageAccount?.message || 'Enter the storage account name manually'}
                  />
                ) : (
                  <FormControl 
                    fullWidth 
                    error={!!errors.cacheStorageAccount}
                    disabled={!watchedCacheResourceGroup}
                  >
                    <InputLabel id="cache-storage-label">Cache Storage Account *</InputLabel>
                    <Select
                      {...field}
                      labelId="cache-storage-label"
                      label="Cache Storage Account *"
                      disabled={!watchedCacheResourceGroup || loadingStorageAccounts}
                    >
                      {loadingStorageAccounts ? (
                        <MenuItem disabled value="">
                          <CircularProgress size={20} sx={{ mr: 1 }} /> Loading storage accounts...
                        </MenuItem>
                      ) : storageAccounts.length === 0 ? (
                        <MenuItem disabled value="">
                          <em>{watchedCacheResourceGroup ? 'No storage accounts found' : 'Select a resource group first'}</em>
                        </MenuItem>
                      ) : (
                        storageAccounts.map((account) => (
                          <MenuItem key={account.name} value={account.name}>
                            {account.name} ({account.kind})
                          </MenuItem>
                        ))
                      )}
                    </Select>
                    {errors.cacheStorageAccount && (
                      <FormHelperText>{errors.cacheStorageAccount.message}</FormHelperText>
                    )}
                  </FormControl>
                )
              }
            />

            {/* Allowed SKUs Multi-Select Field */}
            <Controller
              name="allowedSkus"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.allowedSkus}>
                  <InputLabel id="allowed-skus-label">
                    Allowed VM SKUs (Optional)
                  </InputLabel>
                  <Select
                    {...field}
                    labelId="allowed-skus-label"
                    label="Allowed VM SKUs (Optional)"
                    multiple
                    disabled={skusToShow.length === 0}
                    input={<OutlinedInput label="Allowed VM SKUs (Optional)" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(selected as string[]).map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {skusToShow.map((sku) => (
                      <MenuItem key={sku} value={sku}>
                        {sku}
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.allowedSkus && (
                    <FormHelperText>{errors.allowedSkus.message}</FormHelperText>
                  )}
                  {skusToShow.length === 0 && (
                    <FormHelperText>
                      No VM SKUs configured. Add them in Settings tab to enable restrictions.
                    </FormHelperText>
                  )}
                </FormControl>
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            type="submit" 
            variant="contained"
            disabled={!isAuthenticated}
          >
            Add Landing Zone
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
