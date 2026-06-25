'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_URL, setAuth } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: '', username: '', password: '' });
  const [error, setError] = useState('');
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError('');
    const res = await fetch(`${API_URL}/api/v1/auth/register`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(form) });
    if (!res.ok) { setError(await res.text()); return; }
    const data = await res.json(); setAuth(data.access_token, data.user); router.push('/app');
  }
  return <main className="flex min-h-screen items-center justify-center px-6"><form onSubmit={submit} className="card w-full max-w-md p-8"><h1 className="text-3xl font-black">Create account</h1><div className="mt-6 space-y-4"><input className="input" placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/><input className="input" placeholder="Username" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/><input className="input" placeholder="Password" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/><button className="btn w-full">Register</button></div>{error && <p className="mt-4 rounded-xl bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}<p className="mt-6 text-sm text-slate-400">Already have account? <Link className="text-blue-300" href="/login">Login</Link></p></form></main>;
}
