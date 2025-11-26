import { useEffect, useRef, useCallback, useState } from 'react';

export interface UseAutoRefreshOptions {
  interval?: number;
  enabled?: boolean;
  onRefresh?: () => void | Promise<void>;
  immediate?: boolean;
}

export function useAutoRefresh(options: UseAutoRefreshOptions = {}) {
  const {
    interval = 30000,
    enabled = true,
    onRefresh,
    immediate = false,
  } = options;

  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const refreshCallbackRef = useRef(onRefresh);

  // Keep callback ref updated
  useEffect(() => {
    refreshCallbackRef.current = onRefresh;
  }, [onRefresh]);

  const refresh = useCallback(async () => {
    if (isRefreshing) return;

    setIsRefreshing(true);
    try {
      await refreshCallbackRef.current?.();
      setLastRefresh(new Date());
    } finally {
      setIsRefreshing(false);
    }
  }, [isRefreshing]);

  const scheduleRefresh = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (enabled && interval > 0) {
      timeoutRef.current = setTimeout(() => {
        refresh().then(scheduleRefresh);
      }, interval);
    }
  }, [enabled, interval, refresh]);

  // Setup auto-refresh
  useEffect(() => {
    if (enabled) {
      if (immediate) {
        refresh().then(scheduleRefresh);
      } else {
        scheduleRefresh();
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, scheduleRefresh, immediate, refresh]);

  // Pause/Resume
  const pause = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const resume = useCallback(() => {
    scheduleRefresh();
  }, [scheduleRefresh]);

  return {
    lastRefresh,
    isRefreshing,
    refresh,
    pause,
    resume,
    enabled,
  };
}

// Hook for polling data with auto-refresh
export function usePolling<T>(
  fetcher: () => Promise<T>,
  options: UseAutoRefreshOptions & {
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  } = {}
) {
  const { onSuccess, onError, ...refreshOptions } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const handleRefresh = useCallback(async () => {
    try {
      const result = await fetcher();
      setData(result);
      setError(null);
      onSuccess?.(result);
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
    }
  }, [fetcher, onSuccess, onError]);

  const autoRefresh = useAutoRefresh({
    ...refreshOptions,
    onRefresh: handleRefresh,
    immediate: true,
  });

  return {
    data,
    error,
    ...autoRefresh,
  };
}

export default useAutoRefresh;
