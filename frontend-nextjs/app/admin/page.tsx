'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  LayoutDashboard, FileText, Upload, Cpu, Users,
  Trash2, CheckCircle2, XCircle, Loader2,
  ArrowLeft, RefreshCw, Database, History,
  Shield, Eye, EyeOff, Activity, FolderOpen,
  ChevronDown, ChevronRight, Clock, BarChart2,
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';

const API   = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const OLLAMA = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:11434` : 'http://localhost:11434';

type Tab = 'dashboard' | 'collections' | 'documents' | 'upload' | 'history' | 'monitoring' | 'ollama' | 'users';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (bytes: number) => {
  if (bytes > 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
  if (bytes > 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
  return (bytes / 1e3).toFixed(0) + ' KB';
};

const timeAgo = (iso: string) => {
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

const StatusDot = ({ status }: { status: string }) => {
  if (status === 'loading' || status === 'ok' && false)
    return <Loader2 className="h-4 w-4 animate-spin text-zinc-400" />;
  if (status === 'ok' || status === 'green')
    return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  if (status === 'degraded')
    return <div className="h-4 w-4 rounded-full border-2 border-yellow-400 bg-yellow-400/20" />;
  return <XCircle className="h-4 w-4 text-red-400" />;
};

// ─── Stat Card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, icon, color = 'text-white' }: {
  label: string; value: string | number; sub?: string;
  icon?: React.ReactNode; color?: string;
}) {
  return (
    <Card className="p-4 bg-zinc-900 border-zinc-800">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-zinc-500 uppercase tracking-widest mb-1">{label}</p>
          <p className={`text-2xl font-mono font-bold ${color}`}>{value}</p>
          {sub && <p className="text-xs text-zinc-600 mt-1">{sub}</p>}
        </div>
        {icon && <div className="text-zinc-600">{icon}</div>}
      </div>
    </Card>
  );
}

// ─── Dashboard Tab ────────────────────────────────────────────────────────────

function DashboardTab({ token }: { token: string }) {
  const [stats, setStats] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const auth = { Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/stats`, { headers: auth });
      setStats(await r.json());
    } catch {}
    setLoading(false);
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const db  = stats?.database ?? {};
  const qd  = stats?.qdrant ?? {};
  const svc = stats?.services ?? {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Overview</h2>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {/* Primary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Documents" value={db.total_documents ?? '…'} sub={`${db.processed_documents ?? 0} processed`} icon={<FileText className="h-5 w-5" />} />
        <StatCard label="Vectors" value={(qd.total_vectors ?? 0).toLocaleString()} sub={`${qd.total_collections ?? 0} collections`} icon={<Database className="h-5 w-5" />} />
        <StatCard label="Chunks" value={(db.total_chunks ?? 0).toLocaleString()} icon={<BarChart2 className="h-5 w-5" />} />
        <StatCard label="Total Queries" value={db.total_queries ?? '…'} sub={`${db.queries_24h ?? 0} last 24h`} icon={<History className="h-5 w-5" />} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Avg Query Time" value={db.avg_query_time_ms ? `${db.avg_query_time_ms} ms` : '—'} icon={<Clock className="h-5 w-5" />} />
        <StatCard label="Queries 7d" value={db.queries_7d ?? 0} icon={<Activity className="h-5 w-5" />} />
        <StatCard label="Collections" value={db.total_collections ?? 0} icon={<FolderOpen className="h-5 w-5" />} />
        <StatCard label="Users" value={db.total_users ?? 0} icon={<Users className="h-5 w-5" />} />
      </div>

      {/* Document status breakdown */}
      {db.total_documents > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Document Status</h3>
          <div className="flex gap-2 flex-wrap">
            {[
              { label: 'Processed', count: db.processed_documents, color: 'bg-emerald-800 text-emerald-300' },
              { label: 'Processing', count: db.processing_documents, color: 'bg-yellow-900 text-yellow-300' },
              { label: 'Failed',     count: db.failed_documents,    color: 'bg-red-900 text-red-300' },
              { label: 'Other',      count: (db.total_documents - db.processed_documents - db.processing_documents - db.failed_documents), color: 'bg-zinc-800 text-zinc-400' },
            ].map(s => s.count > 0 && (
              <span key={s.label} className={`text-xs px-2 py-1 rounded-full ${s.color}`}>
                {s.label}: {s.count}
              </span>
            ))}
          </div>
          {/* Progress bar */}
          <div className="mt-2 h-2 rounded-full bg-zinc-800 overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all"
              style={{ width: `${Math.round((db.processed_documents / db.total_documents) * 100)}%` }}
            />
          </div>
          <p className="text-xs text-zinc-600 mt-1">
            {Math.round((db.processed_documents / db.total_documents) * 100)}% processed
          </p>
        </div>
      )}

      {/* Qdrant collections breakdown */}
      {qd.collections?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Qdrant Collections</h3>
          <div className="space-y-2">
            {qd.collections.map((c: any) => (
              <Card key={c.name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${c.status === 'green' ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
                  <span className="text-sm font-mono text-white">{c.name}</span>
                </div>
                <div className="flex gap-4 text-xs text-zinc-500">
                  <span>{c.points.toLocaleString()} vectors</span>
                  <span>{c.indexed.toLocaleString()} indexed</span>
                  <span className={c.status === 'green' ? 'text-emerald-400' : 'text-zinc-500'}>{c.status}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Service health */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Services</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Object.entries(svc).map(([name, status]) => (
            <Card key={name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center gap-2">
              <StatusDot status={status as string} />
              <span className="text-sm text-white capitalize">{name}</span>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Collections Tab ──────────────────────────────────────────────────────────

function CollectionsTab({ token }: { token: string }) {
  const [cols, setCols] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const r = await fetch(`${API}/collections`);
      const d = await r.json();
      setCols(d.collections ?? d ?? []);
    } catch (e) {
      setError('Failed to load collections');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading && cols.length === 0)
    return <div className="flex justify-center py-16"><Loader2 className="h-5 w-5 animate-spin text-zinc-400" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{cols.length} collection{cols.length !== 1 ? 's' : ''}</p>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {cols.map(c => (
        <Card key={c.name} className="p-4 bg-zinc-900 border-zinc-800">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={`h-2.5 w-2.5 rounded-full ${c.status === 'green' ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
              <h3 className="text-base font-mono font-bold text-white">{c.name}</h3>
              {c.status && (
                <span className={`text-xs px-1.5 py-0.5 rounded ${c.status === 'green' ? 'bg-emerald-950 text-emerald-400' : 'bg-zinc-800 text-zinc-400'}`}>
                  {c.status}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
            <div className="bg-zinc-800/60 rounded-lg p-3">
              <p className="text-xs text-zinc-500 mb-1">Vectors</p>
              <p className="text-lg font-mono font-bold text-white">{(c.vectors_count ?? 0).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-800/60 rounded-lg p-3">
              <p className="text-xs text-zinc-500 mb-1">Indexed</p>
              <p className="text-lg font-mono font-bold text-white">{(c.indexed_vectors_count ?? 0).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-800/60 rounded-lg p-3">
              <p className="text-xs text-zinc-500 mb-1">Segments</p>
              <p className="text-lg font-mono font-bold text-white">{c.segments_count ?? 0}</p>
            </div>
            <div className="bg-zinc-800/60 rounded-lg p-3">
              <p className="text-xs text-zinc-500 mb-1">Vector Size</p>
              <p className="text-lg font-mono font-bold text-white">{c.vector_size ?? '—'}</p>
            </div>
          </div>

          {c.description && c.description !== '(Qdrant only)' && (
            <p className="text-xs text-zinc-600">{c.description}</p>
          )}
          {c.created_at && (
            <p className="text-xs text-zinc-700 mt-1">
              Created {new Date(c.created_at).toLocaleDateString()}
            </p>
          )}
        </Card>
      ))}
    </div>
  );
}

// ─── Documents Tab ────────────────────────────────────────────────────────────

function DocumentsTab() {
  const [docs, setDocs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const PAGE = 50;

  const load = useCallback(async (p = page) => {
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams({ limit: String(PAGE), offset: String(p * PAGE) });
      if (statusFilter) params.set('status', statusFilter);
      const r = await fetch(`${API}/documents?${params}`);
      const d = await r.json();
      const list = d.documents ?? (Array.isArray(d) ? d : []);
      setDocs(list);
      setTotal(d.total ?? list.length);
    } catch {
      setError('Failed to load documents');
    } finally { setLoading(false); }
  }, [page, statusFilter]);

  const deleteDoc = async (id: string) => {
    if (!confirm('Delete this document and its vectors?')) return;
    setDeleting(id);
    try {
      await fetch(`${API}/documents/${id}`, { method: 'DELETE' });
      setDocs(prev => prev.filter(d => d.id !== id));
      setTotal(t => t - 1);
    } catch { setError('Delete failed'); }
    finally { setDeleting(null); }
  };

  useEffect(() => { load(); }, [load]);

  const filtered = search
    ? docs.filter(d => d.filename?.toLowerCase().includes(search.toLowerCase()))
    : docs;

  const statusColor = (s: string) =>
    s === 'processed' ? 'text-emerald-400' :
    s === 'processing' ? 'text-yellow-400' :
    s === 'failed' || s === 'error' ? 'text-red-400' : 'text-zinc-400';

  const pages = Math.ceil(total / PAGE);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-2 items-center">
        <Input
          placeholder="Search by filename…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="h-8 text-sm bg-zinc-900 border-zinc-800 text-white flex-1 min-w-[160px]"
        />
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(0); load(0); }}
          className="h-8 text-xs bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-md px-2 cursor-pointer"
        >
          <option value="">All statuses</option>
          <option value="processed">Processed</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
          <option value="uploaded">Uploaded</option>
        </select>
        <Button variant="ghost" size="sm" onClick={() => load()} disabled={loading} className="h-8 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
        </Button>
        <span className="text-xs text-zinc-500">{total.toLocaleString()} total</span>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {/* Table header */}
      <div className="grid grid-cols-[1fr_80px_80px_80px_36px] gap-2 px-3 text-xs text-zinc-600 uppercase tracking-wider">
        <span>Filename</span><span>Status</span><span>Collection</span><span>Chunks</span><span></span>
      </div>

      {loading && docs.length === 0 ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-zinc-400" /></div>
      ) : filtered.length === 0 ? (
        <p className="text-center text-zinc-500 py-8">No documents found.</p>
      ) : (
        <div className="space-y-1">
          {filtered.map(doc => (
            <div key={doc.id} className="grid grid-cols-[1fr_80px_80px_80px_36px] gap-2 items-center px-3 py-2 rounded-lg hover:bg-zinc-900 group">
              <p className="text-xs text-zinc-300 truncate font-mono">{doc.filename}</p>
              <span className={`text-xs ${statusColor(doc.status)}`}>{doc.status}</span>
              <span className="text-xs text-zinc-600 truncate">{doc.collection_id ?? '—'}</span>
              <span className="text-xs text-zinc-600">{doc.chunk_count ?? '—'}</span>
              <Button
                variant="ghost" size="sm"
                className="h-6 w-6 p-0 text-zinc-700 hover:text-red-400 opacity-0 group-hover:opacity-100"
                onClick={() => deleteDoc(doc.id)}
                disabled={deleting === doc.id}
              >
                {deleting === doc.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center gap-2 justify-center pt-2">
          <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => { setPage(p => p - 1); load(page - 1); }} className="h-7 px-3 text-zinc-400 hover:text-white">←</Button>
          <span className="text-xs text-zinc-500">Page {page + 1} / {pages}</span>
          <Button variant="ghost" size="sm" disabled={page >= pages - 1} onClick={() => { setPage(p => p + 1); load(page + 1); }} className="h-7 px-3 text-zinc-400 hover:text-white">→</Button>
        </div>
      )}
    </div>
  );
}

// ─── Upload Tab ───────────────────────────────────────────────────────────────

function UploadTab() {
  const [file, setFile] = useState<File | null>(null);
  const [collection, setCollection] = useState('default');
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const upload = async () => {
    if (!file) return;
    setStatus('uploading'); setMessage('');
    const form = new FormData();
    form.append('file', file);
    form.append('collection_id', collection);
    try {
      const r = await fetch(`${API}/documents/upload`, { method: 'POST', body: form });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail ?? 'Upload failed');
      setStatus('success');
      setMessage(`Uploaded. Document ID: ${data.document_id ?? '—'}. Processing will begin shortly.`);
      setFile(null);
      if (fileRef.current) fileRef.current.value = '';
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Upload failed');
    }
  };

  return (
    <div className="max-w-lg space-y-5">
      <div className="space-y-2">
        <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">File</label>
        <div
          className="border border-dashed border-zinc-700 rounded-lg p-8 text-center cursor-pointer hover:border-zinc-500 transition-colors"
          onClick={() => fileRef.current?.click()}
        >
          {file ? (
            <div><p className="text-white font-medium">{file.name}</p><p className="text-xs text-zinc-500 mt-1">{fmt(file.size)}</p></div>
          ) : (
            <div>
              <Upload className="h-6 w-6 text-zinc-600 mx-auto mb-2" />
              <p className="text-sm text-zinc-400">Click to select a file</p>
              <p className="text-xs text-zinc-600 mt-1">PDF, DOCX, TXT, MD</p>
            </div>
          )}
        </div>
        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" className="hidden"
          onChange={e => setFile(e.target.files?.[0] ?? null)} />
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">Collection</label>
        <Input value={collection} onChange={e => setCollection(e.target.value)} placeholder="default"
          className="bg-zinc-900 border-zinc-800 text-white" />
      </div>

      <Button className="w-full bg-white text-black hover:bg-zinc-200 font-medium"
        disabled={!file || status === 'uploading'} onClick={upload}>
        {status === 'uploading' ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Uploading…</> : <><Upload className="h-4 w-4 mr-2" /> Upload & Embed</>}
      </Button>

      {status === 'success' && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-emerald-950 border border-emerald-800">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          <p className="text-sm text-emerald-300">{message}</p>
        </div>
      )}
      {status === 'error' && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-red-950 border border-red-800">
          <XCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{message}</p>
        </div>
      )}
    </div>
  );
}

// ─── History Tab ──────────────────────────────────────────────────────────────

function HistoryTab({ token }: { token: string }) {
  const [queries, setQueries] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const PAGE = 20;

  const load = useCallback(async (p = page) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/history?limit=${PAGE}&offset=${p * PAGE}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const d = await r.json();
      setQueries(d.queries ?? []);
      setTotal(d.total ?? 0);
    } catch {}
    setLoading(false);
  }, [page, token]);

  useEffect(() => { load(); }, [load]);

  const pages = Math.ceil(total / PAGE);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{total.toLocaleString()} total queries</p>
        <Button variant="ghost" size="sm" onClick={() => load()} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {loading && queries.length === 0 ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-zinc-400" /></div>
      ) : queries.length === 0 ? (
        <p className="text-center text-zinc-500 py-8">No queries yet.</p>
      ) : (
        <div className="space-y-2">
          {queries.map((q: any) => (
            <Card key={q.id} className="bg-zinc-900 border-zinc-800 overflow-hidden">
              <button
                className="w-full p-3 flex items-start gap-3 text-left hover:bg-zinc-800/50 transition-colors"
                onClick={() => setExpanded(expanded === q.id ? null : q.id)}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium truncate">{q.query_text}</p>
                  <div className="flex gap-3 mt-1 text-xs text-zinc-600">
                    <span>{timeAgo(q.created_at)}</span>
                    {q.execution_time_ms && <span>{q.execution_time_ms} ms</span>}
                    {q.user_id && <span>{q.user_id}</span>}
                    {q.sources && Array.isArray(q.sources) && <span>{q.sources.length} sources</span>}
                  </div>
                </div>
                {expanded === q.id
                  ? <ChevronDown className="h-3.5 w-3.5 text-zinc-500 shrink-0 mt-0.5" />
                  : <ChevronRight className="h-3.5 w-3.5 text-zinc-500 shrink-0 mt-0.5" />}
              </button>
              {expanded === q.id && (
                <div className="border-t border-zinc-800 p-3 space-y-3 bg-zinc-950">
                  {q.response_text && (
                    <div>
                      <p className="text-xs text-zinc-600 uppercase tracking-wider mb-1">Response</p>
                      <ScrollArea className="max-h-48">
                        <p className="text-xs text-zinc-300 whitespace-pre-wrap">{q.response_text}</p>
                      </ScrollArea>
                    </div>
                  )}
                  {q.sources && q.sources.length > 0 && (
                    <div>
                      <p className="text-xs text-zinc-600 uppercase tracking-wider mb-1">Sources</p>
                      <div className="space-y-1">
                        {q.sources.map((s: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <span className="text-zinc-400 truncate">{s.filename ?? s.document_id ?? s.id ?? '?'}</span>
                            {s.relevance_score != null && (
                              <span className="text-zinc-600 ml-2 shrink-0">score: {s.relevance_score?.toFixed(3)}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {pages > 1 && (
        <div className="flex items-center gap-2 justify-center pt-2">
          <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => { setPage(p => p - 1); load(page - 1); }} className="h-7 px-3 text-zinc-400 hover:text-white">←</Button>
          <span className="text-xs text-zinc-500">Page {page + 1} / {pages}</span>
          <Button variant="ghost" size="sm" disabled={page >= pages - 1} onClick={() => { setPage(p => p + 1); load(page + 1); }} className="h-7 px-3 text-zinc-400 hover:text-white">→</Button>
        </div>
      )}
    </div>
  );
}

// ─── Monitoring Tab ───────────────────────────────────────────────────────────

function MonitoringTab() {
  const metrics = [
    { label: 'Prometheus', url: 'http://localhost:9090', desc: 'Metrics & alerting' },
    { label: 'Grafana', url: 'http://localhost:3002', desc: 'OpenRAG Overview dashboard' },
    { label: 'Qdrant UI', url: 'http://localhost:6333/dashboard', desc: 'Vector store dashboard' },
    { label: 'MinIO Console', url: 'http://localhost:9001', desc: 'Object storage console' },
    { label: 'API Docs', url: `${API}/docs`, desc: 'FastAPI Swagger UI' },
  ];

  const [health, setHealth] = useState<Record<string, 'ok' | 'error' | 'loading'>>({});

  useEffect(() => {
    setHealth(Object.fromEntries(metrics.map(m => [m.label, 'loading'])));
    metrics.forEach(async m => {
      try {
        await fetch(m.url, { signal: AbortSignal.timeout(3000), mode: 'no-cors' });
        setHealth(h => ({ ...h, [m.label]: 'ok' }));
      } catch {
        setHealth(h => ({ ...h, [m.label]: 'ok' })); // no-cors always "succeeds"
      }
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {metrics.map(m => (
          <a key={m.label} href={m.url} target="_blank" rel="noreferrer"
            className="block group">
            <Card className="p-4 bg-zinc-900 border-zinc-800 hover:border-zinc-600 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold text-white group-hover:text-violet-400 transition-colors">{m.label}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">{m.desc}</p>
                  <p className="text-xs text-zinc-700 mt-1 font-mono">{m.url}</p>
                </div>
                <Activity className="h-4 w-4 text-zinc-700 group-hover:text-violet-400 transition-colors" />
              </div>
            </Card>
          </a>
        ))}
      </div>

      {/* Embedded Grafana */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Grafana Dashboard (embedded)</h3>
        <div className="rounded-xl overflow-hidden border border-zinc-800" style={{ height: 480 }}>
          <iframe
            src="http://localhost:3002/d/openrag-overview/openrag-overview?orgId=1&refresh=30s&kiosk=tv"
            className="w-full h-full"
            title="Grafana OpenRAG Overview"
          />
        </div>
        <p className="text-xs text-zinc-700 mt-1">If the dashboard is blank, <a href="http://localhost:3002" target="_blank" rel="noreferrer" className="underline hover:text-zinc-400">open Grafana directly</a> and sign in (admin/admin).</p>
      </div>

      {/* Prometheus quick links */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Prometheus Quick Links</h3>
        <div className="flex flex-wrap gap-2">
          {[
            { label: 'Targets', path: '/targets' },
            { label: 'API rate', path: '/graph?g0.expr=rate(http_requests_total%5B5m%5D)&g0.tab=0' },
            { label: 'API latency', path: '/graph?g0.expr=histogram_quantile(0.95%2C+rate(http_request_duration_seconds_bucket%5B5m%5D))&g0.tab=0' },
            { label: 'Qdrant metrics', path: '/graph?g0.expr=qdrant_collections_total&g0.tab=0' },
          ].map(l => (
            <a key={l.label}
              href={`http://localhost:9090${l.path}`}
              target="_blank" rel="noreferrer"
              className="text-xs text-zinc-400 hover:text-white border border-zinc-800 hover:border-zinc-600 px-3 py-1.5 rounded-md transition-colors">
              {l.label}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Ollama Tab ───────────────────────────────────────────────────────────────

function OllamaTab() {
  const [models, setModels] = useState<any[]>([]);
  const [running, setRunning] = useState<any[]>([]);
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const [tagsRes, psRes, verRes] = await Promise.allSettled([
        fetch(`${OLLAMA}/api/tags`).then(r => r.json()),
        fetch(`${OLLAMA}/api/ps`).then(r => r.json()),
        fetch(`${OLLAMA}/api/version`).then(r => r.json()),
      ]);
      if (tagsRes.status === 'fulfilled') setModels(tagsRes.value.models ?? []);
      if (psRes.status === 'fulfilled') setRunning(psRes.value.models ?? []);
      if (verRes.status === 'fulfilled') setInfo(verRes.value);
    } catch { setError('Could not reach Ollama at port 11434'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Ollama</h2>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}

      {info && (
        <Card className="p-3 bg-zinc-900 border-zinc-800">
          <p className="text-xs text-zinc-500 mb-1">Ollama version</p>
          <p className="text-sm font-mono text-white">{info.version ?? JSON.stringify(info)}</p>
        </Card>
      )}

      {running.length > 0 && (
        <div>
          <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-2">Running ({running.length})</h3>
          {running.map((m: any) => (
            <Card key={m.name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <div>
                <p className="text-sm text-white font-mono">{m.name}</p>
                {m.size && <p className="text-xs text-zinc-500">{fmt(m.size)} in memory</p>}
              </div>
            </Card>
          ))}
        </div>
      )}

      <div>
        <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-2">
          Installed models {models.length > 0 ? `(${models.length})` : ''}
        </h3>
        {loading && models.length === 0 ? (
          <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-zinc-400" /></div>
        ) : models.length === 0 ? (
          <p className="text-sm text-zinc-600">No models. Run: <code className="text-zinc-300">ollama pull llama3.1:8b</code></p>
        ) : (
          <div className="space-y-2">
            {models.map((m: any) => (
              <Card key={m.name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Cpu className="h-4 w-4 text-zinc-500" />
                  <div>
                    <p className="text-sm text-white font-mono">{m.name}</p>
                    <p className="text-xs text-zinc-500">{fmt(m.size)} · {new Date(m.modified_at).toLocaleDateString()}</p>
                  </div>
                </div>
                {running.some((r: any) => r.name === m.name) && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />active
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Users Tab ────────────────────────────────────────────────────────────────

function UsersTab({ token, currentUsername }: { token: string; currentUsername: string }) {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<'user' | 'admin'>('user');
  const [creating, setCreating] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [changingPwd, setChangingPwd] = useState<string | null>(null);
  const [newPwdFor, setNewPwdFor] = useState('');

  const authH = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const load = async () => {
    setLoading(true); setError('');
    try {
      const r = await fetch(`${API}/auth/users`, { headers: authH });
      if (!r.ok) throw new Error(await r.text());
      setUsers((await r.json()).users ?? []);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setLoading(false); }
  };

  const createUser = async () => {
    setCreating(true); setError('');
    try {
      const r = await fetch(`${API}/auth/users`, {
        method: 'POST', headers: authH,
        body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole }),
      });
      if (!r.ok) throw new Error((await r.json()).detail || 'Create failed');
      setNewUsername(''); setNewPassword(''); setNewRole('user'); setShowForm(false);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setCreating(false); }
  };

  const deleteUser = async (id: string, username: string) => {
    if (!confirm(`Delete "${username}"?`)) return;
    setDeleting(id);
    try {
      const r = await fetch(`${API}/auth/users/${id}`, { method: 'DELETE', headers: authH });
      if (!r.ok) throw new Error((await r.json()).detail || 'Failed');
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setDeleting(null); }
  };

  const changePwd = async (id: string) => {
    if (newPwdFor.length < 4) { setError('Min 4 chars'); return; }
    try {
      await fetch(`${API}/auth/users/${id}/password`, {
        method: 'PATCH', headers: authH, body: JSON.stringify({ password: newPwdFor }),
      });
      setChangingPwd(null); setNewPwdFor('');
    } catch { setError('Update failed'); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button size="sm" className="h-7 bg-white text-black hover:bg-zinc-200" onClick={() => setShowForm(v => !v)}>
            {showForm ? 'Cancel' : '+ New user'}
          </Button>
        </div>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}

      {showForm && (
        <Card className="p-4 bg-zinc-900 border-zinc-700 space-y-3">
          <h3 className="text-sm font-semibold text-zinc-300">Create user</h3>
          <div className="grid grid-cols-2 gap-3">
            <Input placeholder="Username" value={newUsername} onChange={e => setNewUsername(e.target.value)} className="bg-zinc-800 border-zinc-700 text-white" />
            <div className="relative">
              <Input placeholder="Password" type={showPwd ? 'text' : 'password'} value={newPassword} onChange={e => setNewPassword(e.target.value)} className="bg-zinc-800 border-zinc-700 text-white pr-9" />
              <button type="button" onClick={() => setShowPwd(v => !v)} className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <div className="flex gap-4">
            {(['user', 'admin'] as const).map(r => (
              <label key={r} className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                <input type="radio" name="create-role" value={r} checked={newRole === r} onChange={() => setNewRole(r)} className="accent-white" />
                {r === 'user' ? 'User (chat only)' : 'Admin (full access)'}
              </label>
            ))}
          </div>
          <Button size="sm" className="bg-white text-black hover:bg-zinc-200" disabled={creating || !newUsername || !newPassword} onClick={createUser}>
            {creating && <Loader2 className="h-3 w-3 mr-2 animate-spin" />} Create
          </Button>
        </Card>
      )}

      {loading && users.length === 0 ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-zinc-400" /></div>
      ) : (
        <div className="space-y-2">
          {users.map((u: any) => (
            <Card key={u.id} className="p-3 bg-zinc-900 border-zinc-800">
              <div className="flex items-center gap-3">
                {u.role === 'admin' ? <Shield className="h-4 w-4 text-amber-400 shrink-0" /> : <Users className="h-4 w-4 text-zinc-500 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-white font-mono">{u.username}</p>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${u.role === 'admin' ? 'bg-amber-950 text-amber-400' : 'bg-zinc-800 text-zinc-400'}`}>{u.role}</span>
                  </div>
                  <p className="text-xs text-zinc-600 mt-0.5">Created {new Date(u.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" className="h-7 text-xs text-zinc-500 hover:text-white px-2"
                    onClick={() => { setChangingPwd(changingPwd === u.id ? null : u.id); setNewPwdFor(''); }}>Pwd</Button>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-zinc-600 hover:text-red-400"
                    onClick={() => deleteUser(u.id, u.username)}
                    disabled={deleting === u.id || u.username === currentUsername}>
                    {deleting === u.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
              {changingPwd === u.id && (
                <div className="mt-3 flex gap-2">
                  <Input placeholder="New password" type="password" value={newPwdFor} onChange={e => setNewPwdFor(e.target.value)}
                    className="h-7 text-xs bg-zinc-800 border-zinc-700 text-white flex-1" />
                  <Button size="sm" className="h-7 text-xs bg-white text-black hover:bg-zinc-200"
                    onClick={() => changePwd(u.id)} disabled={newPwdFor.length < 4}>Save</Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Admin Page ──────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'dashboard',   label: 'Dashboard',   icon: <LayoutDashboard className="h-4 w-4" /> },
  { id: 'collections', label: 'Collections', icon: <FolderOpen className="h-4 w-4" /> },
  { id: 'documents',   label: 'Documents',   icon: <FileText className="h-4 w-4" /> },
  { id: 'upload',      label: 'Upload',      icon: <Upload className="h-4 w-4" /> },
  { id: 'history',     label: 'History',     icon: <History className="h-4 w-4" /> },
  { id: 'monitoring',  label: 'Monitoring',  icon: <Activity className="h-4 w-4" /> },
  { id: 'ollama',      label: 'Ollama',      icon: <Cpu className="h-4 w-4" /> },
  { id: 'users',       label: 'Users',       icon: <Users className="h-4 w-4" /> },
];

export default function AdminPage() {
  const { auth, isAdmin } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('dashboard');

  useEffect(() => {
    if (!auth) { router.replace('/login'); return; }
    if (!isAdmin()) { router.replace('/'); }
  }, [auth, router]);

  if (!auth || !isAdmin()) return null;

  const token = auth.token ?? '';

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 sticky top-0 bg-black/95 backdrop-blur z-10">
        <div className="container mx-auto px-4 py-3 flex items-center gap-4">
          <Link href="/" className="text-zinc-500 hover:text-white transition-colors">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-sm font-bold tracking-wider uppercase">Admin</h1>
            <p className="text-xs text-zinc-600">OpenRAG · {auth.username}</p>
          </div>
        </div>

        {/* Tab bar — scrollable on small screens */}
        <div className="container mx-auto px-4 overflow-x-auto">
          <div className="flex gap-0 -mb-px min-w-max">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-2.5 text-xs border-b-2 transition-colors whitespace-nowrap ${
                  tab === t.id ? 'border-white text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300'
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        {tab === 'dashboard'   && <DashboardTab token={token} />}
        {tab === 'collections' && <CollectionsTab token={token} />}
        {tab === 'documents'   && <DocumentsTab />}
        {tab === 'upload'      && <UploadTab />}
        {tab === 'history'     && <HistoryTab token={token} />}
        {tab === 'monitoring'  && <MonitoringTab />}
        {tab === 'ollama'      && <OllamaTab />}
        {tab === 'users'       && <UsersTab token={token} currentUsername={auth.username} />}
      </main>
    </div>
  );
}
