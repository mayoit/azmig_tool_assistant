import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { landingZonesService } from '../../services/landingZones.service';
import type { LandingZoneConfig, LandingZoneCreate } from '../../types/project.types';

const landingZoneSchema = z.object({
  migrate_project_name: z.string().min(1, 'Migrate Project Name is required').max(255),
  migrate_project_rg: z.string().min(1, 'Migrate Project Resource Group is required').max(255),
  recovery_vault_name: z.string().min(1, 'Recovery Vault Name is required').max(255),
  recovery_vault_rg: z.string().min(1, 'Recovery Vault Resource Group is required').max(255),
  cache_storage_account: z.string().min(1, 'Cache Storage Account is required').max(255),
  cache_storage_rg: z.string().min(1, 'Cache Storage Resource Group is required').max(255),
  appliance_name: z.string().min(1, 'Appliance Name is required').max(255),
});

type LandingZoneFormData = z.infer<typeof landingZoneSchema>;

interface LandingZoneFormModalProps {
  open: boolean;
  onClose: () => void;
  projectId: number;
  projectName: string;
  initialData?: LandingZoneConfig | null;
}

export default function LandingZoneFormModal({
  open,
  onClose,
  projectId,
  projectName,
  initialData,
}: LandingZoneFormModalProps) {
  const queryClient = useQueryClient();

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LandingZoneFormData>({
    resolver: zodResolver(landingZoneSchema),
    defaultValues: initialData
      ? {
          migrate_project_name: initialData.migrate_project_name,
          migrate_project_rg: initialData.migrate_project_rg,
          recovery_vault_name: initialData.recovery_vault_name,
          recovery_vault_rg: initialData.recovery_vault_rg,
          cache_storage_account: initialData.cache_storage_account,
          cache_storage_rg: initialData.cache_storage_rg,
          appliance_name: initialData.appliance_name,
        }
      : {
          migrate_project_name: '',
          migrate_project_rg: '',
          recovery_vault_name: '',
          recovery_vault_rg: '',
          cache_storage_account: '',
          cache_storage_rg: '',
          appliance_name: '',
        },
  });

  const mutation = useMutation({
    mutationFn: (data: LandingZoneCreate) =>
      landingZonesService.createOrUpdate(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      queryClient.invalidateQueries({ queryKey: ['landing-zone', projectId] });
      onClose();
      reset();
    },
  });

  const onSubmit = (data: LandingZoneFormData) => {
    mutation.mutate(data);
  };

  const handleClose = () => {
    if (!mutation.isPending) {
      reset();
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {initialData ? 'Edit' : 'Configure'} Landing Zone - {projectName}
      </DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          {mutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to save landing zone configuration. Please try again.
            </Alert>
          )}

          <Controller
            name="migrate_project_name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Azure Migrate Project Name"
                fullWidth
                margin="normal"
                required
                error={!!errors.migrate_project_name}
                helperText={errors.migrate_project_name?.message}
              />
            )}
          />

          <Controller
            name="migrate_project_rg"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Migrate Project Resource Group"
                fullWidth
                margin="normal"
                required
                error={!!errors.migrate_project_rg}
                helperText={errors.migrate_project_rg?.message}
              />
            )}
          />

          <Controller
            name="recovery_vault_name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Recovery Services Vault Name"
                fullWidth
                margin="normal"
                required
                error={!!errors.recovery_vault_name}
                helperText={errors.recovery_vault_name?.message}
              />
            )}
          />

          <Controller
            name="recovery_vault_rg"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Recovery Vault Resource Group"
                fullWidth
                margin="normal"
                required
                error={!!errors.recovery_vault_rg}
                helperText={errors.recovery_vault_rg?.message}
              />
            )}
          />

          <Controller
            name="cache_storage_account"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Cache Storage Account"
                fullWidth
                margin="normal"
                required
                error={!!errors.cache_storage_account}
                helperText={errors.cache_storage_account?.message}
              />
            )}
          />

          <Controller
            name="cache_storage_rg"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Cache Storage Resource Group"
                fullWidth
                margin="normal"
                required
                error={!!errors.cache_storage_rg}
                helperText={errors.cache_storage_rg?.message}
              />
            )}
          />

          <Controller
            name="appliance_name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Appliance Name"
                fullWidth
                margin="normal"
                required
                error={!!errors.appliance_name}
                helperText={errors.appliance_name?.message}
              />
            )}
          />
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
            {initialData ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
