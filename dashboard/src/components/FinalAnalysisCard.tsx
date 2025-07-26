import { useState } from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  Button, 
  Alert, 
  AlertTitle,
  Snackbar
} from '@mui/material';
import { 
  Psychology, 
  ContentCopy, 
  ExpandMore, 
  ExpandLess 
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import type { FinalAnalysisCardProps } from '../types';

/**
 * FinalAnalysisCard component - Phase 3
 * Renders AI analysis markdown content with expand/collapse functionality and copy-to-clipboard feature
 */
function FinalAnalysisCard({ analysis, sessionStatus, errorMessage }: FinalAnalysisCardProps) {
  const [analysisExpanded, setAnalysisExpanded] = useState<boolean>(false);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  // Handle copy to clipboard
  const handleCopyAnalysis = async () => {
    if (!analysis) return;
    
    try {
      await navigator.clipboard.writeText(analysis);
      setCopySuccess(true);
    } catch (error) {
      console.error('Failed to copy analysis:', error);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = analysis;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopySuccess(true);
    }
  };

  // Handle snackbar close
  const handleSnackbarClose = () => {
    setCopySuccess(false);
  };

  // Show error state if session failed and no analysis available
  if (sessionStatus === 'failed' && !analysis && errorMessage) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Psychology color="primary" />
          Final AI Analysis
        </Typography>
        
        <Alert severity="error" sx={{ mt: 2 }}>
          <AlertTitle>Processing Error</AlertTitle>
          <Typography variant="body2">
            Session failed before analysis could be completed.
          </Typography>
          <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {errorMessage}
          </Typography>
        </Alert>
      </Paper>
    );
  }

  // Show empty state if no analysis available
  if (!analysis) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Psychology color="primary" />
          Final AI Analysis
        </Typography>
        
        {sessionStatus === 'in_progress' ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Analysis will be available when session completes
            </Typography>
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No analysis available for this session
            </Typography>
          </Box>
        )}
      </Paper>
    );
  }

  const isLongAnalysis = analysis.length > 1000;
  const shouldShowExpandButton = isLongAnalysis && !analysisExpanded;

  return (
    <>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Psychology color="primary" />
            Final AI Analysis
          </Typography>
          <Button
            startIcon={<ContentCopy />}
            variant="outlined"
            size="small"
            onClick={handleCopyAnalysis}
          >
            Copy Analysis
          </Button>
        </Box>

        {/* Analysis Content with Expand/Collapse */}
        <Box sx={{ position: 'relative' }}>
          <Box 
            sx={{ 
              maxHeight: analysisExpanded ? 'none' : isLongAnalysis ? '400px' : 'none',
              overflow: 'hidden',
              transition: 'max-height 0.3s ease-in-out'
            }}
          >
            <Paper 
              variant="outlined" 
              sx={{ 
                p: 3, 
                bgcolor: 'grey.50',
                '& pre': { 
                  whiteSpace: 'pre-wrap', 
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  backgroundColor: 'rgba(0, 0, 0, 0.05)',
                  padding: 2,
                  borderRadius: 1,
                  overflow: 'auto'
                },
                '& code': {
                  backgroundColor: 'rgba(0, 0, 0, 0.08)',
                  padding: '2px 4px',
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                },
                '& h1, & h2, & h3': {
                  color: 'primary.main',
                  marginTop: 2,
                  marginBottom: 1
                },
                '& ul, & ol': {
                  paddingLeft: 3
                },
                '& blockquote': {
                  borderLeft: '4px solid',
                  borderColor: 'primary.main',
                  paddingLeft: 2,
                  marginLeft: 0,
                  fontStyle: 'italic',
                  color: 'text.secondary'
                }
              }}
            >
              <ReactMarkdown>{analysis}</ReactMarkdown>
            </Paper>
          </Box>

          {/* Fade overlay and expand button when collapsed */}
          {shouldShowExpandButton && (
            <>
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: '80px',
                  background: 'linear-gradient(transparent, white)',
                  pointerEvents: 'none'
                }}
              />
              <Box sx={{ textAlign: 'center', mt: 1 }}>
                <Button
                  variant="text"
                  startIcon={<ExpandMore />}
                  onClick={() => setAnalysisExpanded(true)}
                >
                  Show Full Analysis
                </Button>
              </Box>
            </>
          )}

          {/* Collapse button when expanded */}
          {analysisExpanded && isLongAnalysis && (
            <Box sx={{ textAlign: 'center', mt: 1 }}>
              <Button
                variant="text"
                startIcon={<ExpandLess />}
                onClick={() => setAnalysisExpanded(false)}
              >
                Show Less
              </Button>
            </Box>
          )}
        </Box>

        {/* Error message for failed sessions with analysis */}
        {sessionStatus === 'failed' && errorMessage && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <AlertTitle>Session completed with errors</AlertTitle>
            <Typography variant="body2">
              {errorMessage}
            </Typography>
          </Alert>
        )}
      </Paper>

      {/* Copy success snackbar */}
      <Snackbar
        open={copySuccess}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
        message="Analysis copied to clipboard"
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </>
  );
}

export default FinalAnalysisCard; 