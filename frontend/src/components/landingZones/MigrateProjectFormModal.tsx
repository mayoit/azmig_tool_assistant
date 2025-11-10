import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Box,
  Typography,
  IconButton,
  Divider,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Chip,
  OutlinedInput,
  FormControlLabel,
  Checkbox,
  Autocomplete,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import azureResourcesService from '../../services/azureResources';

const appLandingZoneSchema = z.object({
  subscriptionId: z.string().min(1, 'Subscription is required'),
  region: z.string().min(1, 'Region is required'),
  cacheStorageAccount: z.string().min(1, 'Cache Storage Account is required'),
  cacheStorageResourceGroup: z.string().min(1, 'Cache Storage Resource Group is required'),
  isNewResource: z.boolean(),
  allowedSkus: z.array(z.string()).optional(),
});

const migrateProjectSchema = z.object({
  migrateProjectSubscription: z.string().min(1, 'Migrate Project Subscription is required'),
  migrateResourceGroup: z.string().min(1, 'Migrate Resource Group is required'),
  migrateProjectName: z.string().min(1, 'Migrate Project Name is required'),
  applianceName: z.string().min(1, 'Appliance Name is required'),
  appLandingZones: z.array(appLandingZoneSchema).min(1, 'At least one app landing zone is required'),
});

type MigrateProjectFormData = z.infer<typeof migrateProjectSchema>;

interface ProjectSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  disk_types: string[];
  redundancy_types: string[];
}

interface MigrateProjectFormModalProps {
  open: boolean;
  onClose: () => void;
  projectId: number;
  projectName: string;
  editMode?: boolean;
  editIndex?: number;
  initialData?: MigrateProjectFormData;
  projectSettings?: ProjectSettings | null;
  isAuthenticated: boolean;
}

export default function MigrateProjectFormModal({
  open,
  onClose,
  projectId,
  projectName,
  editMode = false,
  editIndex,
  initialData,
  projectSettings,
  isAuthenticated,
}: MigrateProjectFormModalProps) {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [selectedMigrateSubscription, setSelectedMigrateSubscription] = useState<string>('');
  const [selectedMigrateResourceGroup, setSelectedMigrateResourceGroup] = useState<string>('');
  const [selectedMigrateProjectName, setSelectedMigrateProjectName] = useState<string>('');

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
      console.log('🔍 [MigrateProject] Fetching subscriptions for project:', projectId);
      return azureResourcesService.getSubscriptions(projectId);
    },
    enabled: isAuthenticated && open,
  });

  // Fetch resource groups for migrate project subscription
  const { data: migrateResourceGroups = [], isLoading: loadingMigrateRGs } = useQuery({
    queryKey: ['azure-resource-groups', projectId, selectedMigrateSubscription],
    queryFn: () => azureResourcesService.getResourceGroups(projectId, selectedMigrateSubscription),
    enabled: isAuthenticated && open && !!selectedMigrateSubscription,
  });

  // Fetch Azure Migrate projects
  const { data: migrateProjects = [], isLoading: loadingMigrateProjects } = useQuery({
    queryKey: ['azure-migrate-projects', projectId, selectedMigrateSubscription, selectedMigrateResourceGroup],
    queryFn: () => azureResourcesService.getMigrateProjects(projectId, selectedMigrateSubscription, selectedMigrateResourceGroup),
    enabled: isAuthenticated && open && !!selectedMigrateSubscription && !!selectedMigrateResourceGroup,
  });

  // Fetch Azure Migrate appliances
  const { data: migrateAppliances = [], isLoading: loadingAppliances } = useQuery({
    queryKey: ['azure-migrate-appliances', projectId, selectedMigrateSubscription, selectedMigrateResourceGroup, selectedMigrateProjectName],
    queryFn: () => azureResourcesService.getMigrateAppliances(projectId, selectedMigrateSubscription, selectedMigrateResourceGroup, selectedMigrateProjectName),
    enabled: isAuthenticated && open && !!selectedMigrateSubscription && !!selectedMigrateResourceGroup && !!selectedMigrateProjectName,
  });

  // Debug: Log subscription query state
  useEffect(() => {
    console.log('📊 [MigrateProject] Subscription Query State:', {
      isAuthenticated,
      open,
      enabled: isAuthenticated && open,
      loading: loadingSubscriptions,
      subscriptionsCount: subscriptions.length,
      error: subscriptionsError,
    });
  }, [isAuthenticated, open, loadingSubscriptions, subscriptions, subscriptionsError]);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MigrateProjectFormData>({
    resolver: zodResolver(migrateProjectSchema),
    defaultValues: initialData || {
      migrateProjectSubscription: '',
      migrateResourceGroup: '',
      migrateProjectName: '',
      applianceName: '',
      appLandingZones: [
        {
          subscriptionId: '',
          region: '',
          cacheStorageAccount: '',
          cacheStorageResourceGroup: '',
          allowedSkus: [],
          isNewResource: false as boolean,
        },
      ],
    } as MigrateProjectFormData,
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'appLandingZones',
  });

  // Reset form when initialData changes (switching between edit/create modes)
  useEffect(() => {
    if (open) {
      if (initialData) {
        reset(initialData);
      } else {
        reset({
          migrateProjectSubscription: '',
          migrateResourceGroup: '',
          migrateProjectName: '',
          applianceName: '',
          appLandingZones: [
            {
              subscriptionId: '',
              region: '',
              cacheStorageAccount: '',
              cacheStorageResourceGroup: '',
              allowedSkus: [],
              isNewResource: false,
            },
          ],
        });
      }
    }
  }, [open, initialData, reset]);

  const mutation = useMutation({
    mutationFn: async (data: MigrateProjectFormData) => {
      // Transform to match the backend schema (snake_case)
      const payload = {
        'Migrate Project Subscription': data.migrateProjectSubscription,
        'Migrate Resource Group': data.migrateResourceGroup,
        'Migrate Project Name': data.migrateProjectName,
        'Appliance Name': data.applianceName,
        app_landing_zones: data.appLandingZones.map((zone) => ({
          'Subscription ID': zone.subscriptionId,
          'Cache Storage Account': zone.cacheStorageAccount,
          Region: zone.region,
          'Cache Storage Resource Group': zone.cacheStorageResourceGroup,
        })),
      };

      // Get current project to get existing lz_migrate_projects
      const projectResponse = await api.get(`/projects/${projectId}`);
      const currentProjects = projectResponse.data.lz_migrate_projects || [];
      
      let updatedProjects;
      if (editMode && editIndex !== undefined) {
        // Update existing migrate project at the specified index
        updatedProjects = [...currentProjects];
        updatedProjects[editIndex] = payload;
      } else {
        // Append new migrate project to the array
        updatedProjects = [...currentProjects, payload];
      }

      // Update project metadata
      await api.put(`/projects/${projectId}`, {
        metadata_json: {
          lz_migrate_projects: updatedProjects,
        },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setSubmitError(null);
      onClose();
      reset();
    },
    onError: (error: unknown) => {
      const err = error as { response?: { data?: { detail?: string } } };
      setSubmitError(err.response?.data?.detail || 'Failed to add migrate project');
    },
  });

  const onSubmit = (data: MigrateProjectFormData) => {
    mutation.mutate(data);
  };

  const handleClose = () => {
    if (!mutation.isPending) {
      reset();
      setSubmitError(null);
      onClose();
    }
  };

  return (
		<Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
			<DialogTitle>
				{editMode ? 'Edit' : 'Add'} Migrate Project - {projectName}
			</DialogTitle>
			<form onSubmit={handleSubmit(onSubmit)}>
				<DialogContent>
					{(mutation.isError || submitError) && (
						<Alert severity="error" sx={{ mb: 2 }}>
							{submitError ||
								'Failed to add migrate project. Please try again.'}
						</Alert>
					)}

					{/* Authentication Warning */}
					{!isAuthenticated && (
						<Alert severity="warning" sx={{ mb: 2 }}>
							Please configure Azure authentication in the Overview tab before
							adding landing zones.
						</Alert>
					)}

					{/* Subscription Fetch Error */}
					{subscriptionsError && (
						<Alert severity="error" sx={{ mb: 2 }}>
							Failed to fetch Azure subscriptions: {subscriptionsError.message}
							<br />
							<small>Check browser console for details.</small>
						</Alert>
					)}

					{/* Debug Info - Remove after testing */}
					{isAuthenticated &&
						subscriptions.length === 0 &&
						!loadingSubscriptions &&
						!subscriptionsError && (
							<Alert severity="info" sx={{ mb: 2 }}>
								Debug: Authentication OK, but no subscriptions returned from
								API. Check backend logs and Azure credentials.
							</Alert>
						)}

					<Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
						Migrate Project Details
					</Typography>

					<Controller
						name="migrateProjectSubscription"
						control={control}
						render={({ field }) => (
							<Autocomplete
								{...field}
								options={subscriptions}
								getOptionLabel={(option) => typeof option === 'string' ? option : option.display_name}
								value={subscriptions.find(sub => sub.subscription_id === field.value) || null}
								onChange={(_, newValue) => {
									const subscriptionId = newValue?.subscription_id || '';
									field.onChange(subscriptionId);
									setSelectedMigrateSubscription(subscriptionId);
								}}
								disabled={!isAuthenticated || loadingSubscriptions}
								loading={loadingSubscriptions}
								renderInput={(params) => (
									<TextField
										{...params}
										label="Migrate Project Subscription *"
										margin="normal"
										error={!!errors.migrateProjectSubscription}
										helperText={errors.migrateProjectSubscription?.message}
										InputProps={{
											...params.InputProps,
											endAdornment: (
												<>
													{loadingSubscriptions ? <CircularProgress size={20} /> : null}
													{params.InputProps.endAdornment}
												</>
											),
										}}
									/>
								)}
								noOptionsText={subscriptions.length === 0 ? "No subscriptions found" : "No options"}
							/>
						)}
					/>

					<Controller
						name="migrateResourceGroup"
						control={control}
						render={({ field }) => (
							<Autocomplete
								{...field}
								options={migrateResourceGroups}
								getOptionLabel={(option) => typeof option === 'string' ? option : option.name}
								value={migrateResourceGroups.find(rg => rg.name === field.value) || null}
								onChange={(_, newValue) => {
									const rgName = newValue?.name || '';
									field.onChange(rgName);
									setSelectedMigrateResourceGroup(rgName);
								}}
								disabled={!isAuthenticated || !selectedMigrateSubscription || loadingMigrateRGs}
								loading={loadingMigrateRGs}
								renderInput={(params) => (
									<TextField
										{...params}
										label="Migrate Resource Group *"
										margin="normal"
										error={!!errors.migrateResourceGroup}
										helperText={errors.migrateResourceGroup?.message || (!selectedMigrateSubscription ? 'Select a subscription first' : '')}
										InputProps={{
											...params.InputProps,
											endAdornment: (
												<>
													{loadingMigrateRGs ? <CircularProgress size={20} /> : null}
													{params.InputProps.endAdornment}
												</>
											),
										}}
									/>
								)}
								noOptionsText={migrateResourceGroups.length === 0 ? "No resource groups found" : "No options"}
							/>
						)}
					/>

					<Controller
						name="migrateProjectName"
						control={control}
						render={({ field }) => (
							<Autocomplete
								{...field}
								options={migrateProjects}
								getOptionLabel={(option) => typeof option === 'string' ? option : option.name}
								value={migrateProjects.find(mp => mp.name === field.value) || null}
								onChange={(_, newValue) => {
									const projectName = newValue?.name || '';
									field.onChange(projectName);
									setSelectedMigrateProjectName(projectName);
								}}
								disabled={!selectedMigrateResourceGroup || loadingMigrateProjects}
								loading={loadingMigrateProjects}
								renderInput={(params) => (
									<TextField
										{...params}
										label="Migrate Project Name *"
										margin="normal"
										error={!!errors.migrateProjectName}
										helperText={errors.migrateProjectName?.message || (!selectedMigrateResourceGroup ? 'Select a resource group first' : '')}
										InputProps={{
											...params.InputProps,
											endAdornment: (
												<>
													{loadingMigrateProjects ? <CircularProgress size={20} /> : null}
													{params.InputProps.endAdornment}
												</>
											),
										}}
									/>
								)}
								noOptionsText={migrateProjects.length === 0 ? "No migrate projects found" : "No options"}
							/>
						)}
					/>

					<Controller
						name="applianceName"
						control={control}
						render={({ field }) => (
							<Autocomplete
								{...field}
								options={migrateAppliances}
								getOptionLabel={(option) => typeof option === 'string' ? option : `${option.name} (${option.appliance_type})`}
								value={migrateAppliances.find(app => app.name === field.value) || null}
								onChange={(_, newValue) => {
									const applianceName = newValue?.name || '';
									field.onChange(applianceName);
								}}
								disabled={!selectedMigrateProjectName || loadingAppliances}
								loading={loadingAppliances}
								renderInput={(params) => (
									<TextField
										{...params}
										label="Appliance Name *"
										margin="normal"
										error={!!errors.applianceName}
										helperText={errors.applianceName?.message || (!selectedMigrateProjectName ? 'Select a migrate project first' : '')}
										InputProps={{
											...params.InputProps,
											endAdornment: (
												<>
													{loadingAppliances ? <CircularProgress size={20} /> : null}
													{params.InputProps.endAdornment}
												</>
											),
										}}
									/>
								)}
								noOptionsText={migrateAppliances.length === 0 ? "No appliances found" : "No options"}
							/>
						)}
					/>
					<Divider sx={{ my: 3 }} />

					<Box
						sx={{
							display: 'flex',
							justifyContent: 'space-between',
							alignItems: 'center',
							mb: 2,
						}}
					>
						<Typography variant="h6">Application Landing Zones</Typography>
						<Button
							startIcon={<AddIcon />}
							onClick={() =>
								append({
									subscriptionId: '',
									region: '',
									cacheStorageAccount: '',
									cacheStorageResourceGroup: '',
									allowedSkus: [],
									isNewResource: false,
								})
							}
						>
							Add Landing Zone
						</Button>
					</Box>

					{errors.appLandingZones?.root && (
						<Alert severity="error" sx={{ mb: 2 }}>
							{errors.appLandingZones.root.message}
						</Alert>
					)}

					<Stack spacing={2}>
						{fields.map((field, index) => (
							<Box
								key={field.id}
								sx={{
									p: 2,
									border: 1,
									borderColor: 'divider',
									borderRadius: 1,
									backgroundColor: 'action.hover',
								}}
							>
								<Box
									sx={{
										display: 'flex',
										justifyContent: 'space-between',
										alignItems: 'center',
										mb: 2,
									}}
								>
									<Typography variant="subtitle1" fontWeight="medium">
										Landing Zone {index + 1}
									</Typography>
									{fields.length > 1 && (
										<IconButton
											color="error"
											onClick={() => remove(index)}
											size="small"
										>
											<DeleteIcon />
										</IconButton>
									)}
								</Box>

								{/* Mark as New Resource Checkbox */}
								<Controller
									name={`appLandingZones.${index}.isNewResource`}
									control={control}
									render={({ field }) => (
										<FormControlLabel
											control={
												<Checkbox
													checked={field.value || false}
													onChange={(e) => field.onChange(e.target.checked)}
												/>
											}
											label="Mark as new resource (validation will be skipped)"
											sx={{ mb: 1 }}
										/>
									)}
								/>

								<Controller
									name={`appLandingZones.${index}.subscriptionId`}
									control={control}
									render={({ field }) => (
										<FormControl
											fullWidth
											margin="normal"
											error={!!errors.appLandingZones?.[index]?.subscriptionId}
											disabled={!isAuthenticated}
										>
											<InputLabel id={`subscription-label-${index}`}>
												Azure Subscription *
											</InputLabel>
											<Select
												{...field}
												labelId={`subscription-label-${index}`}
												label="Azure Subscription *"
												disabled={!isAuthenticated || loadingSubscriptions}
											>
												{loadingSubscriptions ? (
													<MenuItem disabled value="">
														<CircularProgress size={20} sx={{ mr: 1 }} />{' '}
														Loading subscriptions...
													</MenuItem>
												) : subscriptions.length === 0 ? (
													<MenuItem disabled value="">
														<em>No subscriptions found</em>
													</MenuItem>
												) : (
													subscriptions.map((sub) => (
														<MenuItem
															key={sub.subscription_id}
															value={sub.subscription_id}
														>
															{sub.display_name}
														</MenuItem>
													))
												)}
											</Select>
											{errors.appLandingZones?.[index]?.subscriptionId && (
												<FormHelperText>
													{
														errors.appLandingZones[index]?.subscriptionId
															?.message
													}
												</FormHelperText>
											)}
										</FormControl>
									)}
								/>

								<Controller
									name={`appLandingZones.${index}.region`}
									control={control}
									render={({ field }) => (
										<FormControl
											fullWidth
											margin="normal"
											error={!!errors.appLandingZones?.[index]?.region}
										>
											<InputLabel id={`region-label-${index}`}>
												Region *
											</InputLabel>
											<Select
												{...field}
												labelId={`region-label-${index}`}
												label="Region *"
											>
												{regionsToShow.map((region) => (
													<MenuItem key={region} value={region}>
														{region}
													</MenuItem>
												))}
											</Select>
											{errors.appLandingZones?.[index]?.region && (
												<FormHelperText>
													{errors.appLandingZones[index]?.region?.message}
												</FormHelperText>
											)}
											{regionsToShow.length === defaultRegions.length && (
												<FormHelperText>
													Using default regions. Configure custom regions in
													Settings tab.
												</FormHelperText>
											)}
										</FormControl>
									)}
								/>

								<Controller
									name={`appLandingZones.${index}.cacheStorageAccount`}
									control={control}
									render={({ field }) => (
										<TextField
											{...field}
											label="Cache Storage Account"
											fullWidth
											margin="normal"
											required
											error={
												!!errors.appLandingZones?.[index]?.cacheStorageAccount
											}
											helperText={
												errors.appLandingZones?.[index]?.cacheStorageAccount
													?.message
											}
										/>
									)}
								/>

								<Controller
									name={`appLandingZones.${index}.cacheStorageResourceGroup`}
									control={control}
									render={({ field }) => (
										<TextField
											{...field}
											label="Cache Storage Resource Group"
											fullWidth
											margin="normal"
											required
											error={
												!!errors.appLandingZones?.[index]
													?.cacheStorageResourceGroup
											}
											helperText={
												errors.appLandingZones?.[index]
													?.cacheStorageResourceGroup?.message
											}
										/>
									)}
								/>

								{/* Allowed SKUs Multi-Select Field */}
								<Controller
									name={`appLandingZones.${index}.allowedSkus`}
									control={control}
									render={({ field }) => (
										<FormControl
											fullWidth
											margin="normal"
											error={!!errors.appLandingZones?.[index]?.allowedSkus}
										>
											<InputLabel id={`allowed-skus-label-${index}`}>
												Allowed VM SKUs (Optional)
											</InputLabel>
											<Select
												{...field}
												labelId={`allowed-skus-label-${index}`}
												label="Allowed VM SKUs (Optional)"
												multiple
												disabled={skusToShow.length === 0}
												input={
													<OutlinedInput label="Allowed VM SKUs (Optional)" />
												}
												renderValue={(selected) => (
													<Box
														sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}
													>
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
											{errors.appLandingZones?.[index]?.allowedSkus && (
												<FormHelperText>
													{errors.appLandingZones[index]?.allowedSkus?.message}
												</FormHelperText>
											)}
											{skusToShow.length === 0 && (
												<FormHelperText>
													No VM SKUs configured. Add them in Settings tab to
													enable restrictions.
												</FormHelperText>
											)}
										</FormControl>
									)}
								/>
							</Box>
						))}
					</Stack>
				</DialogContent>
				<DialogActions>
					<Button onClick={handleClose} disabled={mutation.isPending}>
						Cancel
					</Button>
					<Button
						type="submit"
						variant="contained"
						disabled={mutation.isPending}
						startIcon={mutation.isPending && <CircularProgress size={20} />}
					>
						{editMode ? 'Update' : 'Add'} Migrate Project
					</Button>
				</DialogActions>
			</form>
		</Dialog>
	)
}
