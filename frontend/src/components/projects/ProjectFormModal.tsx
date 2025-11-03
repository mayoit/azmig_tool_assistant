import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsService } from '../../services/projects.service';
import type { ProjectCreate, ProjectUpdate } from '../../types/project.types';

// Validation schema
const projectSchema = z.object({
  name: z.string()
    .min(1, 'Project name is required')
    .min(3, 'Project name must be at least 3 characters')
    .max(255, 'Project name must be less than 255 characters'),
  description: z.string()
    .max(1000, 'Description must be less than 1000 characters')
    .optional()
    .or(z.literal('')),
  azure_subscription_id: z.string()
    .min(1, 'Azure Subscription ID is required')
    .uuid('Must be a valid UUID (e.g., 12345678-1234-1234-1234-123456789012)'),
});

type ProjectFormData = z.infer<typeof projectSchema>;

interface ProjectFormModalProps {
  open: boolean;
  onClose: () => void;
  projectId?: number;
  initialData?: Partial<ProjectFormData>;
  mode: 'create' | 'edit';
}

const ProjectFormModal: React.FC<ProjectFormModalProps> = ({
  open,
  onClose,
  projectId,
  initialData,
  mode,
}) => {
  const queryClient = useQueryClient();
  
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: initialData?.name || '',
      description: initialData?.description || '',
      azure_subscription_id: initialData?.azure_subscription_id || '',
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: ProjectCreate) => projectsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      handleClose();
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: ProjectUpdate) => projectsService.update(projectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      handleClose();
    },
  });

  const onSubmit = (data: ProjectFormData) => {
    if (mode === 'create') {
      createMutation.mutate(data as ProjectCreate);
    } else {
      updateMutation.mutate(data as ProjectUpdate);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const mutation = mode === 'create' ? createMutation : updateMutation;
  const isLoading = isSubmitting || mutation.isPending;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        component: 'form',
        onSubmit: handleSubmit(onSubmit),
      }}
    >
      <DialogTitle>
        {mode === 'create' ? 'Create New Project' : 'Edit Project'}
      </DialogTitle>

      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
          {/* Error Alert */}
          {mutation.isError && (
            <Alert severity="error">
              {mutation.error instanceof Error
                ? mutation.error.message
                : 'An error occurred. Please try again.'}
            </Alert>
          )}

          {/* Project Name */}
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Project Name"
                required
                fullWidth
                error={!!errors.name}
                helperText={errors.name?.message}
                placeholder="e.g., Production Migration 2025"
                disabled={isLoading}
              />
            )}
          />

          {/* Description */}
          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Description"
                fullWidth
                multiline
                rows={3}
                error={!!errors.description}
                helperText={errors.description?.message || 'Optional project description'}
                placeholder="Describe your migration project..."
                disabled={isLoading}
              />
            )}
          />

          {/* Azure Subscription ID */}
          <Controller
            name="azure_subscription_id"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Azure Subscription ID"
                required
                fullWidth
                error={!!errors.azure_subscription_id}
                helperText={
                  errors.azure_subscription_id?.message ||
                  'UUID format: 12345678-1234-1234-1234-123456789012'
                }
                placeholder="00000000-0000-0000-0000-000000000000"
                disabled={isLoading}
              />
            )}
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : null}
        >
          {mode === 'create' ? 'Create Project' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectFormModal;
