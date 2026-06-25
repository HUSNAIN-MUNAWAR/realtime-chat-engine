'use client';
import { useEffect, useState } from 'react';
import { MetricCard } from '@/components/MetricCard';
import { api } from '@/lib/api';

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [risky, setRisky] = useState<any[]>([]);
  useEffect(() => {
    const load = () => { api<any>('/api/v1/admin/stats').then(setStats).catch(console.error); api<any[]>('/api/v1/admin/risky-messages').then(setRisky).catch(console.error); };
    load(); const id=setInterval(load,5000); return()=>clearInterval(id);
  }, []);
  return <div className="p-8"><h1 className="text-3xl font-black">Admin dashboard</h1><p className="mt-2 text-slate-400">Live backend stats and persisted risky-message review queue.</p><div className="mt-8 grid gap-4 md:grid-cols-4"><MetricCard label="Users" value={stats?.users ?? '-'} /><MetricCard label="Rooms" value={stats?.rooms ?? '-'} /><MetricCard label="Messages" value={stats?.total_messages ?? '-'} /><MetricCard label="Active WS local" value={stats?.active_connections_local ?? '-'} /></div><h2 className="mt-10 text-xl font-bold">Risk review queue</h2><div className="mt-4 space-y-3">{risky.length===0 && <div className="card p-6 text-slate-400">No risky messages stored yet.</div>}{risky.map(m => <div key={m.id} className="card p-4"><div className="flex justify-between text-sm"><span>{m.risk_label}</span><span>{Math.round(m.risk_score*100)}%</span></div><p className="mt-2">{m.content}</p><p className="mt-2 text-xs text-slate-500">room {m.room_id}</p></div>)}</div></div>;
}
