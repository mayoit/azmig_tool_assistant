import React from 'react';
import { Paper, Typography, Box, Button } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { useNavigate } from 'react-router-dom';
import type { DashboardStats } from '../../services/dashboard.service';

interface QuickActionsProps {
  stats: DashboardStats;
}

const QuickActions: React.FC<QuickActionsProps> = ({ stats }) => {
  const navigate = useNavigate();

  const actions = [
    {
      label: 'Create Project',
      icon: <AddIcon />,
      color: 'primary' as const,
      onClick: () => navigate('/projects?new=true'),
      disabled: false,
      description: 'Start a new migration project',
    },
    {
      label: 'Upload Servers',
      icon: <CloudUploadIcon />,
      color: 'success' as const,
      onClick: () => navigate('/servers/upload'),
      disabled: stats.total_projects === 0,
      description: stats.total_projects === 0 
        ? 'Create a project first'
        : 'Upload server configurations',
    },
    {
      label: 'Run Validation',
      icon: <PlayArrowIcon />,
      color: 'warning' as const,
      onClick: () => navigate('/validations?run=true'),
      disabled: stats.total_servers === 0,
      description: stats.total_servers === 0
        ? 'Upload servers first'
        : 'Start validation process',
    },
    {
      label: 'View Reports',
      icon: <AssessmentIcon />,
      color: 'info' as const,
      onClick: () => navigate('/reports'),
      disabled: stats.total_validations === 0,
      description: stats.total_validations === 0
        ? 'Run validations first'
        : 'View validation reports',
    },
  ];

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Quick Actions
      </Typography>
      
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: 'repeat(1, 1fr)',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(4, 1fr)',
          },
          gap: 2,
          mt: 2,
        }}
      >
        {actions.map((action, index) => (
          <Box key={index}>
            <Button
              variant="contained"
              color={action.color}
              startIcon={action.icon}
              onClick={action.onClick}
              disabled={action.disabled}
              fullWidth
              sx={{
                py: 1.5,
                display: 'flex',
                flexDirection: 'column',
                gap: 0.5,
                height: '100%',
              }}
            >
              <Box sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}>
                {action.label}
              </Box>
              <Box
                sx={{
                  fontSize: '0.75rem',
                  opacity: action.disabled ? 0.7 : 0.9,
                  fontWeight: 'normal',
                }}
              >
                {action.description}
              </Box>
            </Button>
          </Box>
        ))}
      </Box>
    </Paper>
  );
};

export default QuickActions;
