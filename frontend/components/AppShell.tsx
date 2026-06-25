'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const nav = [['Chat','/app'],['Admin','/app/admin'],['Load Tests','/app/load-tests'],['Observability','/app/observability'],['MLOps','/app/mlops']];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.25),transparent_30%),radial-gradient(circle_at_top_right,rgba(16,185,129,0.12),transparent_30%)]">
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-slate-950/80 p-6 backdrop-blur lg:block">
      <Link href="/" className="text-lg font-black tracking-tight">ChatEngine<span className="text-blue-400">100k</span></Link>
      <nav className="mt-8 space-y-2">{nav.map(([label,href]) => <Link key={href} href={href} className={cn('block rounded-xl px-4 py-3 text-sm text-slate-300 hover:bg-white/[0.06]', path === href && 'bg-blue-500/20 text-blue-100 ring-1 ring-blue-400/20')}>{label}</Link>)}</nav>
      <div className="absolute bottom-6 left-6 right-6 rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-xs text-slate-400">WebSocket gateway + Redis fanout + PostgreSQL persistence.</div>
    </aside>
    <section className="lg:pl-64">{children}</section>
  </main>;
}
