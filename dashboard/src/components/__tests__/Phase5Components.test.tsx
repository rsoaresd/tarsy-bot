import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CopyButton from '../CopyButton';
import ProgressIndicator from '../ProgressIndicator';
import TimelineVisualization from '../TimelineVisualization';
import type { TimelineItem } from '../../types';

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
});

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Phase 5 Components', () => {
  describe('CopyButton', () => {
    it('renders copy button with correct label', () => {
      renderWithTheme(
        <CopyButton text="test text" label="Copy Test" />
      );
      
      expect(screen.getByText('Copy Test')).toBeInTheDocument();
    });

    it('renders icon variant', () => {
      renderWithTheme(
        <CopyButton text="test text" variant="icon" />
      );
      
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });

  describe('ProgressIndicator', () => {
    it('shows progress for in_progress status', () => {
      renderWithTheme(
        <ProgressIndicator 
          status="in_progress" 
          startedAt={Date.now() * 1000}
          showDuration={true}
        />
      );
      
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('shows duration for completed status', () => {
      renderWithTheme(
        <ProgressIndicator 
          status="completed" 
          duration={5000}
          showDuration={true}
        />
      );
      
      expect(screen.getByText('5s')).toBeInTheDocument();
    });

    it('does not render when duration is null and status is completed', () => {
      const { container } = renderWithTheme(
        <ProgressIndicator 
          status="completed" 
          duration={null}
          showDuration={true}
        />
      );
      
      expect(container.firstChild).toBeNull();
    });
  });

  describe('TimelineVisualization', () => {
    const mockTimelineItems: TimelineItem[] = [
      {
        id: '1',
        event_id: 'event1',
        type: 'llm',
        timestamp_us: Date.now() * 1000,
        step_description: 'LLM interaction',
        duration_ms: 1000,
        details: {
          prompt: 'Test prompt',
          response: 'Test response',
          model_name: 'test-model'
        }
      },
      {
        id: '2',
        event_id: 'event2',
        type: 'mcp',
        timestamp_us: Date.now() * 1000,
        step_description: 'MCP call',
        duration_ms: 500,
        details: {
          tool_name: 'test-tool',
          parameters: { param: 'value' },
          result: { result: 'success' },
          server_name: 'test-server',
          execution_time_ms: 500
        }
      }
    ];

    it('renders timeline with items', () => {
      renderWithTheme(
        <TimelineVisualization timelineItems={mockTimelineItems} />
      );
      
      expect(screen.getByText('Processing Timeline')).toBeInTheDocument();
      expect(screen.getByText('LLM interaction')).toBeInTheDocument();
      expect(screen.getByText('MCP call')).toBeInTheDocument();
    });

    it('shows active indicator for active sessions', () => {
      renderWithTheme(
        <TimelineVisualization 
          timelineItems={mockTimelineItems} 
          isActive={true}
        />
      );
      
      expect(screen.getByText('Waiting for next interaction...')).toBeInTheDocument();
    });

    it('shows empty state when no items', () => {
      renderWithTheme(
        <TimelineVisualization timelineItems={[]} />
      );
      
      expect(screen.getByText('No timeline data available')).toBeInTheDocument();
    });

    it('shows timeline summary', () => {
      renderWithTheme(
        <TimelineVisualization timelineItems={mockTimelineItems} />
      );
      
      expect(screen.getByText(/Timeline shows 2 interactions in chronological order/)).toBeInTheDocument();
    });
  });
}); 