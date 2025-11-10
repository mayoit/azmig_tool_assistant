import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  AlertTitle,
  CircularProgress,
  Box,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import api from '../services/api';

interface AzureAuthConfigProps {
  projectId: string;
  tenantId: string;  // Get tenant ID from project (already set during creation)
}

interface AuthStatus {
  configured: boolean;
  auth_method: string | null;
  tenant_id: string | null;
  token_valid: boolean;
  token_expires_at: string | null;
}

type AuthMethod = 'service_principal' | 'managed_identity' | 'user_login' | 'user_interactive' | 'user_token';

interface ServicePrincipalCredentials {
  client_id: string;
  client_secret: string;
}

interface ManagedIdentityCredentials {
  client_id?: string;
}

interface UserTokenCredentials {
  access_token: string;
  expires_on: number;
}

export default function AzureAuthConfig({ projectId, tenantId: projectTenantId }: AzureAuthConfigProps) {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [authenticating, setAuthenticating] = useState(false);
  
  // Remove tenantId state - use projectTenantId from props
  const [authMethod, setAuthMethod] = useState<AuthMethod>('service_principal');
  
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [managedIdentityClientId, setManagedIdentityClientId] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [tokenExpiresIn, setTokenExpiresIn] = useState('3600'); // Default 1 hour
  
  const [deviceCodeInfo, setDeviceCodeInfo] = useState<{ verification_uri: string; user_code: string; message: string } | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAuthStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const fetchAuthStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/auth/status`);
      setAuthStatus(response.data);
      
      if (response.data.configured) {
        // Tenant ID comes from props (projectTenantId), not from API response
        setAuthMethod(response.data.auth_method || 'service_principal');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch auth status';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setTestResult(null);

      let credentials: ServicePrincipalCredentials | ManagedIdentityCredentials | UserTokenCredentials | Record<string, never> = {};
      
      if (authMethod === 'service_principal') {
        if (!clientId || !clientSecret) {
          setError('Client ID and Client Secret are required for Service Principal');
          return;
        }
        credentials = { client_id: clientId, client_secret: clientSecret };
      } else if (authMethod === 'managed_identity' && managedIdentityClientId) {
        credentials = { client_id: managedIdentityClientId };
      } else if (authMethod === 'user_token') {
        if (!accessToken) {
          setError('Access Token is required for Manual Token authentication');
          return;
        }
        // Calculate expiration timestamp
        const expiresIn = parseInt(tokenExpiresIn) || 3600;
        const expiresOn = Math.floor(Date.now() / 1000) + expiresIn;
        credentials = { access_token: accessToken, expires_on: expiresOn };
      }

      await api.post(`/projects/${projectId}/auth/configure`, {
        tenant_id: projectTenantId,
        auth_method: authMethod,
        credentials,
      });

      await fetchAuthStatus();
      setTestResult({ success: true, message: 'Authentication configured successfully' });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save authentication';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setError(null);
      setTestResult(null);

      const response = await api.post(`/projects/${projectId}/auth/test`);
      setTestResult({ success: true, message: response.data.message });
      await fetchAuthStatus();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Authentication test failed';
      setTestResult({ success: false, message: errorMessage });
    } finally {
      setTesting(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setLoading(true);
      await api.post(`/projects/${projectId}/auth/refresh`);
      await fetchAuthStatus();
      setTestResult({ success: true, message: 'Token refreshed successfully' });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh token';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthenticate = async () => {
    try {
      setAuthenticating(true);
      setError(null);
      setDeviceCodeInfo(null);

      // Initiate device code flow
      const response = await api.post(`/projects/${projectId}/auth/device-code`);
      const { verification_uri, user_code, message } = response.data;
      
      setDeviceCodeInfo({ verification_uri, user_code, message });
      
      // Open the verification URL in a new window
      window.open(verification_uri, '_blank');
      
      // Track if we found authentication
      let authCompleted = false;
      
      // Poll for authentication completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get(`/projects/${projectId}/auth/status`);
          if (statusResponse.data.token_valid) {
            authCompleted = true;
            clearInterval(pollInterval);
            setAuthenticating(false);
            setDeviceCodeInfo(null);
            setTestResult({ success: true, message: 'Authentication successful!' });
            await fetchAuthStatus();
          }
        } catch (err) {
          console.error('Polling error:', err);
          // Continue polling
        }
      }, 3000); // Poll every 3 seconds
      
      // Stop polling after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (!authCompleted) {
          setAuthenticating(false);
          setError('Authentication timeout. Please try again.');
        }
      }, 300000);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initiate authentication';
      setError(errorMessage);
      setAuthenticating(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" py={4}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Azure Authentication
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Configure Azure credentials for this project to enable validation
        </Typography>

        <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
          {authStatus && authStatus.configured && (
            <Alert severity="info" icon={<InfoIcon />}>
              <AlertTitle>Current Configuration</AlertTitle>
              <Typography variant="body2">Method: {authStatus.auth_method}</Typography>
              <Typography variant="body2">Tenant: {projectTenantId}</Typography>
              <Typography variant="body2">
                Token: {authStatus.token_valid ? (
                  <span style={{ color: '#2e7d32' }}>
                    Valid (expires {new Date(authStatus.token_expires_at!).toLocaleString()})
                  </span>
                ) : (
                  <span style={{ color: '#d32f2f' }}>Expired or Invalid</span>
                )}
              </Typography>
            </Alert>
          )}

          <Alert severity="info" icon={<InfoIcon />}>
            <Typography variant="body2">
              <strong>Azure Tenant ID:</strong> {projectTenantId}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              (Set during project creation)
            </Typography>
          </Alert>

          <FormControl fullWidth>
            <InputLabel>Authentication Method</InputLabel>
            <Select
              value={authMethod}
              label="Authentication Method"
              onChange={(e) => setAuthMethod(e.target.value as AuthMethod)}
            >
              <MenuItem value="service_principal">Service Principal</MenuItem>
              <MenuItem value="managed_identity">Managed Identity</MenuItem>
              <MenuItem value="user_token">User Token (Manual)</MenuItem>
              <MenuItem value="user_interactive">User Login (Browser)</MenuItem>
              <MenuItem value="user_login">User Login (Device Code)</MenuItem>
            </Select>
          </FormControl>

          {authMethod === 'service_principal' && (
            <Box sx={{ borderLeft: 4, borderColor: 'primary.main', pl: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Client ID (Application ID)"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
              />
              <TextField
                fullWidth
                type="password"
                label="Client Secret"
                placeholder="Enter client secret"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                helperText="Credentials are encrypted before storage"
              />
            </Box>
          )}

          {authMethod === 'managed_identity' && (
            <Box sx={{ borderLeft: 4, borderColor: 'success.main', pl: 2 }}>
              <TextField
                fullWidth
                label="Client ID (Optional)"
                placeholder="Leave empty for system-assigned identity"
                value={managedIdentityClientId}
                onChange={(e) => setManagedIdentityClientId(e.target.value)}
                helperText="Only required for user-assigned managed identity"
              />
            </Box>
          )}

          {authMethod === 'user_token' && (
            <Box sx={{ borderLeft: 4, borderColor: 'warning.main', pl: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Alert severity="info" icon={<InfoIcon />}>
                <AlertTitle>How to Get an Access Token</AlertTitle>
                <Typography variant="body2" gutterBottom>
                  You can generate a token using Azure CLI or Azure Portal:
                </Typography>
                <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', fontSize: '0.85rem', mt: 1 }}>
                  <strong>Azure CLI:</strong><br />
                  az account get-access-token --resource https://management.azure.com/
                </Typography>
              </Alert>
              
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Access Token"
                placeholder="Paste your Azure access token here"
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                helperText="Token is encrypted before storage"
              />
              
              <TextField
                fullWidth
                type="number"
                label="Token Valid Duration (seconds)"
                placeholder="3600"
                value={tokenExpiresIn}
                onChange={(e) => setTokenExpiresIn(e.target.value)}
                helperText="How long the token is valid (default: 3600 = 1 hour)"
              />
            </Box>
          )}

          {authMethod === 'user_login' && (
            <>
              <Alert severity="info" icon={<InfoIcon />}>
                Device code flow: Click "Authenticate" to get a code. You'll visit microsoft.com/devicelogin and enter the code.
              </Alert>
              
              {deviceCodeInfo && (
                <Alert severity="warning" icon={<InfoIcon />}>
                  <AlertTitle>Authentication Required</AlertTitle>
                  <Typography variant="body2" gutterBottom>
                    {deviceCodeInfo.message}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold" sx={{ mt: 1 }}>
                    Code: {deviceCodeInfo.user_code}
                  </Typography>
                  <Button 
                    size="small" 
                    sx={{ mt: 1 }}
                    onClick={() => window.open(deviceCodeInfo.verification_uri, '_blank')}
                  >
                    Open {deviceCodeInfo.verification_uri}
                  </Button>
                </Alert>
              )}
            </>
          )}

          {authMethod === 'user_interactive' && (
            <Alert severity="warning" icon={<InfoIcon />}>
              <AlertTitle>Browser-Based Authentication (Local Only)</AlertTitle>
              <Typography variant="body2">
                This method opens Azure login in a browser window on the server. It only works when running the API locally, not in Docker containers.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                Recommended: Use "User Login (Device Code)" instead, which works in all environments.
              </Typography>
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button 
              variant="contained" 
              onClick={handleSave} 
              disabled={saving || !projectTenantId}
              startIcon={saving && <CircularProgress size={20} />}
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </Button>
            
            {authStatus?.configured && (
              <>
                {(authMethod === 'user_login' || authMethod === 'user_interactive') ? (
                  <Button 
                    variant="contained"
                    color="primary"
                    onClick={authMethod === 'user_login' ? handleAuthenticate : handleTest} 
                    disabled={authMethod === 'user_login' ? authenticating : testing}
                    startIcon={(authMethod === 'user_login' ? authenticating : testing) && <CircularProgress size={20} />}
                  >
                    {authMethod === 'user_login' 
                      ? (authenticating ? 'Authenticating...' : 'Authenticate')
                      : (testing ? 'Authenticating...' : 'Authenticate')
                    }
                  </Button>
                ) : (
                  <Button 
                    variant="outlined" 
                    onClick={handleTest} 
                    disabled={testing}
                    startIcon={testing && <CircularProgress size={20} />}
                  >
                    {testing ? 'Testing...' : 'Test Connection'}
                  </Button>
                )}
                
                {!authStatus.token_valid && authMethod !== 'user_login' && authMethod !== 'user_interactive' && (
                  <Button variant="outlined" onClick={handleRefresh}>
                    Refresh Token
                  </Button>
                )}
              </>
            )}
          </Box>

          {testResult && (
            <Alert 
              severity={testResult.success ? 'success' : 'error'}
              icon={testResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
            >
              {testResult.message}
            </Alert>
          )}

          {error && (
            <Alert severity="error" icon={<ErrorIcon />}>
              {error}
            </Alert>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

