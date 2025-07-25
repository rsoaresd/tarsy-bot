import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Button,
  Chip,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Snackbar,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as LLMIcon,
  Settings as MCPIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  AccessTime as TimeIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import { InteractionDetail } from '../types';

interface InteractionDetailsProps {
  interaction: InteractionDetail | null;
  allInteractions?: InteractionDetail[];
  onClose?: () => void;
}

function InteractionDetails({ interaction, allInteractions = [], onClose }: InteractionDetailsProps) {
  const theme = useTheme();
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  // Handle copy to clipboard
  const handleCopy = useCallback(async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(`${label} copied to clipboard`);
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (err) {
      console.error('Failed to copy:', err);
      setCopySuccess('Failed to copy to clipboard');
      setTimeout(() => setCopySuccess(null), 3000);
    }
  }, []);

  // Handle accordion toggle
  const handleAccordionToggle = useCallback((panel: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(panel)) {
        newSet.delete(panel);
      } else {
        newSet.add(panel);
      }
      return newSet;
    });
  }, []);

  // Export full timeline
  const handleExportTimeline = useCallback(async () => {
    const timelineData = allInteractions.map(inter => ({
      timestamp: inter.timestamp,
      type: inter.interaction_type,
      step: inter.step_description,
      duration_ms: inter.duration_ms,
      success: inter.success,
      error: inter.error_message || null,
      // Type-specific data
      ...(inter.interaction_type === 'llm' ? {
        model: inter.model,
        tokens_used: inter.tokens_used,
      } : {
        server_name: inter.server_name,
        tool_name: inter.tool_name,
        tool_arguments: inter.tool_arguments,
      }),
    }));

    const exportText = JSON.stringify(timelineData, null, 2);
    await handleCopy(exportText, 'Timeline data');
  }, [allInteractions, handleCopy]);

  // Format duration
  const formatDuration = (durationMs: number) => {
    if (durationMs < 1000) return `${durationMs}ms`;
    if (durationMs < 60000) return `${(durationMs / 1000).toFixed(2)}s`;
    return `${Math.floor(durationMs / 60000)}m ${((durationMs % 60000) / 1000).toFixed(2)}s`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  // Get interaction type display
  const getTypeDisplay = (type: string) => {
    if (type === 'llm') {
      return {
        icon: <LLMIcon sx={{ color: 'info.main' }} />,
        label: 'LLM Interaction',
        color: 'info',
      };
    } else {
      return {
        icon: <MCPIcon sx={{ color: 'warning.main' }} />,
        label: 'MCP Communication',
        color: 'warning',
      };
    }
  };

  if (!interaction) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h3" color="text.secondary" gutterBottom>
          No Interaction Selected
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Click on a timeline point to view detailed interaction information.
        </Typography>
      </Paper>
    );
  }

  const typeDisplay = getTypeDisplay(interaction.interaction_type);

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {typeDisplay.icon}
            <Typography variant="h2" component="h2">
              Interaction Details
            </Typography>
          </Box>
          
          <Chip
            label={typeDisplay.label}
            color={typeDisplay.color as any}
            size="small"
          />
          
          <Chip
            icon={interaction.success ? <SuccessIcon /> : <ErrorIcon />}
            label={interaction.success ? 'Success' : 'Error'}
            color={interaction.success ? 'success' : 'error'}
            size="small"
          />
        </Box>

        {/* Export Actions */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Copy interaction details" arrow>
            <IconButton
              size="small"
              onClick={() => handleCopy(JSON.stringify(interaction, null, 2), 'Interaction details')}
              aria-label="Copy interaction details"
            >
              <CopyIcon />
            </IconButton>
          </Tooltip>
          
          {allInteractions.length > 0 && (
            <Button
              size="small"
              startIcon={<CodeIcon />}
              onClick={handleExportTimeline}
              aria-label="Export full timeline"
            >
              Export Timeline
            </Button>
          )}
        </Box>
      </Box>

      {/* Overview Section */}
      <Accordion
        expanded={expandedSections.has('overview')}
        onChange={() => handleAccordionToggle('overview')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="overview-content"
          id="overview-header"
        >
          <Typography variant="h3">Overview</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
            {/* Step Description */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Step Description
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {interaction.step_description}
              </Typography>
            </Box>

            {/* Timestamp */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Timestamp
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TimeIcon fontSize="small" color="action" />
                <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace' }}>
                  {formatTimestamp(interaction.timestamp)}
                </Typography>
              </Box>
            </Box>

            {/* Duration */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Duration
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace' }}>
                {formatDuration(interaction.duration_ms)}
              </Typography>
            </Box>

            {/* Session ID */}
            <Box>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Session ID
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace' }}>
                {interaction.session_id}
              </Typography>
            </Box>
          </Box>

          {/* Error Message */}
          {interaction.error_message && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Error:</strong> {interaction.error_message}
              </Typography>
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Type-Specific Details */}
      <Accordion
        expanded={expandedSections.has('details')}
        onChange={() => handleAccordionToggle('details')}
        sx={{ mb: 2 }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="details-content"
          id="details-header"
        >
          <Typography variant="h3">
            {interaction.interaction_type === 'llm' ? 'LLM Details' : 'MCP Details'}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          {interaction.interaction_type === 'llm' ? (
            // LLM-specific details
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              {interaction.model && (
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Model
                  </Typography>
                  <Chip label={interaction.model} variant="outlined" size="small" />
                </Box>
              )}

              {interaction.tokens_used && (
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Tokens Used
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace' }}>
                    {interaction.tokens_used.toLocaleString()}
                  </Typography>
                </Box>
              )}
            </Box>
          ) : (
            // MCP-specific details
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              {interaction.server_name && (
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Server Name
                  </Typography>
                  <Chip label={interaction.server_name} variant="outlined" size="small" />
                </Box>
              )}

              {interaction.communication_type && (
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Communication Type
                  </Typography>
                  <Typography variant="body2">
                    {interaction.communication_type}
                  </Typography>
                </Box>
              )}

              {interaction.tool_name && (
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Tool Name
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace' }}>
                    {interaction.tool_name}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Tool Arguments (MCP only) */}
      {interaction.interaction_type === 'mcp' && interaction.tool_arguments && (
        <Accordion
          expanded={expandedSections.has('arguments')}
          onChange={() => handleAccordionToggle('arguments')}
          sx={{ mb: 2 }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="arguments-content"
            id="arguments-header"
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', mr: 2 }}>
              <Typography variant="h3">Tool Arguments</Typography>
              <Tooltip title="Copy tool arguments" arrow>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy(JSON.stringify(interaction.tool_arguments, null, 2), 'Tool arguments');
                  }}
                  aria-label="Copy tool arguments"
                >
                  <CopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box
              sx={{
                backgroundColor: 'grey.100',
                borderRadius: 1,
                p: 2,
                fontFamily: 'Roboto Mono, monospace',
                fontSize: '0.875rem',
                overflowX: 'auto',
              }}
            >
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(interaction.tool_arguments, null, 2)}
              </pre>
            </Box>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Raw Data */}
      <Accordion
        expanded={expandedSections.has('raw')}
        onChange={() => handleAccordionToggle('raw')}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="raw-content"
          id="raw-header"
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', mr: 2 }}>
            <Typography variant="h3">Raw Data</Typography>
            <Tooltip title="Copy raw interaction data" arrow>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCopy(JSON.stringify(interaction, null, 2), 'Raw interaction data');
                }}
                aria-label="Copy raw interaction data"
              >
                <CopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box
            sx={{
              backgroundColor: 'grey.100',
              borderRadius: 1,
              p: 2,
              fontFamily: 'Roboto Mono, monospace',
              fontSize: '0.875rem',
              overflowX: 'auto',
              maxHeight: 400,
              overflow: 'auto',
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(interaction, null, 2)}
            </pre>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Copy Success Snackbar */}
      <Snackbar
        open={!!copySuccess}
        autoHideDuration={3000}
        onClose={() => setCopySuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setCopySuccess(null)}>
          {copySuccess}
        </Alert>
      </Snackbar>
    </Paper>
  );
}

export default InteractionDetails; 