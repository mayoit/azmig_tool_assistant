import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  InputAdornment,
  IconButton,
  Link as MuiLink,
} from '@mui/material';
import { Visibility, VisibilityOff, Login as LoginIcon } from '@mui/icons-material';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

// Validation schema
const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState<string>('');
  const [isLoading, setIsLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError('');
    setIsLoading(true);

    try {
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAdminLogin = async () => {
    setError('');
    setIsLoading(true);

    try {
      // Login directly with admin credentials
      await login('admin@example.com', 'admin123');
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(onSubmit)}
      sx={{
        width: '100%',
        maxWidth: 400,
        mx: 'auto',
        p: 4,
        display: 'flex',
        flexDirection: 'column',
        gap: 3,
      }}
    >
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
          Welcome Back
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Sign in to your account to continue
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Email Field */}
      <TextField
        label="Email Address"
        type="email"
        autoComplete="email"
        autoFocus
        fullWidth
        error={!!errors.email}
        helperText={errors.email?.message}
        {...register('email')}
        disabled={isLoading}
      />

      {/* Password Field */}
      <TextField
        label="Password"
        type={showPassword ? 'text' : 'password'}
        autoComplete="current-password"
        fullWidth
        error={!!errors.password}
        helperText={errors.password?.message}
        {...register('password')}
        disabled={isLoading}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                aria-label="toggle password visibility"
                onClick={handleTogglePasswordVisibility}
                edge="end"
                disabled={isLoading}
              >
                {showPassword ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      {/* Submit Button */}
      <Button
        type="submit"
        variant="contained"
        size="large"
        fullWidth
        disabled={isLoading}
        startIcon={<LoginIcon />}
        sx={{ mt: 1, py: 1.5 }}
      >
        {isLoading ? 'Signing in...' : 'Sign In'}
      </Button>

      {/* Quick Admin Login Button - Temporary */}
      <Button
        variant="outlined"
        size="large"
        fullWidth
        disabled={isLoading}
        onClick={handleQuickAdminLogin}
        sx={{ 
          py: 1.5,
          borderColor: 'primary.main',
          color: 'primary.main',
          '&:hover': {
            borderColor: 'primary.dark',
            bgcolor: 'primary.50',
          }
        }}
      >
        🚀 Quick Admin Login (Dev)
      </Button>

      {/* Footer Links */}
      <Box sx={{ textAlign: 'center', mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Don't have an account?{' '}
          <MuiLink component={Link} to="/register" underline="hover">
            Sign up
          </MuiLink>
        </Typography>
      </Box>

      {/* Demo Credentials */}
      <Box
        sx={{
          mt: 3,
          p: 2,
          borderRadius: 1,
          bgcolor: 'action.hover',
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography variant="caption" display="block" fontWeight="bold" gutterBottom>
          Demo Credentials:
        </Typography>
        <Typography variant="caption" display="block" color="text.secondary">
          Admin: admin@example.com / admin123
        </Typography>
        <Typography variant="caption" display="block" color="text.secondary">
          Operator: operator@example.com / operator123
        </Typography>
        <Typography variant="caption" display="block" color="text.secondary">
          Viewer: viewer@example.com / viewer123
        </Typography>
      </Box>
    </Box>
  );
};
