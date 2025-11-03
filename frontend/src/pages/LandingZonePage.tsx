import { Box, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';

export default function LandingZonePage() {
  const { id } = useParams();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Landing Zone Configuration (Project ID: {id})
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Landing zone configuration coming soon...
      </Typography>
    </Box>
  );
}
