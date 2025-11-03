import { Box, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';

export default function ValidationsPage() {
  const { id } = useParams();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Validations (Project ID: {id})
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Validation monitoring coming soon...
      </Typography>
    </Box>
  );
}
