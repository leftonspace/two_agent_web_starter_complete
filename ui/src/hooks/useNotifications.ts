import { useState, useCallback, useRef } from 'react';

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  dismissible?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface UseNotificationsOptions {
  maxNotifications?: number;
  defaultDuration?: number;
}

let notificationId = 0;

export function useNotifications(options: UseNotificationsOptions = {}) {
  const { maxNotifications = 5, defaultDuration = 5000 } = options;
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const dismiss = useCallback((id: string) => {
    const timeout = timeoutsRef.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      timeoutsRef.current.delete(id);
    }
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const add = useCallback(
    (notification: Omit<Notification, 'id'>) => {
      const id = `notification-${++notificationId}`;
      const newNotification: Notification = {
        ...notification,
        id,
        dismissible: notification.dismissible ?? true,
        duration: notification.duration ?? defaultDuration,
      };

      setNotifications((prev) => {
        const updated = [newNotification, ...prev];
        // Limit max notifications
        if (updated.length > maxNotifications) {
          const removed = updated.slice(maxNotifications);
          removed.forEach((n) => {
            const timeout = timeoutsRef.current.get(n.id);
            if (timeout) {
              clearTimeout(timeout);
              timeoutsRef.current.delete(n.id);
            }
          });
          return updated.slice(0, maxNotifications);
        }
        return updated;
      });

      // Auto-dismiss
      if (newNotification.duration && newNotification.duration > 0) {
        const timeout = setTimeout(() => {
          dismiss(id);
        }, newNotification.duration);
        timeoutsRef.current.set(id, timeout);
      }

      return id;
    },
    [dismiss, maxNotifications, defaultDuration]
  );

  const info = useCallback(
    (title: string, message?: string) => add({ type: 'info', title, message }),
    [add]
  );

  const success = useCallback(
    (title: string, message?: string) => add({ type: 'success', title, message }),
    [add]
  );

  const warning = useCallback(
    (title: string, message?: string) => add({ type: 'warning', title, message }),
    [add]
  );

  const error = useCallback(
    (title: string, message?: string) =>
      add({ type: 'error', title, message, duration: 8000 }),
    [add]
  );

  const clearAll = useCallback(() => {
    timeoutsRef.current.forEach((timeout) => clearTimeout(timeout));
    timeoutsRef.current.clear();
    setNotifications([]);
  }, []);

  return {
    notifications,
    add,
    dismiss,
    info,
    success,
    warning,
    error,
    clearAll,
  };
}

// Notification context for app-wide notifications
import { createContext, useContext, ReactNode } from 'react';

interface NotificationContextValue extends ReturnType<typeof useNotifications> {}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const notifications = useNotifications();

  return (
    <NotificationContext.Provider value={notifications}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotificationContext() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotificationContext must be used within NotificationProvider');
  }
  return context;
}

export default useNotifications;
