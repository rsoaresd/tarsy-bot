import React, { useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import {
  Box,
  Paper,
  Typography,
  Skeleton,
  useTheme,
  Alert,
} from '@mui/material';
import { SessionSummary, PaginationOptions } from '../types';
import HistoricalSessionCard from './HistoricalSessionCard';

interface VirtualizedSessionGridProps {
  sessions: SessionSummary[];
  onSessionClick: (session: SessionSummary) => void;
  loading?: boolean;
  error?: string | null;
  hasNextPage?: boolean;
  onLoadMore?: () => void;
  pagination: PaginationOptions;
  height?: number;
  itemHeight?: number;
}

interface ItemData {
  sessions: SessionSummary[];
  onSessionClick: (session: SessionSummary) => void;
  hasNextPage: boolean;
  loading: boolean;
  onLoadMore?: () => void;
}

// Memoized row component for optimal performance
const SessionRow = React.memo(({ index, style, data }: {
  index: number;
  style: React.CSSProperties;
  data: ItemData;
}) => {
  const { sessions, onSessionClick, hasNextPage, loading, onLoadMore } = data;
  
  // Handle loading indicator at the end
  if (index >= sessions.length) {
    if (loading) {
      return (
        <div style={style}>
          <Box sx={{ p: 2 }}>
            <Skeleton variant="rectangular" height={80} />
          </Box>
        </div>
      );
    }
    
    // Load more trigger
    if (hasNextPage && onLoadMore) {
      return (
        <div style={style}>
          <Box 
            sx={{ 
              p: 2, 
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
            onClick={onLoadMore}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onLoadMore();
              }
            }}
            aria-label="Load more sessions"
          >
            <Typography variant="body2" color="primary">
              Load More Sessions...
            </Typography>
          </Box>
        </div>
      );
    }
    
    return null;
  }

  const session = sessions[index];
  
  return (
    <div style={style}>
      <Box sx={{ p: 1 }}>
        <HistoricalSessionCard
          session={session}
          onClick={() => onSessionClick(session)}
        />
      </Box>
    </div>
  );
});

SessionRow.displayName = 'SessionRow';

function VirtualizedSessionGrid({
  sessions,
  onSessionClick,
  loading = false,
  error = null,
  hasNextPage = false,
  onLoadMore,
  pagination,
  height = 600,
  itemHeight = 100,
}: VirtualizedSessionGridProps) {
  const theme = useTheme();
  const listRef = useRef<List>(null);
  const [isScrolling, setIsScrolling] = useState(false);

  // Calculate total item count including loading placeholders
  const itemCount = useMemo(() => {
    let count = sessions.length;
    
    // Add slots for loading or load more
    if (loading) {
      count += 3; // Show 3 loading skeletons
    } else if (hasNextPage) {
      count += 1; // Show load more button
    }
    
    return count;
  }, [sessions.length, loading, hasNextPage]);

  // Memoized item data to prevent unnecessary re-renders
  const itemData = useMemo<ItemData>(() => ({
    sessions,
    onSessionClick,
    hasNextPage,
    loading,
    onLoadMore,
  }), [sessions, onSessionClick, hasNextPage, loading, onLoadMore]);

  // Handle infinite scrolling
  const handleItemsRendered = useCallback(({ visibleStopIndex }: {
    visibleStartIndex: number;
    visibleStopIndex: number;
  }) => {
    // Trigger load more when we're near the end
    if (
      hasNextPage && 
      !loading && 
      onLoadMore && 
      visibleStopIndex >= sessions.length - 5
    ) {
      onLoadMore();
    }
  }, [hasNextPage, loading, onLoadMore, sessions.length]);

  // Scroll to top when sessions change (e.g., new filter applied)
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollToItem(0, 'start');
    }
  }, [pagination.page, sessions.length]);

  // Handle scrolling state for performance optimization
  const handleScroll = useCallback(() => {
    if (!isScrolling) {
      setIsScrolling(true);
      // Reset scrolling state after scroll ends
      const timeoutId = setTimeout(() => setIsScrolling(false), 150);
      return () => clearTimeout(timeoutId);
    }
  }, [isScrolling]);

  if (error) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Paper>
    );
  }

  if (!loading && sessions.length === 0) {
    return (
      <Paper sx={{ p: 3, height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h3" color="text.secondary" gutterBottom>
            No Sessions Found
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Try adjusting your filters or search criteria.
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ height, overflow: 'hidden' }}>
      {/* Header with session count */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h3" gutterBottom>
          Session History
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {loading ? 'Loading...' : `${pagination.total.toLocaleString()} sessions found`}
          {isScrolling && (
            <Typography 
              component="span" 
              variant="caption" 
              sx={{ ml: 1, color: 'primary.main' }}
            >
              • Scrolling
            </Typography>
          )}
        </Typography>
      </Box>

      {/* Virtualized List */}
              <List
          ref={listRef}
          width="100%"
          height={height - 80} // Account for header
          itemCount={itemCount}
          itemSize={itemHeight}
          itemData={itemData}
          onItemsRendered={handleItemsRendered}
          onScroll={handleScroll}
          overscanCount={5} // Render 5 items outside visible area for smooth scrolling
          style={{
            // Optimize rendering during scroll
            willChange: isScrolling ? 'transform' : 'auto',
          }}
        >
          {SessionRow}
        </List>

      {/* Performance Stats (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            p: 1,
            borderRadius: 1,
            fontSize: '0.75rem',
            fontFamily: 'monospace',
          }}
        >
          Virtual: {itemCount} items • Height: {itemHeight}px • Overscan: 5
        </Box>
      )}
    </Paper>
  );
}

export default React.memo(VirtualizedSessionGrid); 