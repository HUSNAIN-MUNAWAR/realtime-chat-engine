'use client';
import { useEffect, useMemo, useState } from 'react';
import { api, getUser } from '@/lib/api';
import { useChatSocket } from '@/hooks/useChatSocket';
import { shortId } from '@/lib/utils';

type Room = { id: string; name: string; room_type: string; workspace_id: string };
type Message = { id: string; room_id: string; sender_username?: string; sender_id: string; content: string; risk_label: string; risk_score: number; created_at: string; parent_message_id?: string };

export default function ChatPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [activeRoom, setActiveRoom] = useState<Room | null>(null);
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [thread, setThread] = useState<Message | null>(null);
  const [reply, setReply] = useState('');
  const [users, setUsers] = useState<any[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const user = getUser();
  const { connected, events, send, typing, markRead } = useChatSocket(activeRoom?.id);

  useEffect(() => { api<Room[]>('/api/v1/rooms').then(r => { setRooms(r); setActiveRoom(r[0] || null); }); api<any[]>('/api/v1/users').then(setUsers).catch(()=>{}); }, []);
  useEffect(() => { if (activeRoom) api<{items: Message[]}>(`/api/v1/messages/${activeRoom.id}`).then(d => setHistory(d.items)); }, [activeRoom?.id]);

  const liveMessages = useMemo(() => events.filter(e => e.type === 'message.created').map(e => e.payload as Message), [events]);
  const messages = useMemo(() => [...history, ...liveMessages].filter((m, i, arr) => arr.findIndex(x => x.id === m.id) === i), [history, liveMessages]);
  useEffect(() => { const latest = liveMessages[liveMessages.length - 1]; if (latest) markRead(latest.id); }, [liveMessages.length]);
  useEffect(() => {
    const last = events[events.length - 1];
    if (last?.type === 'typing.start') setTypingUsers(prev => [...new Set([...prev, last.payload.username])].filter(Boolean));
    if (last?.type === 'typing.stop') setTypingUsers(prev => prev.filter(x => x !== last.payload.username));
  }, [events.length]);

  async function createRoom() {
    const ws = await api<any[]>('/api/v1/workspaces');
    const name = prompt('Room name?');
    if (!name || !ws[0]) return;
    const room = await api<Room>('/api/v1/rooms', { method: 'POST', body: JSON.stringify({ workspace_id: ws[0].id, name, room_type: 'channel' }) });
    setRooms([room, ...rooms]); setActiveRoom(room);
  }
  async function createDirect(otherUserId: string) {
    const ws = await api<any[]>('/api/v1/workspaces');
    const room = await api<Room>('/api/v1/rooms/direct', { method: 'POST', body: JSON.stringify({ workspace_id: ws[0].id, other_user_id: otherUserId }) });
    setRooms(prev => [room, ...prev.filter(r => r.id !== room.id)]); setActiveRoom(room);
  }
  function submit(e: React.FormEvent) { e.preventDefault(); if (!input.trim()) return; send(input); setInput(''); typing(false); }
  function submitReply(e: React.FormEvent) { e.preventDefault(); if (!reply.trim() || !thread) return; send(reply, thread.id); setReply(''); }

  return <div className="grid h-screen grid-cols-1 lg:grid-cols-[280px_1fr_320px]">
    <aside className="border-r border-white/10 bg-slate-950/50 p-5">
      <div className="flex items-center justify-between"><h2 className="font-bold">Rooms</h2><button onClick={createRoom} className="btn-secondary py-2">New</button></div>
      <div className="mt-4 space-y-2">{rooms.map(r => <button key={r.id} onClick={()=>setActiveRoom(r)} className={`w-full rounded-xl px-3 py-3 text-left text-sm ${activeRoom?.id===r.id?'bg-blue-500/20 text-blue-100':'hover:bg-white/[0.06]'}`}>#{r.name}<span className="ml-2 text-xs text-slate-500">{r.room_type}</span></button>)}</div>
      <h3 className="mt-8 font-bold">Direct messages</h3>
      <div className="mt-3 space-y-2">{users.filter(u=>u.id!==user?.id).slice(0,8).map(u => <button key={u.id} onClick={()=>createDirect(u.id)} className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-white/[0.06]">@{u.username}</button>)}</div>
    </aside>
    <section className="flex min-h-0 flex-col">
      <header className="flex items-center justify-between border-b border-white/10 p-5"><div><h1 className="text-xl font-black">{activeRoom ? `# ${activeRoom.name}` : 'Select room'}</h1><p className="text-sm text-slate-400">{connected ? 'WebSocket connected' : 'Connecting / disconnected'} • {activeRoom?.room_type}</p></div><span className="badge">{messages.length} loaded</span></header>
      <div className="flex-1 space-y-3 overflow-y-auto p-5">{messages.length === 0 && <div className="card p-8 text-center text-slate-400">No messages yet. Send the first real WebSocket message.</div>}{messages.map(m => <div key={m.id} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"><div className="flex items-center justify-between"><p className="text-sm font-semibold">{m.sender_username || shortId(m.sender_id)}</p><span className={`badge ${m.risk_label==='risky'?'border-red-400/30 text-red-200':''}`}>{m.risk_label} {Math.round((m.risk_score || 0)*100)}%</span></div><p className="mt-2 text-slate-100">{m.content}</p><div className="mt-3 flex gap-3 text-xs text-slate-500"><span>sent • delivered • read via WS receipts</span><button onClick={()=>setThread(m)} className="text-blue-300">Open thread</button></div></div>)}</div>
      {typingUsers.length > 0 && <p className="px-5 pb-2 text-xs text-slate-400">{typingUsers.join(', ')} typing...</p>}
      <form onSubmit={submit} className="border-t border-white/10 p-5"><div className="flex gap-3"><input className="input" placeholder="Send a real persisted WebSocket message..." value={input} onChange={e=>{setInput(e.target.value); typing(true);}} onBlur={()=>typing(false)}/><button className="btn">Send</button></div></form>
    </section>
    <aside className="border-l border-white/10 bg-slate-950/50 p-5"><h2 className="font-bold">Thread panel</h2>{thread ? <div className="mt-4"><div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"><p className="text-sm text-slate-400">Parent message</p><p className="mt-2">{thread.content}</p></div><div className="mt-4 space-y-2">{messages.filter(m=>m.parent_message_id===thread.id).map(m=><div key={m.id} className="rounded-xl bg-white/[0.04] p-3 text-sm">{m.content}</div>)}</div><form onSubmit={submitReply} className="mt-4 space-y-3"><input className="input" value={reply} onChange={e=>setReply(e.target.value)} placeholder="Reply in thread"/><button className="btn w-full">Reply</button></form></div> : <p className="mt-4 text-sm text-slate-400">Open a message thread from the chat feed.</p>}</aside>
  </div>;
}
