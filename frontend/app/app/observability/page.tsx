'use client';
import { useEffect, useState } from 'react';
import { MetricCard } from '@/components/MetricCard';
import { api } from '@/lib/api';

export default function ObservabilityPage() {
  const [stats, setStats] = useState<any>(null);
  useEffect(() => { const load=()=>api<any>('/api/v1/admin/stats').then(setStats).catch(console.error); load(); const id=setInterval(load,5000); return()=>clearInterval(id); }, []);
  return <div className="p-8"><h1 className="text-3xl font-black">Observability</h1><p className="mt-2 text-slate-400">Real metrics are exposed at backend /metrics and scraped by Prometheus. Grafana runs at localhost:3001.</p><div className="mt-8 grid gap-4 md:grid-cols-4"><MetricCard label="Process RSS" value={`${stats?.system?.process_rss_mb ?? '-'} MB`} /><MetricCard label="System memory" value={`${stats?.system?.system_memory_percent ?? '-'}%`} /><MetricCard label="Active rooms local" value={stats?.active_rooms_local ?? '-'} /><MetricCard label="Risky messages" value={stats?.risky_messages ?? '-'} /></div><div className="card mt-8 p-6"><h2 className="font-bold">Prometheus queries included</h2><pre className="mt-4 overflow-x-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-300">{`chat_ws_active_connections\nrate(chat_messages_sent_total[1m])\nhistogram_quantile(0.95, rate(chat_message_processing_seconds_bucket[5m]))\nrate(chat_ml_predictions_total[1m])`}</pre></div></div>;
}
