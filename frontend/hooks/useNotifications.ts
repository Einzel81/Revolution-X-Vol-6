"use client";

import { useState, useEffect, useCallback } from "react";
import { useWebSocket } from "./useWebSocket";

interface Notification {
  id: string;
  type: "trade" | "price" | "system" | "ai";
  title: string;
  message: string;
  priority: "low" | "medium" | "high";
  read: boolean;
  timestamp: string;
  data?: Record<string, any>;
}

interface NotificationPreferences {
  enabled: boolean;
  sound: boolean;
  desktop: boolean;
  filters: {
    trades: boolean;
    prices: boolean;
    system: boolean;
    ai: boolean;
  };
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    enabled: true,
    sound: true,
    desktop: false,
    filters: {
      trades: true,
      prices: true,
      system: true,
      ai: true,
    },
  });
  const { lastMessage } = useWebSocket();

  // Request notification permission
  useEffect(() => {
    if ("Notification" in window && preferences.desktop) {
      Notification.requestPermission();
    }
  }, [preferences.desktop]);

  // Handle incoming notifications
  useEffect(() => {
    if (!lastMessage) return;

    const data = JSON.parse(lastMessage);
    if (data.type === "notification" && preferences.enabled) {
      const notification: Notification = {
        id: Math.random().toString(36).substring(2, 9),
        ...data.payload,
        read: false,
        timestamp: new Date().toISOString(),
      };

      // Check filters
      if (!preferences.filters[notification.type]) return;

      setNotifications((prev) => [notification, ...prev]);

      // Show desktop notification
      if (preferences.desktop && "Notification" in window) {
        new Notification(notification.title, {
          body: notification.message,
          icon: "/icon.png",
        });
      }

      // Play sound
      if (preferences.sound) {
        const audio = new Audio("/notification.mp3");
        audio.play().catch(() => {});
      }
    }
  }, [lastMessage, preferences]);

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const updatePreferences = useCallback((newPrefs: Partial<NotificationPreferences>) => {
    setPreferences((prev) => ({ ...prev, ...newPrefs }));
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return {
    notifications,
    unreadCount,
    preferences,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAll,
    updatePreferences,
  };
}
