import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Alert,
  Divider,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  MoreVert as MoreIcon,
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
  Code as CodeIcon,
  FileCopy as FileCopyIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { SessionSummary, InteractionDetail } from '../types';

interface SessionActionsProps {
  session: SessionSummary;
  interactions?: InteractionDetail[];
  isActive?: boolean;
  onRefresh?: () => void;
  showBackButton?: boolean;
}

function SessionActions({ 
  session, 
  interactions = [], 
  isActive = false, 
  onRefresh,
  showBackButton = true,
}: SessionActionsProps) {
  const navigate = useNavigate();
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const menuOpen = Boolean(menuAnchorEl);

  // Handle menu open/close
  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchorEl(event.currentTarget);
  }, []);

  const handleMenuClose = useCallback(() => {
    setMenuAnchorEl(null);
  }, []);

  // Handle copy to clipboard
  const handleCopy = useCallback(async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(`${label} copied to clipboard`);
      setTimeout(() => setCopySuccess(null), 3000);
      handleMenuClose();
    } catch (err) {
      console.error('Failed to copy:', err);
      setCopySuccess('Failed to copy to clipboard');
      setTimeout(() => setCopySuccess(null), 3000);
    }
  }, [handleMenuClose]);

  // Handle back navigation
  const handleBack = useCallback(() => {
    navigate('/dashboard');
  }, [navigate]);

  // Copy session summary
  const handleCopySessionSummary = useCallback(async () => {
    const summary = {
      session_id: session.session_id,
      agent_type: session.agent_type,
      status: session.status,
      start_time: session.start_time,
      last_activity: session.last_activity,
      interactions_count: session.interactions_count,
      llm_interactions: session.llm_interactions,
      mcp_communications: session.mcp_communications,
      errors_count: session.errors_count,
      current_step: session.current_step,
    };
    
    await handleCopy(JSON.stringify(summary, null, 2), 'Session summary');
  }, [session, handleCopy]);

  // Copy session ID
  const handleCopySessionId = useCallback(async () => {
    await handleCopy(session.session_id, 'Session ID');
  }, [session.session_id, handleCopy]);

  // Copy session URL
  const handleCopySessionUrl = useCallback(async () => {
    const url = `${window.location.origin}/sessions/${session.session_id}`;
    await handleCopy(url, 'Session URL');
  }, [session.session_id, handleCopy]);

  // Export timeline data
  const handleExportTimeline = useCallback(async () => {
    if (interactions.length === 0) {
      setCopySuccess('No timeline data available to export');
      setTimeout(() => setCopySuccess(null), 3000);
      return;
    }

    const timelineData = {
      session: {
        id: session.session_id,
        agent_type: session.agent_type,
        status: session.status,
        start_time: session.start_time,
        end_time: session.last_activity,
      },
      interactions: interactions.map(interaction => ({
        timestamp: interaction.timestamp,
        type: interaction.interaction_type,
        step: interaction.step_description,
        duration_ms: interaction.duration_ms,
        success: interaction.success,
        error: interaction.error_message || null,
        // Type-specific data
        ...(interaction.interaction_type === 'llm' ? {
          model: interaction.model,
          tokens_used: interaction.tokens_used,
        } : {
          server_name: interaction.server_name,
          tool_name: interaction.tool_name,
          tool_arguments: interaction.tool_arguments,
        }),
      })),
      metadata: {
        exported_at: new Date().toISOString(),
        total_interactions: interactions.length,
        llm_interactions: interactions.filter(i => i.interaction_type === 'llm').length,
        mcp_communications: interactions.filter(i => i.interaction_type === 'mcp').length,
        errors: interactions.filter(i => !i.success).length,
      },
    };

    await handleCopy(JSON.stringify(timelineData, null, 2), 'Timeline data');
  }, [interactions, session, handleCopy]);

  // Download timeline as file
  const handleDownloadTimeline = useCallback(() => {
    if (interactions.length === 0) {
      setCopySuccess('No timeline data available to download');
      setTimeout(() => setCopySuccess(null), 3000);
      return;
    }

    const timelineData = {
      session: {
        id: session.session_id,
        agent_type: session.agent_type,
        status: session.status,
        start_time: session.start_time,
        end_time: session.last_activity,
      },
      interactions: interactions.map(interaction => ({
        timestamp: interaction.timestamp,
        type: interaction.interaction_type,
        step: interaction.step_description,
        duration_ms: interaction.duration_ms,
        success: interaction.success,
        error: interaction.error_message || null,
        ...(interaction.interaction_type === 'llm' ? {
          model: interaction.model,
          tokens_used: interaction.tokens_used,
        } : {
          server_name: interaction.server_name,
          tool_name: interaction.tool_name,
          tool_arguments: interaction.tool_arguments,
        }),
      })),
      metadata: {
        exported_at: new Date().toISOString(),
        total_interactions: interactions.length,
        llm_interactions: interactions.filter(i => i.interaction_type === 'llm').length,
        mcp_communications: interactions.filter(i => i.interaction_type === 'mcp').length,
        errors: interactions.filter(i => !i.success).length,
      },
    };

    const blob = new Blob([JSON.stringify(timelineData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `session-${session.session_id}-timeline.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setCopySuccess('Timeline downloaded successfully');
    setTimeout(() => setCopySuccess(null), 3000);
    handleMenuClose();
  }, [interactions, session, handleMenuClose]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  }, []);

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
      {/* Primary Actions */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {/* Back Button */}
        {showBackButton && (
          <Button
            startIcon={<BackIcon />}
            onClick={handleBack}
            onKeyDown={(e) => handleKeyDown(e, handleBack)}
            variant="outlined"
            size="medium"
            aria-label="Back to dashboard"
          >
            Back to Dashboard
          </Button>
        )}

        {/* Refresh Button (for active sessions) */}
        {isActive && onRefresh && (
          <Tooltip title="Refresh session data" arrow>
            <IconButton
              onClick={onRefresh}
              onKeyDown={(e) => handleKeyDown(e, onRefresh)}
              aria-label="Refresh session data"
              size="medium"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Quick Actions */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {/* Copy Session ID */}
        <Tooltip title="Copy session ID" arrow>
          <IconButton
            onClick={handleCopySessionId}
            onKeyDown={(e) => handleKeyDown(e, handleCopySessionId)}
            aria-label="Copy session ID"
            size="medium"
          >
            <CopyIcon />
          </IconButton>
        </Tooltip>

        {/* Export Timeline (if available) */}
        {interactions.length > 0 && (
          <Button
            startIcon={<CodeIcon />}
            onClick={handleExportTimeline}
            onKeyDown={(e) => handleKeyDown(e, handleExportTimeline)}
            variant="contained"
            size="medium"
            aria-label="Export timeline data"
          >
            Export Timeline
          </Button>
        )}

        {/* More Actions Menu */}
        <Tooltip title="More actions" arrow>
          <IconButton
            onClick={handleMenuOpen}
            onKeyDown={(e) => handleKeyDown(e, () => handleMenuOpen(e as any))}
            aria-label="More actions"
            aria-expanded={menuOpen ? 'true' : 'false'}
            aria-haspopup="true"
            size="medium"
          >
            <MoreIcon />
          </IconButton>
        </Tooltip>

        {/* Actions Menu */}
        <Menu
          anchorEl={menuAnchorEl}
          open={menuOpen}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          MenuListProps={{
            'aria-labelledby': 'more-actions-button',
            role: 'menu',
          }}
        >
          {/* Copy Actions */}
          <MenuItem
            onClick={handleCopySessionSummary}
            role="menuitem"
            aria-label="Copy session summary"
          >
            <ListItemIcon>
              <FileCopyIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Copy Session Summary</ListItemText>
          </MenuItem>

          <MenuItem
            onClick={handleCopySessionUrl}
            role="menuitem"
            aria-label="Copy session URL"
          >
            <ListItemIcon>
              <LinkIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Copy Session URL</ListItemText>
          </MenuItem>

          <Divider />

          {/* Export Actions */}
          {interactions.length > 0 && (
            <MenuItem
              onClick={handleDownloadTimeline}
              role="menuitem"
              aria-label="Download timeline as file"
            >
              <ListItemIcon>
                <DownloadIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Download Timeline</ListItemText>
            </MenuItem>
          )}

          {/* Refresh (for active sessions) */}
          {isActive && onRefresh && (
            <>
              <Divider />
              <MenuItem
                onClick={() => {
                  onRefresh();
                  handleMenuClose();
                }}
                role="menuitem"
                aria-label="Refresh session data"
              >
                <ListItemIcon>
                  <RefreshIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>
                  Refresh Session
                  {isActive && (
                    <Box component="span" sx={{ color: 'success.main', ml: 1 }}>
                      (Live)
                    </Box>
                  )}
                </ListItemText>
              </MenuItem>
            </>
          )}
        </Menu>
      </Box>

      {/* Success/Error Snackbar */}
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
    </Box>
  );
}

export default SessionActions; 