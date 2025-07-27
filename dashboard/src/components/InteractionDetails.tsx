import { 
  Box, 
  Typography, 
  Collapse, 
  Divider,
  Stack
} from '@mui/material';
import type { LLMInteraction, MCPInteraction, SystemEvent } from '../types';
import CopyButton from './CopyButton';
import JsonDisplay from './JsonDisplay';

interface InteractionDetailsProps {
  type: 'llm' | 'mcp' | 'system';
  details: LLMInteraction | MCPInteraction | SystemEvent;
  expanded?: boolean;
}

/**
 * InteractionDetails component - Phase 5
 * Expandable detailed view of LLM/MCP interactions with copy functionality
 */
function InteractionDetails({ 
  type, 
  details, 
  expanded = false
}: InteractionDetailsProps) {

  const renderLLMDetails = (llmDetails: LLMInteraction) => (
    <Stack spacing={2}>
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Prompt
          </Typography>
          <CopyButton
            text={llmDetails.prompt}
            variant="icon"
            size="small"
            tooltip="Copy prompt"
          />
        </Box>
                                                    <JsonDisplay data={llmDetails.prompt} />
        </Box>
        
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Response
            </Typography>
            <CopyButton
              text={llmDetails.response}
              variant="icon"
              size="small"
              tooltip="Copy response"
            />
          </Box>
         <JsonDisplay data={llmDetails.response} />
      </Box>

      {/* Model metadata */}
      <Box>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Model Information
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Typography variant="body2" color="text.secondary">
            <strong>Model:</strong> {llmDetails.model_name}
          </Typography>
          {llmDetails.tokens_used && (
            <Typography variant="body2" color="text.secondary">
              <strong>Tokens:</strong> {llmDetails.tokens_used.toLocaleString()}
            </Typography>
          )}
          {llmDetails.temperature !== undefined && (
            <Typography variant="body2" color="text.secondary">
              <strong>Temperature:</strong> {llmDetails.temperature}
            </Typography>
          )}
        </Stack>
      </Box>
    </Stack>
  );

  const renderMCPDetails = (mcpDetails: MCPInteraction) => (
    <Stack spacing={2}>
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Tool Call
          </Typography>
          <CopyButton
            text={`${mcpDetails.tool_name}(${JSON.stringify(mcpDetails.parameters, null, 2)})`}
            variant="icon"
            size="small"
            tooltip="Copy tool call"
          />
        </Box>
        <Box>
          <Typography 
            variant="body2" 
            sx={{ 
              fontFamily: 'monospace', 
              fontSize: '0.875rem',
              fontWeight: 600,
              mb: 1,
              p: 1,
              bgcolor: 'grey.100',
              borderRadius: 1
            }}
          >
            {mcpDetails.tool_name}
          </Typography>
          {Object.keys(mcpDetails.parameters).length > 0 && (
            <JsonDisplay data={mcpDetails.parameters} collapsed={1} />
          )}
        </Box>
      </Box>
      
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Result
          </Typography>
          <CopyButton
            text={JSON.stringify(mcpDetails.result, null, 2)}
            variant="icon"
            size="small"
            tooltip="Copy result"
          />
        </Box>
        <JsonDisplay data={mcpDetails.result} collapsed={1} />
      </Box>

      {/* MCP metadata */}
      <Box>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Tool Information
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Typography variant="body2" color="text.secondary">
            <strong>Server:</strong> {mcpDetails.server_name}
          </Typography>
          {mcpDetails.execution_time_ms && (
            <Typography variant="body2" color="text.secondary">
              <strong>Execution Time:</strong> {mcpDetails.execution_time_ms}ms
            </Typography>
          )}
        </Stack>
      </Box>
    </Stack>
  );

  const renderSystemDetails = (systemDetails: SystemEvent) => (
    <Stack spacing={2}>
      <Box>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Event Description
        </Typography>
        <JsonDisplay data={systemDetails.description} />
      </Box>

      {systemDetails.metadata && Object.keys(systemDetails.metadata).length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Metadata
            </Typography>
            <CopyButton
              text={JSON.stringify(systemDetails.metadata, null, 2)}
              variant="icon"
              size="small"
              tooltip="Copy metadata"
            />
          </Box>
          <JsonDisplay data={systemDetails.metadata} collapsed={1} />
        </Box>
      )}
    </Stack>
  );

  const renderDetails = () => {
    switch (type) {
      case 'llm':
        return renderLLMDetails(details as LLMInteraction);
      case 'mcp':
        return renderMCPDetails(details as MCPInteraction);
      case 'system':
        return renderSystemDetails(details as SystemEvent);
      default:
        return (
          <Typography variant="body2" color="text.secondary">
            No details available for this interaction type.
          </Typography>
        );
    }
  };

  const getInteractionText = () => {
    switch (type) {
      case 'llm':
        const llm = details as LLMInteraction;
        return `${llm.prompt}\n\n---\n\n${llm.response}`;
      case 'mcp':
        const mcp = details as MCPInteraction;
        return `${mcp.tool_name}(${JSON.stringify(mcp.parameters, null, 2)})\n\n---\n\n${JSON.stringify(mcp.result, null, 2)}`;
      case 'system':
        const system = details as SystemEvent;
        return `${system.description}${system.metadata ? '\n\n' + JSON.stringify(system.metadata, null, 2) : ''}`;
      default:
        return '';
    }
  };

  return (
    <Collapse in={expanded}>
      <Box sx={{ pt: 1 }}>
        <Divider sx={{ mb: 2 }} />
        {renderDetails()}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start' }}>
          <CopyButton
            text={getInteractionText()}
            size="small"
            label="Copy All Details"
            tooltip="Copy all interaction details"
          />
        </Box>
      </Box>
    </Collapse>
  );
}

export default InteractionDetails; 