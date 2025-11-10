import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import TuneIcon from '@mui/icons-material/Tune';
import ValidationSettingsEditor from '../validation/ValidationSettingsEditor';
import ProjectSettingsEditor from '../projects/ProjectSettingsEditor';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `settings-tab-${index}`,
    'aria-controls': `settings-tabpanel-${index}`,
  };
}

interface ProjectSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  disk_types: string[];
  redundancy_types: string[];
}

interface ValidationSettings {
  global: {
    fail_fast: boolean;
    parallel_execution: boolean;
    timeout_seconds: number;
  };
  landing_zone: {
    access_validation: {
      enabled: boolean;
      checks: {
        migrate_project_rbac: { enabled: boolean };
        recovery_vault_rbac: { enabled: boolean };
        subscription_rbac: { enabled: boolean };
      };
    };
    appliance_health: { enabled: boolean };
    storage_cache: { enabled: boolean; auto_create_if_missing: boolean };
    quota_validation: { enabled: boolean };
  };
  servers: {
    region_validation: { enabled: boolean };
    resource_group_validation: { enabled: boolean };
    vnet_subnet_validation: { enabled: boolean };
    vm_sku_validation: { enabled: boolean };
    disk_type_validation: { enabled: boolean };
    discovery_validation: { enabled: boolean };
    rbac_validation: { enabled: boolean };
  };
}

interface SettingsEditorProps {
  projectId: number;
  projectSettings: ProjectSettings | null;
  validationSettings: ValidationSettings;
}

export default function SettingsEditor({
  projectId,
  projectSettings,
  validationSettings,
}: SettingsEditorProps) {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      <Paper sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          aria-label="settings tabs"
          sx={{ px: 2 }}
        >
          <Tab 
            icon={<SettingsIcon />} 
            iconPosition="start" 
            label="Project Settings" 
            {...a11yProps(0)} 
          />
          <Tab 
            icon={<TuneIcon />} 
            iconPosition="start" 
            label="Validation Settings" 
            {...a11yProps(1)} 
          />
        </Tabs>
      </Paper>

      <TabPanel value={currentTab} index={0}>
        <ProjectSettingsEditor
          projectId={projectId}
          initialSettings={projectSettings}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <ValidationSettingsEditor
          projectId={projectId}
          initialSettings={validationSettings}
        />
      </TabPanel>
    </Box>
  );
}
