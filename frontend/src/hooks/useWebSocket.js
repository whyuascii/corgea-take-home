import { useEffect, useRef, useState } from 'react';

const MAX_RETRIES = 10;
const BASE_DELAY_MS = 1000;
const MAX_DELAY_MS = 30000;

/**
 * Hook for WebSocket connections with exponential backoff reconnection.
 *
 * @param {string} path  WebSocket path (e.g. "/ws/projects/my-proj/scans/")
 * @param {object} opts  Options: { enabled, onMessage }
 * @returns {{ lastMessage, connected, retryCount }}
 */
export default function useWebSocket(path, opts = {}) {
  const { enabled = true, onMessage } = opts;
  const [lastMessage, setLastMessage] = useState(null);
  const [connected, setConnected] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const retryRef = useRef(0);
  // Use a ref for onMessage to avoid re-creating the WebSocket when the
  // callback identity changes (stale closure / reconnection loop fix).
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!enabled || !path) return;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;

      // Cookies are sent automatically on WebSocket handshake
      const url = `${protocol}//${host}${path}`;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryRef.current = 0;
        setRetryCount(0);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessageRef.current?.(data);
        } catch {
          setLastMessage(event.data);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;

        // Exponential backoff with jitter, capped at MAX_RETRIES
        if (retryRef.current < MAX_RETRIES) {
          const delay = Math.min(
            BASE_DELAY_MS * Math.pow(2, retryRef.current),
            MAX_DELAY_MS,
          );
          // Add ±25% jitter to prevent thundering herd
          const jitter = delay * (0.75 + Math.random() * 0.5);
          retryRef.current += 1;
          setRetryCount(retryRef.current);
          reconnectTimer.current = setTimeout(connect, jitter);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [path, enabled]);

  return { lastMessage, connected, retryCount };
}
