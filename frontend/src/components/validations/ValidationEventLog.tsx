import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Chip,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon,
  AccessTime as AccessTimeIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import { validationsService } from '../../services/validations.service';
import type { ValidationEvent } from '../../types/validation.types';

interface ServerValidationJob {
  id: number;
  job_type: string;
  status: string;
  total_items: number;
  processed_items: number;
  created_at: string;
  completed_at?: string;
}

interface ValidationEventLogProps {
  serverValidations?: ServerValidationJob[];
  landingZoneValidations?: unknown[];
  onRefresh?: () => void;
  isLoading?: boolean;
}

export default function ValidationEventLog({
  serverValidations = [],
  onRefresh,
  isLoading = false,
}: ValidationEventLogProps) {
  const [expandedJob, setExpandedJob] = useState<string | false>(false);
  const [expandedEvent, setExpandedEvent] = useState<string | false>(false);
  
  // Fetch validation events for all jobs
  const jobIds = serverValidations.map(j => j.id);
  
  // Fetch events for each job
  const eventsQueries = useQuery({
    queryKey: ['validation-events-all', jobIds],
    queryFn: async () => {
      const allEvents: Record<number, ValidationEvent[]> = {};
      
      for (const jobId of jobIds) {
        try {
          const data = await validationsService.getEvents(jobId);
          allEvents[jobId] = data.events || [];
        } catch (error) {
          allEvents[jobId] = [];
        }
      }
      
      return allEvents;
    },
    enabled: jobIds.length > 0,
    refetchInterval: () => {
      // Auto-refresh every 5 seconds if any job is running
      const hasRunningJob = serverValidations.some(j => j.status === 'running' || j.status === 'pending');
      return hasRunningJob ? 5000 : false;
    },
  });
  
  const eventsByJob = eventsQueries.data || {};
  
  const handleJobAccordionChange = (panel: string) => (_: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedJob(isExpanded ? panel : false);
  };
  
  const handleEventAccordionChange = (panel: string) => (_: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedEvent(isExpanded ? panel : false);
  };
  
  const handleRefresh = () => {
    eventsQueries.refetch();
    onRefresh?.();
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'PASSED':
      case 'COMPLETED':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'FAILED':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'WARNING':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'SKIPPED':
        return <InfoIcon color="disabled" fontSize="small" />;
      case 'RUNNING':
      case 'PENDING':
        return <PlayArrowIcon color="info" fontSize="small" />;
      default:
        return <ScheduleIcon color="info" fontSize="small" />;
    }
  };

  const getStatusColor = (status: string): "success" | "error" | "warning" | "info" | "default" => {
    switch (status?.toUpperCase()) {
      case 'PASSED':
      case 'COMPLETED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'WARNING':
        return 'warning';
      case 'RUNNING':
      case 'PENDING':
      case 'INPROGRESS':
      case 'STARTED':
        return 'info';
      default:
        return 'default';
    }
  };

  if (serverValidations.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No validation jobs yet. Click "Run Validation" to start.
      </Alert>
    );
  }

  const totalEvents = Object.values(eventsByJob).reduce((sum, events) => sum + events.length, 0);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary">
          {serverValidations.length} validation job{serverValidations.length !== 1 ? 's' : ''}
          {totalEvents > 0 && ` • ${totalEvents} total event${totalEvents !== 1 ? 's' : ''}`}
        </Typography>
        <Tooltip title="Refresh">
          <IconButton size="small" onClick={handleRefresh} disabled={isLoading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Stack spacing={2}>
        {serverValidations.map((job) => {
          const jobEvents = eventsByJob[job.id] || [];
          const passedEvents = jobEvents.filter(e => e.status === 'passed').length;
          const failedEvents = jobEvents.filter(e => e.status === 'failed').length;
          
          return (
						<Accordion
							key={`job-${job.id}`}
							expanded={expandedJob === `job-${job.id}`}
							onChange={handleJobAccordionChange(`job-${job.id}`)}
							elevation={2}
							sx={{
								border: 1,
								borderColor: 'divider',
								'&:before': { display: 'none' },
							}}
						>
							<AccordionSummary
								expandIcon={<ExpandMoreIcon />}
								sx={{ bgcolor: 'background.paper' }}
							>
								<Box
									sx={{
										display: 'flex',
										alignItems: 'center',
										gap: 2,
										width: '100%',
									}}
								>
									{getStatusIcon(job.status)}
									<Box sx={{ flex: 1 }}>
										<Typography
											variant="body1"
											fontWeight="medium"
											sx={{ color: '#000' }}
										>
											Validation Job #{job.id}
											<Typography
												component="span"
												variant="caption"
												sx={{ ml: 1, color: '#666' }}
											>
												({job.job_type})
											</Typography>
										</Typography>
										<Box
											sx={{
												display: 'flex',
												alignItems: 'center',
												gap: 1,
												mt: 0.5,
											}}
										>
											<AccessTimeIcon sx={{ fontSize: 14, color: '#666' }} />
											<Typography variant="caption" sx={{ color: '#666' }}>
												{formatDistanceToNow(new Date(job.created_at), {
													addSuffix: true,
												})}
											</Typography>
											{jobEvents.length > 0 && (
												<Typography variant="caption" sx={{ color: '#666' }}>
													• {jobEvents.length} event
													{jobEvents.length !== 1 ? 's' : ''}
												</Typography>
											)}
											{passedEvents > 0 && (
												<Chip
													label={`${passedEvents} passed`}
													size="small"
													color="success"
													variant="outlined"
													sx={{ height: 20, fontSize: '0.7rem' }}
												/>
											)}
											{failedEvents > 0 && (
												<Chip
													label={`${failedEvents} failed`}
													size="small"
													color="error"
													variant="outlined"
													sx={{ height: 20, fontSize: '0.7rem' }}
												/>
											)}
										</Box>
									</Box>
									<Chip
										label={job.status.toUpperCase()}
										size="small"
										color={getStatusColor(job.status)}
									/>
								</Box>
							</AccordionSummary>
							<AccordionDetails>
								{job.status === 'running' && (
									<Box sx={{ mb: 2 }}>
										<LinearProgress />
										<Typography
											variant="caption"
											sx={{ mt: 1, display: 'block', color: '#666' }}
										>
											Validation in progress... {job.processed_items} /{' '}
											{job.total_items} items
										</Typography>
									</Box>
								)}

								{jobEvents.length === 0 ? (
									<Alert severity="info">
										No validation events found for this job.
									</Alert>
								) : (
									<Stack spacing={1}>
										<Typography
											variant="subtitle2"
											sx={{ color: '' }}
											gutterBottom
										>
											Validation Events
										</Typography>
										{jobEvents.map((event: ValidationEvent) => (
											<Accordion
												key={`event-${event.id}`}
												expanded={expandedEvent === `event-${event.id}`}
												onChange={handleEventAccordionChange(
													`event-${event.id}`
												)}
												elevation={0}
												sx={{
													border: 1,
													borderColor: 'divider',
													borderRadius: 1,
												}}
											>
												<AccordionSummary expandIcon={<ExpandMoreIcon />}>
													<Box
														sx={{
															display: 'flex',
															alignItems: 'center',
															gap: 2,
															width: '100%',
														}}
													>
														{getStatusIcon(event.status)}
														<Box sx={{ flex: 1 }}>
															<Typography
																variant="body2"
																fontWeight="medium"
																sx={{ color: 'text.primary' }}
															>
																{event.event_name}
																{event.resource_name && (
																	<Typography
																		component="span"
																		variant="caption"
																		sx={{ ml: 1, color: 'text.primary' }}
																	>
																		({event.resource_name})
																	</Typography>
																)}
															</Typography>
															<Box
																sx={{
																	display: 'flex',
																	alignItems: 'center',
																	gap: 1,
																	mt: 0.5,
																}}
															>
																<AccessTimeIcon
																	sx={{ fontSize: 12, color: '#666' }}
																/>
																<Typography
																	variant="caption"
																	sx={{ color: '#666' }}
																>
																	{formatDistanceToNow(
																		new Date(event.event_timestamp),
																		{ addSuffix: true }
																	)}
																</Typography>
																{event.duration_ms && (
																	<Typography
																		variant="caption"
																		sx={{ color: '#666' }}
																	>
																		• {event.duration_ms}ms
																	</Typography>
																)}
															</Box>
														</Box>
														<Chip
															label={event.status.toUpperCase()}
															size="small"
															color={getStatusColor(event.status)}
														/>
														<Chip
															label={event.operation_status}
															size="small"
															variant="outlined"
															color={getStatusColor(event.operation_status)}
														/>
													</Box>
												</AccordionSummary>
												<AccordionDetails>
													<Stack spacing={2}>
														<Box>
															<Typography
																variant="subtitle2"
																gutterBottom
																color="text.primary"
															>
																Event Details
															</Typography>
															<TableContainer
																component={Paper}
																variant="outlined"
															>
																<Table size="small">
																	<TableBody>
																		<TableRow>
																			<TableCell
																				component="th"
																				sx={{
																					fontWeight: 'medium',
																					width: '30%',
																					color: 'text.primary',
																				}}
																			>
																				Category
																			</TableCell>
																			<TableCell sx={{ color: 'text.primary' }}>
																				{event.event_category}
																			</TableCell>
																		</TableRow>
																		<TableRow>
																			<TableCell
																				component="th"
																				sx={{
																					fontWeight: 'medium',
																					color: 'text.primary',
																				}}
																			>
																				Validation Type
																			</TableCell>
																			<TableCell sx={{ color: 'text.primary' }}>
																				{event.validation_type}
																			</TableCell>
																		</TableRow>
																		{event.resource_type && (
																			<TableRow>
																				<TableCell
																					component="th"
																					sx={{
																						fontWeight: 'medium',
																						color: 'text.primary',
																					}}
																				>
																					Resource Type
																				</TableCell>
																				<TableCell
																					sx={{ color: 'text.primary' }}
																				>
																					{event.resource_type}
																				</TableCell>
																			</TableRow>
																		)}
																		<TableRow>
																			<TableCell
																				component="th"
																				sx={{
																					fontWeight: 'medium',
																					color: 'text.primary',
																				}}
																			>
																				Event Time
																			</TableCell>
																			<TableCell sx={{ color: 'text.primary' }}>
																				{format(
																					new Date(event.event_timestamp),
																					'PPpp'
																				)}
																			</TableCell>
																		</TableRow>
																		{event.submitted_at && (
																			<TableRow>
																				<TableCell
																					component="th"
																					sx={{
																						fontWeight: 'medium',
																						color: 'text.primary',
																					}}
																				>
																					Started
																				</TableCell>
																				<TableCell
																					sx={{ color: 'text.primary' }}
																				>
																					{format(
																						new Date(event.submitted_at),
																						'PPpp'
																					)}
																				</TableCell>
																			</TableRow>
																		)}
																		{event.completed_at && (
																			<TableRow>
																				<TableCell
																					component="th"
																					sx={{
																						fontWeight: 'medium',
																						color: 'text.primary',
																					}}
																				>
																					Completed
																				</TableCell>
																				<TableCell
																					sx={{ color: 'text.primary' }}
																				>
																					{format(
																						new Date(event.completed_at),
																						'PPpp'
																					)}
																				</TableCell>
																			</TableRow>
																		)}
																	</TableBody>
																</Table>
															</TableContainer>
														</Box>

														{event.message && (
															<Box>
																<Typography
																	variant="subtitle2"
																	gutterBottom
																	color="text.primary"
																>
																	Message
																</Typography>
																<Alert
																	severity={
																		event.status === 'passed'
																			? 'success'
																			: event.status === 'failed'
																			? 'error'
																			: 'info'
																	}
																>
																	{event.message}
																</Alert>
															</Box>
														)}

														{event.error_message && (
															<Box>
																<Typography
																	variant="subtitle2"
																	gutterBottom
																	color="text.primary"
																>
																	Error
																</Typography>
																<Alert severity="error">
																	{event.error_message}
																</Alert>
															</Box>
														)}

														{event.request_payload &&
															Object.keys(event.request_payload).length > 0 && (
																<Box>
																	<Typography
																		variant="subtitle2"
																		gutterBottom
																		color="text.primary"
																	>
																		Request Details
																	</Typography>
																	<Paper
																		variant="outlined"
																		sx={{ p: 1, bgcolor: 'grey.50' }}
																	>
																		<pre
																			style={{
																				margin: 0,
																				fontSize: '0.75rem',
																				overflow: 'auto',
																				color: '#000',
																			}}
																		>
																			{JSON.stringify(
																				event.request_payload,
																				null,
																				2
																			)}
																		</pre>
																	</Paper>
																</Box>
															)}

														{event.response_payload &&
															Object.keys(event.response_payload).length >
																0 && (
																<Box>
																	<Typography
																		variant="subtitle2"
																		gutterBottom
																		color="text.primary"
																	>
																		Response Details
																	</Typography>
																	<Paper
																		variant="outlined"
																		sx={{ p: 1, bgcolor: 'grey.50' }}
																	>
																		<pre
																			style={{
																				margin: 0,
																				fontSize: '0.75rem',
																				overflow: 'auto',
																				color: '#000',
																			}}
																		>
																			{JSON.stringify(
																				event.response_payload,
																				null,
																				2
																			)}
																		</pre>
																	</Paper>
																</Box>
															)}
													</Stack>
												</AccordionDetails>
											</Accordion>
										))}
									</Stack>
								)}
							</AccordionDetails>
						</Accordion>
					)
        })}
      </Stack>
    </Box>
  );
}
