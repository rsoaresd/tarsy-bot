import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';

// Virtualization configuration
interface VirtualizationConfig {
  itemHeight: number;
  overscanCount?: number;
  threshold?: number; // Minimum items before virtualizing
  bufferSize?: number; // Buffer for smooth scrolling
}

// Virtualization state
interface VirtualizationState {
  isVirtualized: boolean;
  visibleStartIndex: number;
  visibleStopIndex: number;
  scrollOffset: number;
  scrolling: boolean;
}

// Hook for managing virtualization behavior
export function useVirtualization<T>(
  items: T[],
  config: VirtualizationConfig
) {
  const {
    itemHeight,
    overscanCount = 5,
    threshold = 50,
    bufferSize = 10,
  } = config;

  const [state, setState] = useState<VirtualizationState>({
    isVirtualized: items.length >= threshold,
    visibleStartIndex: 0,
    visibleStopIndex: Math.min(items.length - 1, overscanCount * 2),
    scrollOffset: 0,
    scrolling: false,
  });

  const listRef = useRef<List>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update virtualization when items change
  useEffect(() => {
    const shouldVirtualize = items.length >= threshold;
    
    setState(prev => ({
      ...prev,
      isVirtualized: shouldVirtualize,
      visibleStopIndex: shouldVirtualize 
        ? prev.visibleStopIndex 
        : items.length - 1,
    }));
  }, [items.length, threshold]);

  // Handle visible range changes
  const handleItemsRendered = useCallback(({
    visibleStartIndex,
    visibleStopIndex,
  }: {
    visibleStartIndex: number;
    visibleStopIndex: number;
  }) => {
    setState(prev => ({
      ...prev,
      visibleStartIndex,
      visibleStopIndex,
    }));
  }, []);

  // Handle scroll events
  const handleScroll = useCallback(({
    scrollOffset,
  }: {
    scrollOffset: number;
  }) => {
    setState(prev => ({
      ...prev,
      scrollOffset,
      scrolling: true,
    }));

    // Clear existing timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Set scrolling to false after scroll ends
    scrollTimeoutRef.current = setTimeout(() => {
      setState(prev => ({
        ...prev,
        scrolling: false,
      }));
    }, 150);
  }, []);

  // Scroll to specific item
  const scrollToItem = useCallback((index: number, align: 'start' | 'center' | 'end' | 'smart' = 'smart') => {
    if (listRef.current && state.isVirtualized) {
      listRef.current.scrollToItem(index, align);
    }
  }, [state.isVirtualized]);

  // Get currently visible items
  const visibleItems = useMemo(() => {
    if (!state.isVirtualized) {
      return items;
    }

    const start = Math.max(0, state.visibleStartIndex - bufferSize);
    const end = Math.min(items.length, state.visibleStopIndex + bufferSize + 1);
    
    return items.slice(start, end);
  }, [items, state.visibleStartIndex, state.visibleStopIndex, state.isVirtualized, bufferSize]);

  // Calculate estimated total height
  const estimatedTotalHeight = useMemo(() => {
    return items.length * itemHeight;
  }, [items.length, itemHeight]);

  // Performance metrics
  const metrics = useMemo(() => ({
    totalItems: items.length,
    visibleItems: state.visibleStopIndex - state.visibleStartIndex + 1,
    isVirtualized: state.isVirtualized,
    scrollOffset: state.scrollOffset,
    estimatedHeight: estimatedTotalHeight,
    memoryEfficiency: state.isVirtualized 
      ? (state.visibleStopIndex - state.visibleStartIndex + 1) / items.length
      : 1,
  }), [items.length, state, estimatedTotalHeight]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return {
    // State
    ...state,
    
    // Refs
    listRef,
    
    // Callbacks
    handleItemsRendered,
    handleScroll,
    scrollToItem,
    
    // Data
    visibleItems,
    estimatedTotalHeight,
    
    // Config
    itemHeight,
    overscanCount,
    
    // Performance
    metrics,
  };
}

// Hook for managing large dataset performance
export function useLargeDatasetOptimization<T>(
  data: T[],
  options: {
    chunkSize?: number;
    processingDelay?: number;
    maxConcurrent?: number;
  } = {}
) {
  const {
    chunkSize = 100,
    processingDelay = 16, // One frame at 60fps
    maxConcurrent = 3,
  } = options;

  const [processedData, setProcessedData] = useState<T[]>([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const processingRef = useRef(false);
  const abortRef = useRef(false);

  // Process data in chunks to avoid blocking UI
  const processDataChunks = useCallback(async (items: T[]) => {
    if (processingRef.current) return;
    
    processingRef.current = true;
    abortRef.current = false;
    setProcessing(true);
    setProgress(0);

    try {
      const chunks = [];
      for (let i = 0; i < items.length; i += chunkSize) {
        chunks.push(items.slice(i, i + chunkSize));
      }

      const results: T[] = [];
      
      for (let i = 0; i < chunks.length; i++) {
        if (abortRef.current) break;

        // Process chunk
        results.push(...chunks[i]);
        
        // Update progress
        setProgress((i + 1) / chunks.length);
        
        // Update UI with current results
        setProcessedData([...results]);
        
        // Yield to UI thread
        if (processingDelay > 0) {
          await new Promise(resolve => setTimeout(resolve, processingDelay));
        }
      }

      if (!abortRef.current) {
        setProcessedData(results);
        setProgress(1);
      }
    } finally {
      setProcessing(false);
      processingRef.current = false;
    }
  }, [chunkSize, processingDelay]);

  // Abort current processing
  const abortProcessing = useCallback(() => {
    abortRef.current = true;
  }, []);

  // Auto-process when data changes
  useEffect(() => {
    if (data.length > chunkSize) {
      processDataChunks(data);
    } else {
      setProcessedData(data);
      setProgress(1);
    }

    return () => {
      abortProcessing();
    };
  }, [data, processDataChunks, chunkSize, abortProcessing]);

  return {
    data: processedData,
    processing,
    progress,
    abortProcessing,
  };
}

// Hook for optimizing expensive computations
export function useComputationOptimization<T, R>(
  data: T,
  computeFn: (data: T) => R,
  dependencies: any[] = []
) {
  const [result, setResult] = useState<R | null>(null);
  const [computing, setComputing] = useState(false);
  
  const computationRef = useRef<{
    data: T;
    result: R;
  } | null>(null);
  
  const abortRef = useRef(false);

  // Memoized computation with cancellation
  const performComputation = useCallback(async (inputData: T) => {
    // Check if we already have the result cached
    if (computationRef.current && computationRef.current.data === inputData) {
      setResult(computationRef.current.result);
      return;
    }

    setComputing(true);
    abortRef.current = false;

    try {
      // Yield to UI thread before starting computation
      await new Promise(resolve => setTimeout(resolve, 0));
      
      if (abortRef.current) return;

      const computedResult = computeFn(inputData);
      
      if (!abortRef.current) {
        computationRef.current = { data: inputData, result: computedResult };
        setResult(computedResult);
      }
    } finally {
      setComputing(false);
    }
  }, [computeFn]);

  // Trigger computation when dependencies change
  useEffect(() => {
    performComputation(data);

    return () => {
      abortRef.current = true;
    };
  }, [data, performComputation, ...dependencies]);

  return {
    result,
    computing,
  };
}

// Hook for managing memory usage
export function useMemoryMonitoring() {
  const [memoryInfo, setMemoryInfo] = useState<{
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
    usage: number;
  } | null>(null);

  useEffect(() => {
    const updateMemoryInfo = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        setMemoryInfo({
          usedJSHeapSize: Math.round(memory.usedJSHeapSize / 1024 / 1024), // MB
          totalJSHeapSize: Math.round(memory.totalJSHeapSize / 1024 / 1024), // MB
          jsHeapSizeLimit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024), // MB
          usage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
        });
      }
    };

    updateMemoryInfo();
    
    const interval = setInterval(updateMemoryInfo, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return memoryInfo;
} 