import { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Card, 
  CardHeader, 
  CardContent,
  Chip,
  IconButton,
  CircularProgress,
  Avatar
} from '@mui/material';
import { 
  Psychology, 
  Build, 
  Settings, 
  ExpandMore, 
  ExpandLess
} from '@mui/icons-material';
import type { TimelineItem as TimelineItemType } from '../types';
import { formatTimestamp, formatDurationMs } from '../utils/timestamp';
import InteractionDetails from './InteractionDetails';

import CopyButton from './CopyButton';

interface TimelineVisualizationProps {
  timelineItems: TimelineItemType[];
  isActive?: boolean;
  sessionId?: string;
}

/**
 * TimelineVisualization component - Phase 5  
 * Enhanced timeline with Material-UI Timeline components and expandable interactions
 */
function TimelineVisualization({ 
  timelineItems, 
  isActive = false
}: TimelineVisualizationProps) {
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  const toggleExpansion = (itemId: string) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
  };

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case 'llm':
        return <Psychology />;
      case 'mcp':
        return <Build />;
      case 'system':
        return <Settings />;
      default:
        return <Settings />;
    }
  };

  const getInteractionColor = (type: string): 'primary' | 'secondary' | 'warning' => {
    switch (type) {
      case 'llm':
        return 'primary';    // Blue
      case 'mcp':
        return 'secondary';  // Purple  
      case 'system':
        return 'warning';    // Orange
      default:  
        return 'primary';
    }
  };



  if (!timelineItems || timelineItems.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
          Processing Timeline
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No timeline data available
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Processing Timeline
        </Typography>
        <CopyButton
          text={timelineItems.map(item => {
            const timestamp = formatTimestamp(item.timestamp_us, 'absolute');
            const duration = item.duration_ms ? ` (${formatDurationMs(item.duration_ms)})` : '';
            return `${timestamp}${duration} - ${item.type.toUpperCase()}: ${item.step_description}`;
          }).join('\n')}
          size="small"
          label="Copy Timeline"
          tooltip="Copy entire timeline"
        />
      </Box>

      {/* Custom Clean Timeline */}
      <Box sx={{ position: 'relative' }}>
        {timelineItems.map((item, index) => {
          const itemKey = item.id || `item-${index}`;
          return (
          <Box key={itemKey} sx={{ display: 'flex', position: 'relative' }}>
            {/* Timeline Line and Dot */}
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center',
              mr: 3,
              position: 'relative'
            }}>
              {/* Timeline Dot */}
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: `${getInteractionColor(item.type)}.main`,
                  color: 'white',
                  fontSize: '1rem',
                  zIndex: 2
                }}
              >
                {getInteractionIcon(item.type)}
              </Avatar>
              
              {/* Connecting Line */}
              {index < timelineItems.length - 1 && (
                <Box
                  sx={{
                    width: 2,
                    backgroundColor: 'divider',
                    flexGrow: 1,
                    minHeight: 32,
                    mt: 1,
                    mb: 1
                  }}
                />
              )}
            </Box>

            {/* Timeline Content */}
            <Box sx={{ flex: 1, mb: index < timelineItems.length - 1 ? 3 : 0 }}>
              <Card variant="outlined" sx={{ 
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  boxShadow: 2,
                  borderColor: `${getInteractionColor(item.type)}.main`
                }
              }}>
                <CardHeader
                  title={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {item.step_description}
                      </Typography>
                      {item.duration_ms && (
                        <Chip 
                          label={formatDurationMs(item.duration_ms)} 
                          size="small" 
                          variant="filled"
                          color={getInteractionColor(item.type)}
                          sx={{ fontSize: '0.75rem', height: 24 }}
                        />
                      )}
                    </Box>
                  }
                  subheader={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                        {formatTimestamp(item.timestamp_us, 'short')}
                      </Typography>
                      <Typography variant="body2" sx={{ color: `${getInteractionColor(item.type)}.main`, fontWeight: 500 }}>
                        • {item.type.toUpperCase()}
                      </Typography>
                    </Box>
                  }
                  action={
                    item.details && (
                      <IconButton 
                        onClick={() => toggleExpansion(itemKey)}
                        size="small"
                        sx={{ 
                          color: `${getInteractionColor(item.type)}.main`,
                          '&:hover': { bgcolor: `${getInteractionColor(item.type)}.light` }
                        }}
                      >
                        {expandedItems[itemKey] ? <ExpandLess /> : <ExpandMore />}
                      </IconButton>
                    )
                  }
                  sx={{ pb: item.details && !expandedItems[itemKey] ? 2 : 1 }}
                />
                
                {/* Expandable interaction details */}
                {item.details && (
                  <CardContent sx={{ pt: 0 }}>
                    <InteractionDetails
                      type={item.type}
                      details={item.details}
                      expanded={expandedItems[itemKey]}
                    />
                  </CardContent>
                )}
              </Card>
            </Box>
          </Box>
          );
        })}
      </Box>

      {/* Real-time indicator for active sessions */}
      {isActive && (
        <Box sx={{ 
          mt: 2, 
          p: 2, 
          bgcolor: 'info.50', 
          borderRadius: 1, 
          border: 1, 
          borderColor: 'info.200',
          display: 'flex', 
          alignItems: 'center', 
          gap: 1 
        }}>
          <CircularProgress size={16} color="info" />
          <Typography variant="body2" color="info.main" sx={{ fontWeight: 500 }}>
            Waiting for next interaction...
          </Typography>
        </Box>
      )}

      {/* Timeline summary */}
      <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Timeline shows {timelineItems.length} interaction{timelineItems.length !== 1 ? 's' : ''} in chronological order
          {isActive && ' • Updates automatically for active sessions'}
        </Typography>
      </Box>
    </Paper>
  );
}

export default TimelineVisualization; 