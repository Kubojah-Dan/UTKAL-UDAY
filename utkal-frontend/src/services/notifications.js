const SEEN_NOTIFICATIONS_KEY = "utkal_seen_notifications";

export function getSeenNotifications() {
  try {
    const raw = localStorage.getItem(SEEN_NOTIFICATIONS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? new Set(parsed.map((item) => String(item))) : new Set();
  } catch {
    return new Set();
  }
}

export function markNotificationsSeen(ids = []) {
  const seen = getSeenNotifications();
  ids.forEach((id) => {
    if (id) seen.add(String(id));
  });

  const compact = Array.from(seen).slice(-200);
  localStorage.setItem(SEEN_NOTIFICATIONS_KEY, JSON.stringify(compact));
}

export function showBrowserNotification(notification) {
  if (typeof window === "undefined" || !("Notification" in window)) return;
  if (Notification.permission !== "granted") return;

  const title = notification?.title || "New update";
  const body = notification?.message || "";
  const browserNotification = new Notification(title, { body });
  browserNotification.onclick = () => {
    window.focus();
    if (notification?.action_path?.startsWith("/")) {
      window.location.assign(notification.action_path);
    }
    browserNotification.close();
  };
}
