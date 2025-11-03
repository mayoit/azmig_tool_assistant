import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { ValidationTrend } from '../../services/dashboard.service';
import { format } from 'date-fns';

interface ValidationChartProps {
  trends: ValidationTrend[];
}

const ValidationChart: React.FC<ValidationChartProps> = ({ trends }) => {
  // Format dates for display
  const formattedData = trends.map((trend) => ({
    ...trend,
    displayDate: format(new Date(trend.date), 'MMM dd'),
  }));

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Validation Trends (Last 30 Days)
      </Typography>

      {trends.length === 0 ? (
        <Box sx={{ py: 8, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2">
            No validation data yet. Trends will appear after running validations.
          </Typography>
        </Box>
      ) : (
        <Box sx={{ width: '100%', height: 300, mt: 2 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={formattedData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="displayDate"
                tick={{ fontSize: 12 }}
                stroke="#888"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                stroke="#888"
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: '14px' }}
                iconType="line"
              />
              <Line
                type="monotone"
                dataKey="passed"
                stroke="#4caf50"
                strokeWidth={2}
                name="Passed"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="failed"
                stroke="#f44336"
                strokeWidth={2}
                name="Failed"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="total"
                stroke="#2196f3"
                strokeWidth={2}
                name="Total"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Paper>
  );
};

export default ValidationChart;
