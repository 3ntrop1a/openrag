'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import {
  LayoutDashboard, FileText, Upload, Cpu,
  Trash2, CheckCircle2, XCircle, Loader2,
  ArrowLeft, RefreshCw, Database, Users, Shield, Eye, EyeOff
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const OLLAMA = 'http://localhost:11434';

type Tab = 'dashboard' | 'documents' | 'upload' | 'ollama' | 'users';

// ─── Types ────────────────────────────────────────────────────────────────────

interface HealthStatus {
  service: string;
  status: 'ok' | 'error' | 'loading';
  detail?: string;
}

interface Document {
  id: string;
  filename: string;
  status: string;
  collection_id: string;
  created_at?: string;
  chunk_count?: number;
}

interface Collection {
  name: string;
  vectors_count: number;
  status?: string;
}

interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (bytes: number) => {
  if (bytes > 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
  if (bytes > 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
  return (bytes / 1e3).toFixed(0) + ' KB';
};

const StatusDot = ({ status }: { status: 'ok' | 'error' | 'loading' }) => {
  if (status === 'loading') return <Loader2 className="h-4 w-4 animate-spin text-zinc-400" />;
  if (status === 'ok') return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  return <XCircle className="h-4 w-4 text-red-400" />;
};

// ─── Dashboard Tab ────────────────────────────────────────────────────────────

function DashboardTab() {
  const [health, setHealth] = useState<HealthStatus[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [docCount, setDocCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const services = [
    { label: 'API Gateway', url: `${API}/health` },
    { label: 'Qdrant', url: 'http://localhost:6333/healthz' },
    { label: 'Ollama', url: `${OLLAMA}/api/tags` },
    { label: 'MinIO', url: 'http://localhost:9000/minio/health/live' },
  ];

  const load = async () => {
    setLoading(true);
    setHealth(services.map(s => ({ service: s.label, status: 'loading' })));

    // Health checks
    const results = await Promise.all(
      services.map(async s => {
        try {
          const r = await fetch(s.url, { signal: AbortSignal.timeout(4000) });
          return { service: s.label, status: r.ok ? 'ok' : 'error', detail: `${r.status}` } as HealthStatus;
        } catch {
          return { service: s.label, status: 'error', detail: 'unreachable' } as HealthStatus;
        }
      })
    );
    setHealth(results);

    // Collections & doc count
    try {
      const [col, docs] = await Promise.all([
        fetch(`${API}/collections`).then(r => r.json()),
        fetch(`${API}/documents`).then(r => r.json()),
      ]);
      setCollections(col.collections ?? col ?? []);
      setDocCount((docs.documents ?? docs ?? []).length);
    } catch { /* ignore */ }

    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const totalVectors = collections.reduce((s, c) => s + (c.vectors_count ?? 0), 0);

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Documents', value: docCount ?? '—', icon: <FileText className="h-4 w-4" /> },
          { label: 'Vectors', value: totalVectors.toLocaleString(), icon: <Database className="h-4 w-4" /> },
          { label: 'Collections', value: collections.length, icon: <LayoutDashboard className="h-4 w-4" /> },
        ].map(s => (
          <Card key={s.label} className="p-4 bg-zinc-900 border-zinc-800">
            <div className="flex items-center gap-2 text-zinc-400 text-xs mb-2">
              {s.icon} {s.label}
            </div>
            <p className="text-2xl font-mono font-bold text-white">{s.value}</p>
          </Card>
        ))}
      </div>

      {/* Service health */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Services</h2>
          <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {health.map(h => (
            <Card key={h.service} className="p-3 bg-zinc-900 border-zinc-800 flex items-center gap-3">
              <StatusDot status={h.status} />
              <div>
                <p className="text-sm text-white font-medium">{h.service}</p>
                {h.detail && <p className="text-xs text-zinc-500">{h.detail}</p>}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Collections */}
      {collections.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest mb-3">Collections</h2>
          <div className="space-y-2">
            {collections.map((c: Collection) => (
              <Card key={c.name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center justify-between">
                <span className="text-sm text-white font-mono">{c.name}</span>
                <span className="text-xs text-zinc-400">{(c.vectors_count ?? 0).toLocaleString()} vectors</span>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Documents Tab ────────────────────────────────────────────────────────────

function DocumentsTab() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch(`${API}/documents`);
      const data = await r.json();
      setDocs(data.documents ?? data ?? []);
    } catch {
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const deleteDoc = async (id: string) => {
    if (!confirm('Delete this document and its vectors?')) return;
    setDeleting(id);
    try {
      await fetch(`${API}/documents/${id}`, { method: 'DELETE' });
      setDocs(prev => prev.filter(d => d.id !== id));
    } catch {
      setError('Delete failed');
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => { load(); }, []);

  const statusColor = (s: string) =>
    s === 'processed' ? 'text-emerald-400' :
    s === 'processing' ? 'text-yellow-400' :
    s === 'error' ? 'text-red-400' : 'text-zinc-400';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{docs.length} document{docs.length !== 1 ? 's' : ''}</p>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {loading && docs.length === 0 ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-zinc-400" /></div>
      ) : docs.length === 0 ? (
        <p className="text-center text-zinc-500 py-8">No documents yet. Upload some in the Upload tab.</p>
      ) : (
        <div className="space-y-2">
          {docs.map(doc => (
            <Card key={doc.id} className="p-3 bg-zinc-900 border-zinc-800 flex items-center gap-3">
              <FileText className="h-4 w-4 text-zinc-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white font-medium truncate">{doc.filename}</p>
                <div className="flex gap-3 mt-0.5">
                  <span className={`text-xs ${statusColor(doc.status)}`}>{doc.status}</span>
                  <span className="text-xs text-zinc-600">{doc.collection_id}</span>
                  {doc.chunk_count != null && (
                    <span className="text-xs text-zinc-600">{doc.chunk_count} chunks</span>
                  )}
                </div>
              </div>
              <Button
                variant="ghost" size="sm"
                className="h-7 w-7 p-0 text-zinc-600 hover:text-red-400"
                onClick={() => deleteDoc(doc.id)}
                disabled={deleting === doc.id}
              >
                {deleting === doc.id
                  ? <Loader2 className="h-3 w-3 animate-spin" />
                  : <Trash2 className="h-3 w-3" />}
              </Button>
            </Card>
          ))}
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
    setStatus('uploading');
    setMessage('');
    const form = new FormData();
    form.append('file', file);
    form.append('collection_id', collection);
    try {
      const r = await fetch(`${API}/documents/upload`, { method: 'POST', body: form });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail ?? 'Upload failed');
      setStatus('success');
      setMessage(`Uploaded successfully. Document ID: ${data.document_id ?? data.id ?? '—'}`);
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
            <div>
              <p className="text-white font-medium">{file.name}</p>
              <p className="text-xs text-zinc-500 mt-1">{fmt(file.size)}</p>
            </div>
          ) : (
            <div>
              <Upload className="h-6 w-6 text-zinc-600 mx-auto mb-2" />
              <p className="text-sm text-zinc-400">Click to select a file</p>
              <p className="text-xs text-zinc-600 mt-1">PDF, DOCX, TXT, MD</p>
            </div>
          )}
        </div>
        <input
          ref={fileRef} type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={e => setFile(e.target.files?.[0] ?? null)}
        />
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">Collection</label>
        <Input
          value={collection}
          onChange={e => setCollection(e.target.value)}
          placeholder="default"
          className="bg-zinc-900 border-zinc-800 text-white"
        />
      </div>

      <Button
        className="w-full bg-white text-black hover:bg-zinc-200 font-medium"
        disabled={!file || status === 'uploading'}
        onClick={upload}
      >
        {status === 'uploading' ? (
          <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Uploading…</>
        ) : (
          <><Upload className="h-4 w-4 mr-2" /> Upload & Embed</>
        )}
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

// ─── Users Tab ────────────────────────────────────────────────────────────────

interface UserRecord {
  id: string;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

function UsersTab() {
  const { auth } = useAuth();
  const token = auth?.token ?? '';

  const [users, setUsers] = useState<UserRecord[]>([]);
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

  const authHeader = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const load = async () => {
    setLoading(true); setError('');
    try {
      const r = await fetch(`${API}/auth/users`, { headers: authHeader });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setUsers(data.users ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load users');
    } finally { setLoading(false); }
  };

  const createUser = async () => {
    if (!newUsername || !newPassword) return;
    setCreating(true); setError('');
    try {
      const r = await fetch(`${API}/auth/users`, {
        method: 'POST',
        headers: authHeader,
        body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || 'Create failed');
      }
      setNewUsername(''); setNewPassword(''); setNewRole('user'); setShowForm(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed');
    } finally { setCreating(false); }
  };

  const deleteUser = async (id: string, username: string) => {
    if (!confirm(`Delete user "${username}"?`)) return;
    setDeleting(id);
    try {
      const r = await fetch(`${API}/auth/users/${id}`, { method: 'DELETE', headers: authHeader });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || 'Delete failed');
      }
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed');
    } finally { setDeleting(null); }
  };

  const changePassword = async (id: string) => {
    if (!newPwdFor || newPwdFor.length < 4) { setError('Password must be at least 4 characters'); return; }
    try {
      const r = await fetch(`${API}/auth/users/${id}/password`, {
        method: 'PATCH', headers: authHeader,
        body: JSON.stringify({ password: newPwdFor }),
      });
      if (!r.ok) throw new Error('Failed to update password');
      setChangingPwd(null); setNewPwdFor('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed');
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
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
            <Input
              placeholder="Username" value={newUsername}
              onChange={e => setNewUsername(e.target.value)}
              className="bg-zinc-800 border-zinc-700 text-white"
            />
            <div className="relative">
              <Input
                placeholder="Password" type={showPwd ? 'text' : 'password'}
                value={newPassword} onChange={e => setNewPassword(e.target.value)}
                className="bg-zinc-800 border-zinc-700 text-white pr-9"
              />
              <button
                type="button" onClick={() => setShowPwd(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white"
              >
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <label className="text-xs text-zinc-400 flex items-center gap-2 cursor-pointer">
              <input type="radio" name="create-role" value="user" checked={newRole === 'user'}
                onChange={() => setNewRole('user')} className="accent-white" />
              User (chat only)
            </label>
            <label className="text-xs text-zinc-400 flex items-center gap-2 cursor-pointer">
              <input type="radio" name="create-role" value="admin" checked={newRole === 'admin'}
                onChange={() => setNewRole('admin')} className="accent-white" />
              Admin (full access)
            </label>
          </div>
          <Button
            size="sm" className="bg-white text-black hover:bg-zinc-200"
            disabled={creating || !newUsername || !newPassword}
            onClick={createUser}
          >
            {creating ? <Loader2 className="h-3 w-3 mr-2 animate-spin" /> : null}
            Create
          </Button>
        </Card>
      )}

      {loading && users.length === 0 ? (
        <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-zinc-400" /></div>
      ) : (
        <div className="space-y-2">
          {users.map(u => (
            <Card key={u.id} className="p-3 bg-zinc-900 border-zinc-800">
              <div className="flex items-center gap-3">
                {u.role === 'admin'
                  ? <Shield className="h-4 w-4 text-amber-400 shrink-0" />
                  : <Users className="h-4 w-4 text-zinc-500 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-white font-medium font-mono">{u.username}</p>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      u.role === 'admin' ? 'bg-amber-950 text-amber-400' : 'bg-zinc-800 text-zinc-400'
                    }`}>{u.role}</span>
                    {!u.is_active && <span className="text-xs text-red-400">inactive</span>}
                  </div>
                  <p className="text-xs text-zinc-600 mt-0.5">
                    Created {new Date(u.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost" size="sm"
                    className="h-7 text-xs text-zinc-500 hover:text-white px-2"
                    onClick={() => { setChangingPwd(changingPwd === u.id ? null : u.id); setNewPwdFor(''); }}
                  >
                    Pwd
                  </Button>
                  <Button
                    variant="ghost" size="sm"
                    className="h-7 w-7 p-0 text-zinc-600 hover:text-red-400"
                    onClick={() => deleteUser(u.id, u.username)}
                    disabled={deleting === u.id || u.username === auth?.username}
                  >
                    {deleting === u.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
              {changingPwd === u.id && (
                <div className="mt-3 flex gap-2">
                  <Input
                    placeholder="New password" type="password" value={newPwdFor}
                    onChange={e => setNewPwdFor(e.target.value)}
                    className="h-7 text-xs bg-zinc-800 border-zinc-700 text-white flex-1"
                  />
                  <Button size="sm" className="h-7 text-xs bg-white text-black hover:bg-zinc-200"
                    onClick={() => changePassword(u.id)} disabled={newPwdFor.length < 4}>
                    Save
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Ollama Tab ───────────────────────────────────────────────────────────────

function OllamaTab() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [running, setRunning] = useState<OllamaModel[]>([]);
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [tagsRes, psRes, versionRes] = await Promise.allSettled([
        fetch(`${OLLAMA}/api/tags`).then(r => r.json()),
        fetch(`${OLLAMA}/api/ps`).then(r => r.json()),
        fetch(`${OLLAMA}/api/version`).then(r => r.json()),
      ]);
      if (tagsRes.status === 'fulfilled') setModels(tagsRes.value.models ?? []);
      if (psRes.status === 'fulfilled') setRunning(psRes.value.models ?? []);
      if (versionRes.status === 'fulfilled') setInfo(versionRes.value);
    } catch {
      setError('Could not reach Ollama');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Ollama</h2>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading} className="h-7 px-2 text-zinc-400 hover:text-white">
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {/* RAG config */}
      {info && (
        <div>
          <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-2">Ollama Version</h3>
          <Card className="p-4 bg-zinc-900 border-zinc-800">
            <pre className="text-xs text-zinc-300 font-mono whitespace-pre-wrap">
              {JSON.stringify(info, null, 2)}
            </pre>
          </Card>
        </div>
      )}

      {/* Running models */}
      <div>
        <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-2">
          Running{running.length > 0 ? ` (${running.length})` : ''}
        </h3>
        {running.length === 0 ? (
          <p className="text-sm text-zinc-600">No model currently loaded in memory.</p>
        ) : (
          <div className="space-y-2">
            {running.map(m => (
              <Card key={m.name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <div>
                  <p className="text-sm text-white font-mono">{m.name}</p>
                  <p className="text-xs text-zinc-500">{fmt(m.size)} in VRAM</p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Available models */}
      <div>
        <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-2">
          Installed models{models.length > 0 ? ` (${models.length})` : ''}
        </h3>
        {loading && models.length === 0 ? (
          <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-zinc-400" /></div>
        ) : models.length === 0 ? (
          <p className="text-sm text-zinc-600">No models installed. Run: <code className="text-zinc-300">ollama pull llama3.1:8b</code></p>
        ) : (
          <div className="space-y-2">
            {models.map(m => (
              <Card key={m.name} className="p-3 bg-zinc-900 border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Cpu className="h-4 w-4 text-zinc-500" />
                  <div>
                    <p className="text-sm text-white font-mono">{m.name}</p>
                    <p className="text-xs text-zinc-500">
                      {fmt(m.size)} · {new Date(m.modified_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                {running.some(r => r.name === m.name) && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    active
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Prometheus link */}
      <div className="pt-2 border-t border-zinc-800">
        <p className="text-xs text-zinc-500 mb-2">Monitoring</p>
        <div className="flex gap-3">
          <a href="http://localhost:9090" target="_blank" rel="noreferrer"
            className="text-xs text-zinc-400 hover:text-white underline underline-offset-4">
            Prometheus :9090
          </a>
          <a href="http://localhost:3002" target="_blank" rel="noreferrer"
            className="text-xs text-zinc-400 hover:text-white underline underline-offset-4">
            Grafana :3002
          </a>
        </div>
      </div>
    </div>
  );
}

// ─── Main Admin Page ──────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
  { id: 'documents', label: 'Documents', icon: <FileText className="h-4 w-4" /> },
  { id: 'upload', label: 'Upload', icon: <Upload className="h-4 w-4" /> },
  { id: 'ollama', label: 'Ollama', icon: <Cpu className="h-4 w-4" /> },
  { id: 'users', label: 'Users', icon: <Users className="h-4 w-4" /> },
];

export default function AdminPage() {
  const { auth, isAdmin } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('dashboard');

  // Redirect if not authenticated or not admin
  useEffect(() => {
    if (!auth) { router.replace('/login'); return; }
    if (!isAdmin()) { router.replace('/'); }
  }, [auth, router]);

  if (!auth || !isAdmin()) return null;

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
            <p className="text-xs text-zinc-600">OpenRAG</p>
          </div>
        </div>

        {/* Tab bar */}
        <div className="container mx-auto px-4">
          <div className="flex gap-1 -mb-px">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm border-b-2 transition-colors ${
                  tab === t.id
                    ? 'border-white text-white'
                    : 'border-transparent text-zinc-500 hover:text-zinc-300'
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-6 max-w-3xl">
        {tab === 'dashboard' && <DashboardTab />}
        {tab === 'documents' && <DocumentsTab />}
        {tab === 'upload' && <UploadTab />}
        {tab === 'ollama' && <OllamaTab />}
        {tab === 'users' && <UsersTab />}
      </main>
    </div>
  );
}
