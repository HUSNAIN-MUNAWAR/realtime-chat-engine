import Link from 'next/link';

export default function LandingPage() {
  return <main className="min-h-screen overflow-hidden bg-slate-950 bg-[radial-gradient(circle_at_20%_10%,rgba(59,130,246,0.35),transparent_30%),radial-gradient(circle_at_80%_0%,rgba(16,185,129,0.18),transparent_35%)] px-6 py-10">
    <nav className="mx-auto flex max-w-6xl items-center justify-between"><div className="text-xl font-black">ChatEngine<span className="text-blue-400">100k</span></div><div className="space-x-3"><Link href="/login" className="btn-secondary">Login</Link><Link href="/register" className="btn">Register</Link></div></nav>
    <section className="mx-auto grid max-w-6xl gap-10 py-24 lg:grid-cols-2 lg:items-center">
      <div><span className="badge">FastAPI • WebSockets • Redis • PostgreSQL • MLOps</span><h1 className="mt-6 text-5xl font-black tracking-tight text-white md:text-7xl">Production-style real-time chat engine.</h1><p className="mt-6 text-lg leading-8 text-slate-300">A horizontally scalable WebSocket chat platform with durable message persistence, Redis fanout, online presence, read receipts, message risk scoring, Prometheus metrics, and a configurable 100k virtual-user load-test framework.</p><div className="mt-8 flex gap-3"><Link href="/register" className="btn">Open workspace</Link><a href="http://localhost:8000/docs" className="btn-secondary">API docs</a></div></div>
      <div className="card p-6 shadow-glow"><div className="grid gap-4 md:grid-cols-2">{['WebSocket gateway','Redis fanout','PostgreSQL store','JWT/RBAC','Risk scoring','Prometheus'].map((item) => <div key={item} className="rounded-2xl border border-white/10 bg-slate-900/70 p-5"><p className="font-semibold text-white">{item}</p><p className="mt-2 text-sm text-slate-400">Implemented as real backend code.</p></div>)}</div></div>
    </section>
  </main>;
}
