/**
 * Result display component to show the LLM analysis results
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ResultDisplayProps {
  result: string;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([result], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tarsy-analysis-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Custom components for ReactMarkdown
  const markdownComponents = {
    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={tomorrow}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    h1: ({ children }: any) => (
      <Typography variant="h4" component="h1" gutterBottom>
        {children}
      </Typography>
    ),
    h2: ({ children }: any) => (
      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        {children}
      </Typography>
    ),
    h3: ({ children }: any) => (
      <Typography variant="h6" component="h3" gutterBottom sx={{ mt: 2 }}>
        {children}
      </Typography>
    ),
    p: ({ children }: any) => (
      <Typography variant="body1" paragraph>
        {children}
      </Typography>
    ),
    ul: ({ children }: any) => (
      <Box component="ul" sx={{ pl: 2, mb: 2 }}>
        {children}
      </Box>
    ),
    ol: ({ children }: any) => (
      <Box component="ol" sx={{ pl: 2, mb: 2 }}>
        {children}
      </Box>
    ),
    li: ({ children }: any) => (
      <Typography component="li" variant="body1" sx={{ mb: 0.5 }}>
        {children}
      </Typography>
    ),
    blockquote: ({ children }: any) => (
      <Box
        sx={{
          borderLeft: 4,
          borderColor: 'primary.main',
          pl: 2,
          py: 1,
          mb: 2,
          backgroundColor: 'grey.50',
        }}
      >
        {children}
      </Box>
    ),
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <AnalyticsIcon color="primary" />
            <Typography variant="h6">
              AI Analysis Results
            </Typography>
            <Chip label="Completed" color="success" size="small" />
          </Box>
          
          <Box display="flex" gap={1}>
            <Tooltip title={copied ? 'Copied!' : 'Copy to clipboard'}>
              <IconButton onClick={handleCopyToClipboard} size="small">
                <CopyIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Download as Markdown">
              <IconButton onClick={handleDownload} size="small">
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1" fontWeight="medium">
              📊 Full Analysis Report
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box
              sx={{
                maxHeight: '70vh',
                overflow: 'auto',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                p: 2,
                backgroundColor: 'background.paper',
              }}
            >
              <ReactMarkdown components={markdownComponents}>
                {result}
              </ReactMarkdown>
            </Box>
          </AccordionDetails>
        </Accordion>

        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            Analysis generated at {new Date().toLocaleString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ResultDisplay; 