import JsonView from '@uiw/react-json-view';
import { Box, Typography, useTheme } from '@mui/material';

interface JsonDisplayProps {
  data: any;
  collapsed?: boolean | number;
  maxHeight?: number;
}

/**
 * JsonDisplay component - Phase 5
 * Pretty JSON viewer with syntax highlighting and Material-UI theming
 */
function JsonDisplay({ data, collapsed = true, maxHeight = 400 }: JsonDisplayProps) {
  const theme = useTheme();
  
  // Debug info for long content
  const contentLength = String(data).length;
  const showDebugInfo = contentLength > 1000;

  // Helper function to check if data should be displayed as JSON
  const shouldDisplayAsJson = (value: any): boolean => {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') {
      // Try to parse string to see if it's JSON
      try {
        const parsed = JSON.parse(value);
        return typeof parsed === 'object';
      } catch {
        return false;
      }
    }
    return typeof value === 'object';
  };

  // Parse string to object if needed
  const getDisplayData = () => {
    if (typeof data === 'string') {
      try {
        return JSON.parse(data);
      } catch {
        return data;
      }
    }
    return data;
  };

  const displayData = getDisplayData();

  // If it's not JSON-like data, display as plain text
  if (!shouldDisplayAsJson(data)) {
    return (
      <Box>
        {showDebugInfo && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            Content length: {contentLength.toLocaleString()} characters • Scrollable area
          </Typography>
        )}
        <Box 
          component="pre" 
          sx={{ 
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            m: 0,
            p: 2,
            bgcolor: theme.palette.grey[50],
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`,
            maxHeight: maxHeight,
            overflow: 'auto',
            position: 'relative',
            // Enhanced scrollbars
            '&::-webkit-scrollbar': {
              width: '10px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: theme.palette.grey[100],
              borderRadius: '6px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: theme.palette.grey[400],
              borderRadius: '6px',
              border: `2px solid ${theme.palette.grey[50]}`,
              '&:hover': {
                backgroundColor: theme.palette.primary.main,
              },
            },
            // Fade effect to indicate more content
            '&::after': contentLength > 1000 ? {
              content: '""',
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '20px',
              background: `linear-gradient(transparent, ${theme.palette.grey[50]})`,
              pointerEvents: 'none',
              borderRadius: '0 0 4px 4px',
            } : {}
          }}
        >
          {String(data)}
        </Box>
      </Box>
    );
  }

  // Display as pretty JSON
  return (
    <Box>
      {showDebugInfo && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          Content length: {contentLength.toLocaleString()} characters • Scrollable JSON
        </Typography>
      )}
      <Box sx={{ 
        position: 'relative',
        '& .w-rjv': {
          backgroundColor: `${theme.palette.grey[50]} !important`,
          borderRadius: theme.shape.borderRadius,
          border: `1px solid ${theme.palette.divider}`,
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace !important',
          fontSize: '0.875rem !important',
          maxHeight: maxHeight,
          overflow: 'auto',
          position: 'relative',
          '&::-webkit-scrollbar': {
            width: '10px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: theme.palette.grey[100],
            borderRadius: '6px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: theme.palette.grey[400],
            borderRadius: '6px',
            border: `2px solid ${theme.palette.grey[50]}`,
            '&:hover': {
              backgroundColor: theme.palette.primary.main,
            },
          }
        },
        '& .w-rjv-line': {
          borderColor: `${theme.palette.divider} !important`
        },
        // Fade effect for JSON content
        ...(contentLength > 1000 && {
          '&::after': {
            content: '""',
            position: 'absolute',
            bottom: '1px',
            left: '1px',
            right: '1px',
            height: '20px',
            background: `linear-gradient(transparent, ${theme.palette.grey[50]})`,
            pointerEvents: 'none',
            borderRadius: '0 0 4px 4px',
            zIndex: 1,
          }
        })
      }}>
        <JsonView 
          value={displayData}
          collapsed={collapsed}
          displayDataTypes={false}
          displayObjectSize={false}
          enableClipboard={false}
          style={{
            backgroundColor: theme.palette.grey[50],
            padding: theme.spacing(2),
          }}
        />
      </Box>
    </Box>
  );
}

export default JsonDisplay; 