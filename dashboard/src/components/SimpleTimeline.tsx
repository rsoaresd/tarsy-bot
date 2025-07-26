import { Paper, Typography, List, ListItem, ListItemIcon, ListItemText, Box } from '@mui/material';
import { Psychology, Build, Settings, Circle } from '@mui/icons-material';
import type { SimpleTimelineProps } from '../types';

/**
 * Get icon for interaction type
 */
const getInteractionIcon = (type: string) => {
  switch (type) {
    case 'llm':
      return <Psychology sx={{ color: 'primary.main' }} />;
    case 'mcp':
      return <Build sx={{ color: 'secondary.main' }} />;
    case 'system':
      return <Settings sx={{ color: 'info.main' }} />;
    default:
      return <Circle sx={{ color: 'grey.500', fontSize: 12 }} />;
  }
};

/**
 * Format timestamp for timeline display
 */
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch (error) {
    return timestamp;
  }
};

/**
 * Format duration in milliseconds
 */
const formatDuration = (durationMs: number | null): string => {
  if (!durationMs) return '';
  
  if (durationMs < 1000) {
    return `${durationMs}ms`;
  } else if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
};

/**
 * SimpleTimeline component - Phase 3
 * Displays a basic timeline of LLM/MCP interactions with icons and timestamps
 */
function SimpleTimeline({ timelineItems }: SimpleTimelineProps) {
  if (!timelineItems || timelineItems.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Settings color="primary" />
          Processing Timeline
        </Typography>
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            No timeline data available
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Settings color="primary" />
        Processing Timeline
      </Typography>
      
      <List sx={{ width: '100%' }}>
        {timelineItems.map((item, index) => (
          <ListItem 
            key={item.id}
            sx={{ 
              alignItems: 'flex-start',
              borderLeft: index < timelineItems.length - 1 ? '2px solid' : 'none',
              borderColor: 'divider',
              ml: 2,
              pl: 2,
              position: 'relative',
              '&::before': index < timelineItems.length - 1 ? {
                content: '""',
                position: 'absolute',
                left: -9,
                top: 48,
                bottom: 0,
                width: 2,
                backgroundColor: 'divider',
              } : {},
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
              {getInteractionIcon(item.type)}
            </ListItemIcon>
            
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                    {item.step_description}
                  </Typography>
                  {item.duration_ms && (
                    <Typography variant="caption" color="text.secondary">
                      ({formatDuration(item.duration_ms)})
                    </Typography>
                  )}
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {formatTimestamp(item.timestamp)} • {item.type.toUpperCase()}
                  </Typography>
                  {item.details && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      {item.type === 'llm' && 'details' in item.details && 
                        `Model: ${(item.details as any).model_name || 'Unknown'}`
                      }
                      {item.type === 'mcp' && 'details' in item.details && 
                        `Tool: ${(item.details as any).tool_name || 'Unknown'}`
                      }
                      {item.type === 'system' && 'details' in item.details && 
                        `Event: ${(item.details as any).event_type || 'Unknown'}`
                      }
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
      
      <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Timeline shows {timelineItems.length} interaction{timelineItems.length !== 1 ? 's' : ''} in chronological order
        </Typography>
      </Box>
    </Paper>
  );
}

export default SimpleTimeline; 