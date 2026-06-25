'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function MLOpsPage() {
  const [model, setModel] = useState<any>(null);
  const [text, setText] = useState('urgent money scam send password now');
  const [prediction, setPrediction] = useState<any>(null);
  useEffect(() => { api<any>('/api/v1/mlops/model').then(setModel).catch(console.error); }, []);
  async function score() { setPrediction(await api<any>('/api/v1/mlops/risk-score', { method: 'POST', body: JSON.stringify({ text }) })); }
  return <div className="p-8"><h1 className="text-3xl font-black">MLOps dashboard</h1><p className="mt-2 text-slate-400">Real model artifact, model metadata, inference endpoint, and persisted message risk scores.</p><div className="card mt-8 p-6"><h2 className="font-bold">Current model</h2><pre className="mt-4 overflow-x-auto rounded-xl bg-slate-900 p-4 text-xs">{JSON.stringify(model, null, 2)}</pre></div><div className="card mt-6 p-6"><h2 className="font-bold">Live inference test</h2><textarea className="input mt-4 min-h-28" value={text} onChange={e=>setText(e.target.value)} /><button onClick={score} className="btn mt-4">Score text</button>{prediction && <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-900 p-4 text-xs">{JSON.stringify(prediction, null, 2)}</pre>}</div></div>;
}
