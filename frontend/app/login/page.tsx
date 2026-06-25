'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_URL, setAuth } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('Admin12345!');
  const [error, setError] = useState('');
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError('');
    const res = await fetch(`${API_URL}/api/v1/auth/login`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email,password}) });
    if (!res.ok) { setError(await res.text()); return; }
    const data = await res.json(); setAuth(data.access_token, data.user); router.push('/app');
  }
  return <main className="flex min-h-screen items-center justify-center px-6"><form onSubmit={submit} className="card w-full max-w-md p-8"><h1 className="text-3xl font-black">Login</h1><p className="mt-2 text-sm text-slate-400">Demo admin is pre-filled for local Docker startup.</p><div className="mt-6 space-y-4"><input className="input" value={email} onChange={e=>setEmail(e.target.value)} /><input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} /><button className="btn w-full">Login</button></div>{error && <p className="mt-4 rounded-xl bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}<p className="mt-6 text-sm text-slate-400">No account? <Link className="text-blue-300" href="/register">Register</Link></p></form></main>;
}
