"""The phone client: one page served by the API at ``/``.

Chats, the tools waiting for approval, Mission Control's approvals and the
latest tasks, in the UI language.  The texts are filled in when the page is
served, so the page itself stays plain HTML with no build step.  It can be
added to the phone's home screen (``/manifest.webmanifest``).
"""

from __future__ import annotations

import json

from arqen.ui import strings
from arqen.ui.strings import status_label, tr

# English source text by key; tr() gives the Swedish.
_TEXTS = {
    "chats": "Chats",
    "approvals": "Approvals",
    "tasks": "Tasks",
    "newChat": "New chat",
    "connect": "Connect",
    "connectHelp": "Scan the QR code under Settings → Mobile in Arqen on your computer, or paste the token from there.",
    "token": "Token",
    "badToken": "The token was not accepted. Scan the QR code again.",
    "offline": "Arqen cannot be reached. Is it running on your computer?",
    "placeholder": "Message Arqen…",
    "send": "Send",
    "thinking": "Arqen is thinking…",
    "wantsToRun": "Arqen wants to run {tool}",
    "approve": "Approve",
    "reject": "Reject",
    "approved": "Approved",
    "rejected": "Rejected",
    "nothingWaiting": "Nothing is waiting for you.",
    "noChats": "No chats yet. Start one below.",
    "noTasks": "No tasks yet.",
    "back": "Back",
    "result": "Result",
    "error": "Error",
    "signOut": "Sign out",
    "failed": "Something went wrong: {error}",
    "you": "YOU",
    "task": "Task",
}
_STATUSES = ("queued", "running", "completed", "failed", "cancelled", "waiting_approval", "pending")


def _texts() -> dict[str, str]:
    texts = {key: tr(value) for key, value in _TEXTS.items()}
    texts["status"] = {status: status_label(status) for status in _STATUSES}
    return texts


def manifest() -> dict:
    return {
        "name": "Arqen",
        "short_name": "Arqen",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#101214",
        "theme_color": "#101214",
        "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}],
    }


ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="112" fill="#101214"/>
<circle cx="256" cy="256" r="150" fill="none" stroke="#b7ff18" stroke-width="22"/>
<path d="M256 118 A138 138 0 0 1 394 256" fill="none" stroke="#e8ffb0" stroke-width="22" stroke-linecap="round"/>
<text x="256" y="292" font-family="Arial, sans-serif" font-size="112" font-weight="700" fill="#b7ff18" text-anchor="middle">A</text>
</svg>"""


def mobile_page() -> str:
    # "</" cannot appear inside the inline script.
    data = json.dumps(_texts(), ensure_ascii=False).replace("</", "<\\/")
    return _PAGE.replace("__LANG__", strings.LANGUAGE).replace("__TEXTS__", data)


_PAGE = r"""<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#101214">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon.svg">
<title>Arqen</title>
<style>
:root {
  --bg: #101214; --surface: #171a1c; --surface-2: #1e2225; --border: #2c3236;
  --ink: #eef1eb; --ink-dim: #a7b0aa; --ink-faint: #737c77;
  --accent: #b7ff18; --accent-ink: #101214; --warn: #ffd166; --bad: #ff6b6b;
  --mono: ui-monospace, "Cascadia Mono", "SF Mono", Consolas, monospace;
}
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body { height: 100%; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
button, input, textarea { font: inherit; color: inherit; }
button { cursor: pointer; }
.app { display: flex; flex-direction: column; height: 100dvh; max-width: 760px; margin: 0 auto; }
header { display: flex; align-items: center; gap: 10px; padding: calc(12px + env(safe-area-inset-top)) 16px 10px; border-bottom: 1px solid var(--border); }
.brand { font-family: var(--mono); font-weight: 700; letter-spacing: .14em; color: var(--accent); }
.chip { font-family: var(--mono); font-size: 11px; color: var(--ink-dim); border: 1px solid var(--border); border-radius: 99px; padding: 2px 9px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 45vw; }
.chip:empty { display: none; }
.spacer { flex: 1; }
.icon-btn { background: none; border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px; color: var(--ink-dim); font-size: 13px; }
main { flex: 1; overflow-y: auto; padding: 14px 16px; -webkit-overflow-scrolling: touch; }
nav.tabs { display: flex; border-top: 1px solid var(--border); padding-bottom: env(safe-area-inset-bottom); background: var(--bg); }
nav.tabs button { flex: 1; background: none; border: 0; padding: 12px 4px 13px; color: var(--ink-faint); font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; position: relative; }
nav.tabs button.active { color: var(--accent); }
.badge { display: inline-block; min-width: 18px; margin-left: 5px; padding: 0 5px; border-radius: 99px; background: var(--warn); color: #111; font-size: 11px; line-height: 18px; }
.list { display: grid; gap: 10px; }
.row { display: block; width: 100%; text-align: left; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 13px 14px; }
.row .title { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row .meta { font-family: var(--mono); font-size: 12px; color: var(--ink-faint); margin-top: 3px; }
.empty { color: var(--ink-faint); text-align: center; padding: 40px 12px; }
.primary { background: var(--accent); color: var(--accent-ink); border: 0; border-radius: 10px; padding: 12px 18px; font-weight: 700; }
.ghost { background: none; color: var(--ink); border: 1px solid var(--border); border-radius: 10px; padding: 12px 18px; font-weight: 600; }
.bubble { max-width: 88%; padding: 10px 13px; border-radius: 14px; white-space: pre-wrap; overflow-wrap: anywhere; margin-bottom: 10px; }
.bubble.user { margin-left: auto; background: var(--surface-2); border: 1px solid var(--border); border-bottom-right-radius: 4px; }
.bubble.arqen { background: var(--surface); border: 1px solid var(--border); border-bottom-left-radius: 4px; }
.bubble.arqen code { font-family: var(--mono); font-size: 13px; background: var(--surface-2); padding: 1px 5px; border-radius: 5px; }
.bubble.thinking { color: var(--ink-faint); font-style: italic; }
.card { background: var(--surface); border: 1px solid var(--warn); border-radius: 12px; padding: 13px 14px; margin-bottom: 10px; }
.card .what { font-weight: 600; margin-bottom: 6px; }
.card pre { margin: 0 0 12px; max-height: 180px; overflow: auto; font-family: var(--mono); font-size: 12px; color: var(--ink-dim); white-space: pre-wrap; overflow-wrap: anywhere; }
.card .actions { display: flex; gap: 10px; }
.card .actions button { flex: 1; }
.card.done { border-color: var(--border); opacity: .75; }
.composer { display: flex; gap: 8px; padding: 10px 12px; border-top: 1px solid var(--border); background: var(--bg); }
.composer textarea { flex: 1; resize: none; min-height: 44px; max-height: 140px; padding: 11px 12px; border-radius: 12px; border: 1px solid var(--border); background: var(--surface); }
.composer textarea:focus, .connect input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.composer .primary { padding: 0 16px; }
.chat-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.chat-head .title { font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.connect { display: grid; gap: 14px; padding-top: 12vh; text-align: center; }
.connect h1 { margin: 0; font-family: var(--mono); letter-spacing: .2em; color: var(--accent); }
.connect p { margin: 0; color: var(--ink-dim); }
.connect input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface); }
.error { color: var(--bad); }
.status { font-family: var(--mono); font-size: 11px; letter-spacing: .05em; }
.status.completed { color: var(--accent); } .status.failed, .status.cancelled { color: var(--bad); }
.status.waiting_approval, .status.pending { color: var(--warn); } .status.running, .status.queued { color: var(--ink-dim); }
.detail { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px; white-space: pre-wrap; overflow-wrap: anywhere; }
[hidden] { display: none !important; }
</style>
</head>
<body>
<div class="app">
  <header>
    <span class="brand">ARQEN</span><span class="chip" id="model"></span>
    <span class="spacer"></span>
    <button class="icon-btn" id="signout" hidden></button>
  </header>
  <main id="view"></main>
  <div class="composer" id="composer" hidden>
    <textarea id="input" rows="1"></textarea>
    <button class="primary" id="send"></button>
  </div>
  <nav class="tabs" id="tabs" hidden>
    <button data-tab="chats"></button>
    <button data-tab="approvals"></button>
    <button data-tab="tasks"></button>
  </nav>
</div>
<script>
const T = __TEXTS__;
const $ = s => document.querySelector(s);
const view = $('#view');
let token = '';
let tab = 'chats';
let chatId = '';
let busy = false;
let badgeTimer = 0;

const fmt = (text, values) => text.replace(/\{(\w+)\}/g, (m, k) => values[k] ?? m);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const rich = s => esc(s).replace(/`([^`\n]+)`/g, '<code>$1</code>').replace(/\*\*([^*\n]+)\*\*/g, '<b>$1</b>');
const untitled = t => !t || t === 'New chat' || t === 'Ny chatt';
const when = iso => { try { return new Date(iso).toLocaleString([], {dateStyle: 'short', timeStyle: 'short'}); } catch { return ''; } };

try { token = localStorage.getItem('arqen-token') || ''; } catch {}
// The QR code's link carries the token in the fragment; keep it, then clear
// the address bar so it is not left on screen or in the history.
function tokenFromLink() {
  const fromLink = new URLSearchParams(location.hash.slice(1)).get('token');
  if (!fromLink) return false;
  token = fromLink;
  try { localStorage.setItem('arqen-token', token); } catch {}
  history.replaceState(null, '', location.pathname);
  return true;
}
tokenFromLink();
// Opening the link while the page is already open changes only the fragment.
window.addEventListener('hashchange', () => { if (tokenFromLink()) start(); });

async function api(method, path, body) {
  let response;
  try {
    response = await fetch('/api/v1' + path, {
      method, headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch { throw new Error(T.offline); }
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401) { signOut(T.badToken); throw new Error(T.badToken); }
  if (!response.ok) throw new Error(payload.error?.message || String(response.status));
  return payload.data;
}

function signOut(message) {
  token = '';
  try { localStorage.removeItem('arqen-token'); } catch {}
  showConnect(message);
}

function showConnect(message = '') {
  $('#tabs').hidden = true; $('#composer').hidden = true; $('#signout').hidden = true; $('#model').textContent = '';
  view.innerHTML = `<div class="connect"><h1>ARQEN</h1><p>${esc(T.connectHelp)}</p>
    <input id="token" type="password" autocomplete="off" placeholder="${esc(T.token)}">
    <button class="primary" id="connect">${esc(T.connect)}</button><p class="error">${esc(message)}</p></div>`;
  $('#connect').onclick = () => { token = $('#token').value.trim(); if (!token) return;
    try { localStorage.setItem('arqen-token', token); } catch {} start(); };
}

async function start() {
  try {
    const status = await api('GET', '/status');
    $('#model').textContent = status.model || status.provider || '';
  } catch (error) { if (token) showConnect(error.message); return; }
  $('#tabs').hidden = false; $('#signout').hidden = false;
  show(tab);
  refreshBadge();
  badgeTimer = badgeTimer || setInterval(refreshBadge, 20000);
}

function show(name) {
  tab = name; chatId = '';
  $('#composer').hidden = name !== 'chats';
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  ({chats: showChats, approvals: showApprovals, tasks: showTasks})[name]();
}

async function showChats() {
  view.innerHTML = '';
  try {
    const sessions = (await api('GET', '/sessions')).sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    if (tab !== 'chats' || chatId) return;
    view.innerHTML = sessions.length ? '<div class="list">' + sessions.slice(0, 50).map(s =>
      `<button class="row" data-id="${esc(s.session_id)}"><div class="title">${esc(untitled(s.title) ? T.newChat : s.title)}</div>
       <div class="meta">${esc(when(s.updated_at))}</div></button>`).join('') + '</div>'
      : `<div class="empty">${esc(T.noChats)}</div>`;
    view.querySelectorAll('.row').forEach(row => row.onclick = () => openChat(row.dataset.id));
  } catch (error) { view.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; }
}

async function openChat(id) {
  chatId = id;
  view.innerHTML = '';
  try {
    const session = await api('GET', '/sessions/' + id);
    if (chatId !== id) return;
    view.innerHTML = `<div class="chat-head"><button class="icon-btn" id="back">‹ ${esc(T.back)}</button>
      <span class="title">${esc(untitled(session.title) ? T.newChat : session.title)}</span></div><div id="messages"></div>`;
    $('#back').onclick = () => show('chats');
    for (const m of session.messages) {
      if (m.role === 'user') bubble('user', m.content);
      else if (m.role === 'assistant' && m.content) bubble('arqen', m.content);
    }
    if (session.confirmation) confirmation(session.confirmation);
    view.scrollTop = view.scrollHeight;
  } catch (error) { view.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; }
}

function bubble(kind, text) {
  const box = $('#messages'); if (!box) return null;
  const el = document.createElement('div');
  el.className = 'bubble ' + kind;
  el.innerHTML = kind === 'arqen' ? rich(text) : esc(text);
  box.appendChild(el);
  view.scrollTop = view.scrollHeight;
  return el;
}

function confirmation(pending) {
  const box = $('#messages'); if (!box) return;
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `<div class="what">${esc(fmt(T.wantsToRun, {tool: pending.tool}))}</div>
    <pre>${esc(JSON.stringify(pending.arguments, null, 2)).slice(0, 4000)}</pre>
    <div class="actions"><button class="ghost" data-approve="false">${esc(T.reject)}</button>
    <button class="primary" data-approve="true">${esc(T.approve)}</button></div>`;
  card.querySelectorAll('button').forEach(button => button.onclick = async () => {
    const approve = button.dataset.approve === 'true';
    card.classList.add('done');
    card.querySelector('.actions').innerHTML = `<span class="status">${esc(approve ? T.approved : T.rejected)}</span>`;
    await reply(() => api('POST', `/sessions/${chatId}/confirmation`, {approve}));
    refreshBadge();
  });
  box.appendChild(card);
  view.scrollTop = view.scrollHeight;
}

async function reply(call) {
  busy = true; $('#send').disabled = true;
  const waiting = bubble('arqen thinking', T.thinking);
  try {
    const result = await call();
    waiting?.remove();
    // With a tool waiting, the card says it all; the engine's "I need your
    // confirmation" line would only repeat it.
    if (result.confirmation) confirmation(result.confirmation);
    else if (result.assistant_message) bubble('arqen', result.assistant_message);
  } catch (error) {
    waiting?.remove();
    bubble('arqen', fmt(T.failed, {error: error.message}));
  } finally { busy = false; $('#send').disabled = false; }
}

async function send() {
  const input = $('#input');
  const content = input.value.trim();
  if (!content || busy) return;
  if (!chatId) {
    try { const created = await api('POST', '/sessions', {}); await openChat(created.session_id); }
    catch (error) { view.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; return; }
  }
  input.value = ''; grow();
  bubble('user', content);
  await reply(() => api('POST', `/sessions/${chatId}/messages`, {content}));
}

async function showApprovals() {
  view.innerHTML = '';
  try {
    const [approvals, tasks] = await Promise.all([api('GET', '/mission/approvals'), api('GET', '/mission/tasks')]);
    if (tab !== 'approvals') return;
    const titles = Object.fromEntries(tasks.map(t => [t.id, t.title]));
    const pending = approvals.filter(a => a.status === 'pending');
    if (!pending.length) { view.innerHTML = `<div class="empty">${esc(T.nothingWaiting)}</div>`; return; }
    view.innerHTML = pending.map(a => `<div class="card" data-id="${esc(a.id)}">
      <div class="meta status pending">${esc(T.task)}: ${esc(titles[a.task_id] || a.task_id.slice(0, 8))}</div>
      <div class="what">${esc(a.action)}</div><pre>${esc(JSON.stringify(a.payload, null, 2)).slice(0, 4000)}</pre>
      <div class="actions"><button class="ghost" data-status="rejected">${esc(T.reject)}</button>
      <button class="primary" data-status="approved">${esc(T.approve)}</button></div></div>`).join('');
    view.querySelectorAll('.card').forEach(card => card.querySelectorAll('button').forEach(button => button.onclick = async () => {
      card.classList.add('done');
      card.querySelector('.actions').innerHTML = `<span class="status">${esc(T.thinking)}</span>`;
      try {
        await api('POST', `/mission/approvals/${card.dataset.id}/decision`, {status: button.dataset.status});
        card.querySelector('.actions').innerHTML = `<span class="status">${esc(button.dataset.status === 'approved' ? T.approved : T.rejected)}</span>`;
      } catch (error) { card.querySelector('.actions').innerHTML = `<span class="error">${esc(error.message)}</span>`; }
      refreshBadge();
    }));
  } catch (error) { view.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; }
}

async function showTasks() {
  view.innerHTML = '';
  try {
    const tasks = (await api('GET', '/mission/tasks')).sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
    if (tab !== 'tasks') return;
    view.innerHTML = tasks.length ? '<div class="list">' + tasks.slice(0, 40).map(t =>
      `<button class="row" data-id="${esc(t.id)}"><div class="title">${esc(t.title)}</div>
       <div class="meta"><span class="status ${esc(t.status)}">${esc(T.status[t.status] || t.status)}</span> · ${esc(when(t.updated_at || t.created_at))}</div></button>`).join('') + '</div>'
      : `<div class="empty">${esc(T.noTasks)}</div>`;
    view.querySelectorAll('.row').forEach(row => row.onclick = () => openTask(row.dataset.id));
  } catch (error) { view.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; }
}

async function openTask(id) {
  try {
    const {task} = await api('GET', '/mission/tasks/' + id);
    view.innerHTML = `<div class="chat-head"><button class="icon-btn" id="back">‹ ${esc(T.back)}</button>
      <span class="title">${esc(task.title)}</span></div>
      <p class="status ${esc(task.status)}">${esc(T.status[task.status] || task.status)}</p>
      ${task.result ? `<h3>${esc(T.result)}</h3><div class="detail">${rich(task.result)}</div>` : ''}
      ${task.error ? `<h3>${esc(T.error)}</h3><div class="detail error">${esc(task.error)}</div>` : ''}`;
    $('#back').onclick = () => show('tasks');
  } catch (error) { view.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; }
}

async function refreshBadge() {
  if (!token) return;
  try {
    const approvals = await api('GET', '/mission/approvals');
    const count = approvals.filter(a => a.status === 'pending').length;
    const button = document.querySelector('[data-tab="approvals"]');
    button.innerHTML = esc(T.approvals) + (count ? `<span class="badge">${count}</span>` : '');
  } catch {}
}

function grow() { const input = $('#input'); input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 140) + 'px'; }

document.querySelectorAll('#tabs button').forEach(b => { b.textContent = T[b.dataset.tab]; b.onclick = () => show(b.dataset.tab); });
$('#send').textContent = T.send;
$('#input').placeholder = T.placeholder;
$('#signout').textContent = T.signOut;
$('#signout').onclick = () => signOut('');
$('#send').onclick = send;
$('#input').addEventListener('input', grow);
$('#input').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !matchMedia('(pointer: coarse)').matches) { e.preventDefault(); send(); } });

if (token) start(); else showConnect();
</script>
</body>
</html>
"""
