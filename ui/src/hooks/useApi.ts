import { useState, useCallback, useRef, useEffect } from 'react';

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export interface UseApiOptions<T> {
  initialData?: T | null;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  cacheKey?: string;
  cacheDuration?: number;
}

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();

export function useApi<T>(
  fetcher: () => Promise<T>,
  options: UseApiOptions<T> = {}
) {
  const {
    initialData = null,
    onSuccess,
    onError,
    cacheKey,
    cacheDuration = 30000, // 30 seconds default
  } = options;

  const [state, setState] = useState<UseApiState<T>>({
    data: initialData,
    loading: false,
    error: null,
  });

  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(async () => {
    // Check cache first
    if (cacheKey) {
      const cached = cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < cacheDuration) {
        setState({ data: cached.data as T, loading: false, error: null });
        return cached.data as T;
      }
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const data = await fetcher();

      if (mountedRef.current) {
        setState({ data, loading: false, error: null });

        // Update cache
        if (cacheKey) {
          cache.set(cacheKey, { data, timestamp: Date.now() });
        }

        onSuccess?.(data);
      }

      return data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));

      if (mountedRef.current) {
        setState((prev) => ({ ...prev, loading: false, error }));
        onError?.(error);
      }

      throw error;
    }
  }, [fetcher, cacheKey, cacheDuration, onSuccess, onError]);

  const reset = useCallback(() => {
    setState({ data: initialData, loading: false, error: null });
    if (cacheKey) {
      cache.delete(cacheKey);
    }
  }, [initialData, cacheKey]);

  const setData = useCallback((data: T | ((prev: T | null) => T)) => {
    setState((prev) => ({
      ...prev,
      data: typeof data === 'function' ? (data as (prev: T | null) => T)(prev.data) : data,
    }));
  }, []);

  return {
    ...state,
    execute,
    reset,
    setData,
    refetch: execute,
  };
}

export function useApiOnMount<T>(
  fetcher: () => Promise<T>,
  options: UseApiOptions<T> = {}
) {
  const api = useApi(fetcher, options);
  const initialFetchRef = useRef(false);

  useEffect(() => {
    if (!initialFetchRef.current) {
      initialFetchRef.current = true;
      api.execute().catch(() => {
        // Error handled in state
      });
    }
  }, []);

  return api;
}

export function useMutation<TData, TVariables = void>(
  mutator: (variables: TVariables) => Promise<TData>,
  options: {
    onSuccess?: (data: TData) => void;
    onError?: (error: Error) => void;
  } = {}
) {
  const [state, setState] = useState<UseApiState<TData>>({
    data: null,
    loading: false,
    error: null,
  });

  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const mutate = useCallback(
    async (variables: TVariables) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const data = await mutator(variables);

        if (mountedRef.current) {
          setState({ data, loading: false, error: null });
          options.onSuccess?.(data);
        }

        return data;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));

        if (mountedRef.current) {
          setState((prev) => ({ ...prev, loading: false, error }));
          options.onError?.(error);
        }

        throw error;
      }
    },
    [mutator, options]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    mutate,
    reset,
  };
}

// Clear entire cache
export function clearApiCache() {
  cache.clear();
}

// Clear specific cache entry
export function clearCacheEntry(key: string) {
  cache.delete(key);
}

export default useApi;
