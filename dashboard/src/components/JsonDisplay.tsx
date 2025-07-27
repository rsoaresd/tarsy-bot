import JsonView from '@uiw/react-json-view';
import { Box, useTheme } from '@mui/material';

interface JsonDisplayProps {
  data: any;
  collapsed?: boolean | number;
}

/**
 * JsonDisplay component - Phase 5
 * Pretty JSON viewer with syntax highlighting and Material-UI theming
 */
function JsonDisplay({ data, collapsed = true }: JsonDisplayProps) {
  const theme = useTheme();

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
          maxHeight: 400,
          overflow: 'auto'
        }}
      >
        {String(data)}
      </Box>
    );
  }

  // Display as pretty JSON
  return (
    <Box sx={{ 
      '& .w-rjv': {
        backgroundColor: `${theme.palette.grey[50]} !important`,
        borderRadius: theme.shape.borderRadius,
        border: `1px solid ${theme.palette.divider}`,
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace !important',
        fontSize: '0.875rem !important',
        maxHeight: 400,
        overflow: 'auto'
      },
      '& .w-rjv-line': {
        borderColor: `${theme.palette.divider} !important`
      }
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
  );
}

export default JsonDisplay; 