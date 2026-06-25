'use client';
import { useEffect, useRef, useState } from 'react';
import { getToken, WS_URL } from '@/lib/api';

export type ChatEvent = { type: string; request_id?: string; payload: any };

export function useChatSocket(roomId?: string) {
  const [events, setEvents] = useState<ChatEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token || !roomId) return;
    const ws = new WebSocket(`${WS_URL}?token=${encodeURIComponent(token)}`);
    socketRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'room.join', request_id: crypto.randomUUID(), payload: { room_id: roomId } }));
    };
    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data);
      setEvents((prev) => [...prev.slice(-300), event]);
      if (event.type === 'message.created') {
        ws.send(JSON.stringify({ type: 'message.delivered', payload: { room_id: event.payload.room_id, message_id: event.payload.id } }));
      }
    };
    ws.onclose = () => setConnected(false);
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'presence.heartbeat', request_id: crypto.randomUUID(), payload: {} }));
    }, 25000);
    return () => { clearInterval(heartbeat); ws.close(); };
  }, [roomId]);

  function send(content: string, parent_message_id?: string) {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || !roomId) return;
    ws.send(JSON.stringify({ type: parent_message_id ? 'thread.reply' : 'message.send', request_id: crypto.randomUUID(), payload: { room_id: roomId, content, parent_message_id, client_message_id: crypto.randomUUID() } }));
  }
  function typing(start: boolean) {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || !roomId) return;
    ws.send(JSON.stringify({ type: start ? 'typing.start' : 'typing.stop', payload: { room_id: roomId } }));
  }
  function markRead(messageId: string) {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || !roomId) return;
    ws.send(JSON.stringify({ type: 'message.read', payload: { room_id: roomId, message_id: messageId } }));
  }
  return { connected, events, send, typing, markRead };
}
