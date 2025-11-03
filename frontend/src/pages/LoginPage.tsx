import { Box, Container, Paper } from '@mui/material';
import { LoginForm } from '../components/auth/LoginForm';

export default function LoginPage() {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            width: '100%',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <LoginForm />
        </Paper>
      </Box>
    </Container>
  );
}
