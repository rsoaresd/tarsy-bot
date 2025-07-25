import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tooltip,
  IconButton,
  Zoom,
  useTheme,
} from '@mui/material';
import {
  Psychology as LLMIcon,
  Settings as MCPIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  FitScreen as FitScreenIcon,
} from '@mui/icons-material';
import { InteractionDetail } from '../types';

interface TimelineVisualizationProps {
  interactions: InteractionDetail[];
  isActive?: boolean;
  onInteractionClick?: (interaction: InteractionDetail) => void;
  height?: number;
}

interface TimelinePoint {
  interaction: InteractionDetail;
  x: number;
  y: number;
  timestamp: Date;
}

function TimelineVisualization({ 
  interactions, 
  isActive = false, 
  onInteractionClick,
  height = 400,
}: TimelineVisualizationProps) {
  const theme = useTheme();
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedInteraction, setSelectedInteraction] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });

  const svgWidth = 800;
  const svgHeight = height - 100; // Leave space for controls
  const margin = { top: 40, right: 40, bottom: 60, left: 60 };
  const plotWidth = svgWidth - margin.left - margin.right;
  const plotHeight = svgHeight - margin.top - margin.bottom;

  // Process timeline data
  const timelineData = useMemo(() => {
    if (!interactions.length) return { points: [], timeRange: { start: new Date(), end: new Date() } };

    const sortedInteractions = [...interactions].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const startTime = new Date(sortedInteractions[0].timestamp);
    const endTime = isActive 
      ? new Date() // For active sessions, end time is now
      : new Date(sortedInteractions[sortedInteractions.length - 1].timestamp);

    const timeRange = endTime.getTime() - startTime.getTime();

    // Create timeline points
    const points: TimelinePoint[] = sortedInteractions.map((interaction, index) => {
      const timestamp = new Date(interaction.timestamp);
      const relativeTime = timestamp.getTime() - startTime.getTime();
      const x = margin.left + (relativeTime / timeRange) * plotWidth;
      
      // Alternate between two tracks for LLM and MCP
      const trackOffset = interaction.interaction_type === 'llm' ? -20 : 20;
      const y = margin.top + plotHeight / 2 + trackOffset;

      return {
        interaction,
        x,
        y,
        timestamp,
      };
    });

    return { points, timeRange: { start: startTime, end: endTime } };
  }, [interactions, isActive, plotWidth, plotHeight]);

  // Handle interaction point click
  const handlePointClick = useCallback((interaction: InteractionDetail) => {
    setSelectedInteraction(interaction.interaction_id);
    onInteractionClick?.(interaction);
  }, [onInteractionClick]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent, interaction: InteractionDetail) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handlePointClick(interaction);
    }
  }, [handlePointClick]);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev * 1.5, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev / 1.5, 0.5));
  }, []);

  const handleFitToScreen = useCallback(() => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  }, []);

  // Get interaction icon and color
  const getInteractionDisplay = (interaction: InteractionDetail) => {
    const isError = !interaction.success;
    
    if (interaction.interaction_type === 'llm') {
      return {
        icon: LLMIcon,
        color: isError ? theme.palette.error.main : theme.palette.info.main,
        bgColor: isError ? theme.palette.error.light : theme.palette.info.light,
        label: 'LLM Interaction',
      };
    } else {
      return {
        icon: MCPIcon,
        color: isError ? theme.palette.error.main : theme.palette.warning.main,
        bgColor: isError ? theme.palette.error.light : theme.palette.warning.light,
        label: 'MCP Communication',
      };
    }
  };

  // Format duration for display
  const formatDuration = (durationMs: number) => {
    if (durationMs < 1000) return `${durationMs}ms`;
    if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
    return `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`;
  };

  // Format timestamp for axis
  const formatTimeAxis = (timestamp: Date, isStart: boolean = false) => {
    const now = new Date();
    const diffMs = now.getTime() - timestamp.getTime();
    
    if (diffMs < 3600000) { // Less than 1 hour
      return timestamp.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    }
    
    return timestamp.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  if (!interactions.length) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center', height }}>
        <Typography variant="h3" color="text.secondary" gutterBottom>
          No Timeline Data Available
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {isActive ? 'Waiting for interactions...' : 'No interactions found for this session.'}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      {/* Header with Controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box>
          <Typography variant="h2" component="h2" gutterBottom>
            Processing Timeline
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {interactions.length} interaction{interactions.length !== 1 ? 's' : ''} • 
            Duration: {formatDuration(
              timelineData.timeRange.end.getTime() - timelineData.timeRange.start.getTime()
            )}
          </Typography>
        </Box>

        {/* Timeline Controls */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Zoom In" arrow>
            <IconButton
              size="small"
              onClick={handleZoomIn}
              disabled={zoomLevel >= 5}
              aria-label="Zoom in timeline"
            >
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Zoom Out" arrow>
            <IconButton
              size="small"
              onClick={handleZoomOut}
              disabled={zoomLevel <= 0.5}
              aria-label="Zoom out timeline"
            >
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Fit to Screen" arrow>
            <IconButton
              size="small"
              onClick={handleFitToScreen}
              aria-label="Fit timeline to screen"
            >
              <FitScreenIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* SVG Timeline */}
      <Box
        sx={{
          width: '100%',
          height: svgHeight,
          overflow: 'hidden',
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
          backgroundColor: 'background.paper',
        }}
      >
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{
            transform: `scale(${zoomLevel}) translate(${panOffset.x}px, ${panOffset.y}px)`,
            transition: 'transform 0.2s ease-in-out',
          }}
          role="img"
          aria-label="Timeline visualization of session interactions"
        >
          {/* Timeline Base Line */}
          <line
            x1={margin.left}
            y1={margin.top + plotHeight / 2}
            x2={margin.left + plotWidth}
            y2={margin.top + plotHeight / 2}
            stroke={theme.palette.divider}
            strokeWidth="2"
            aria-hidden="true"
          />

          {/* LLM Track Label */}
          <text
            x={margin.left - 10}
            y={margin.top + plotHeight / 2 - 25}
            textAnchor="end"
            fontSize="12"
            fill={theme.palette.text.secondary}
            aria-hidden="true"
          >
            LLM
          </text>

          {/* MCP Track Label */}
          <text
            x={margin.left - 10}
            y={margin.top + plotHeight / 2 + 35}
            textAnchor="end"
            fontSize="12"
            fill={theme.palette.text.secondary}
            aria-hidden="true"
          >
            MCP
          </text>

          {/* Time Axis */}
          <line
            x1={margin.left}
            y1={margin.top + plotHeight + 10}
            x2={margin.left + plotWidth}
            y2={margin.top + plotHeight + 10}
            stroke={theme.palette.divider}
            strokeWidth="1"
            aria-hidden="true"
          />

          {/* Start Time Label */}
          <text
            x={margin.left}
            y={margin.top + plotHeight + 30}
            textAnchor="start"
            fontSize="11"
            fill={theme.palette.text.secondary}
            aria-hidden="true"
          >
            {formatTimeAxis(timelineData.timeRange.start, true)}
          </text>

          {/* End Time Label */}
          <text
            x={margin.left + plotWidth}
            y={margin.top + plotHeight + 30}
            textAnchor="end"
            fontSize="11"
            fill={theme.palette.text.secondary}
            aria-hidden="true"
          >
            {formatTimeAxis(timelineData.timeRange.end)}
            {isActive && (
              <tspan fill={theme.palette.success.main}> (Live)</tspan>
            )}
          </text>

          {/* Interaction Points */}
          {timelineData.points.map((point, index) => {
            const display = getInteractionDisplay(point.interaction);
            const isSelected = selectedInteraction === point.interaction.interaction_id;
            const IconComponent = display.icon;

            return (
              <g key={point.interaction.interaction_id}>
                {/* Connection Line to Main Timeline */}
                <line
                  x1={point.x}
                  y1={margin.top + plotHeight / 2}
                  x2={point.x}
                  y2={point.y}
                  stroke={display.color}
                  strokeWidth="1"
                  strokeDasharray={point.interaction.success ? "none" : "3,3"}
                  aria-hidden="true"
                />

                {/* Interaction Point */}
                <Tooltip
                  title={
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {point.interaction.step_description}
                      </Typography>
                      <Typography variant="caption" display="block">
                        {display.label} • {formatDuration(point.interaction.duration_ms)}
                      </Typography>
                      <Typography variant="caption" display="block">
                        {point.interaction.timestamp}
                      </Typography>
                      {point.interaction.error_message && (
                        <Typography variant="caption" color="error" display="block">
                          Error: {point.interaction.error_message}
                        </Typography>
                      )}
                    </Box>
                  }
                  arrow
                  placement="top"
                >
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r={isSelected ? 12 : 8}
                    fill={display.bgColor}
                    stroke={display.color}
                    strokeWidth={isSelected ? 3 : 2}
                    style={{
                      cursor: 'pointer',
                      transition: 'all 0.2s ease-in-out',
                      filter: isSelected ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' : 'none',
                    }}
                    onClick={() => handlePointClick(point.interaction)}
                    onKeyDown={(e) => handleKeyDown(e as any, point.interaction)}
                    tabIndex={0}
                    role="button"
                    aria-label={`${display.label}: ${point.interaction.step_description} at ${point.interaction.timestamp}`}
                    aria-pressed={isSelected}
                  />
                </Tooltip>

                {/* Success/Error Indicator */}
                {!point.interaction.success && (
                  <text
                    x={point.x}
                    y={point.y}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize="10"
                    fill={theme.palette.error.contrastText}
                    pointerEvents="none"
                    aria-hidden="true"
                  >
                    ✗
                  </text>
                )}

                {/* Real-time Animation for Active Sessions */}
                {isActive && index === timelineData.points.length - 1 && (
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="15"
                    fill="none"
                    stroke={theme.palette.primary.main}
                    strokeWidth="2"
                    opacity="0.7"
                    aria-hidden="true"
                  >
                    <animate
                      attributeName="r"
                      values="8;20;8"
                      dur="2s"
                      repeatCount="indefinite"
                    />
                    <animate
                      attributeName="opacity"
                      values="0.7;0;0.7"
                      dur="2s"
                      repeatCount="indefinite"
                    />
                  </circle>
                )}
              </g>
            );
          })}

          {/* Progress Indicator for Active Sessions */}
          {isActive && (
            <text
              x={margin.left + plotWidth + 10}
              y={margin.top + plotHeight / 2}
              fontSize="12"
              fill={theme.palette.success.main}
              aria-live="polite"
              aria-label="Session is active and updating in real-time"
            >
              ● Live
            </text>
          )}
        </svg>
      </Box>

      {/* Legend */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3, mt: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              backgroundColor: theme.palette.info.main,
            }}
            aria-hidden="true"
          />
          <Typography variant="caption">LLM Interactions</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              backgroundColor: theme.palette.warning.main,
            }}
            aria-hidden="true"
          />
          <Typography variant="caption">MCP Communications</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              backgroundColor: theme.palette.error.main,
            }}
            aria-hidden="true"
          />
          <Typography variant="caption">Errors</Typography>
        </Box>
      </Box>

      {/* ARIA Live Region for Real-time Updates */}
      {isActive && (
        <Box
          aria-live="polite"
          aria-atomic="false"
          style={{
            position: 'absolute',
            left: '-10000px',
            width: '1px',
            height: '1px',
            overflow: 'hidden',
          }}
        >
          Session timeline is updating in real-time. {interactions.length} interactions so far.
        </Box>
      )}
    </Paper>
  );
}

export default TimelineVisualization; 