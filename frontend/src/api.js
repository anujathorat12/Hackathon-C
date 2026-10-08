// Same-origin by default: Vite proxies /api in dev, FastAPI serves the build in demo mode.
const BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
const WS_ROOT = '/api/v1/workspaces'
const AUTH_ROOT = '/api/v1/auth'

export const getToken = () => localStorage.getItem('agent101_token')
export const setToken = (t) => {
  if (t) {
    localStorage.setItem('agent101_token', t)
  } else {
    localStorage.removeItem('agent101_token')
  }
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  const token = getToken()
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(BASE + path, { ...options, headers })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch { /* non-JSON error body */ }
    throw new Error(detail)
  }
  return res.json()
}

const json = (method, body) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: body === undefined ? undefined : JSON.stringify(body),
})

export const api = {
  // Auth & Admin
  login: (email, password) => request(`${AUTH_ROOT}/login`, json('POST', { email, password })),
  register: (data) => request(`${AUTH_ROOT}/register`, json('POST', data)),
  me: () => request(`${AUTH_ROOT}/me`),
  logout: () => request(`${AUTH_ROOT}/logout`, json('POST')),
  getUsers: () => request(`${AUTH_ROOT}/users`),
  adminGetAnalytics: () => request(`${AUTH_ROOT}/admin/analytics`),
  adminCreateUser: (data) => request(`${AUTH_ROOT}/admin/users`, json('POST', data)),
  adminUpdateRole: (id, role) => request(`${AUTH_ROOT}/admin/users/${id}/role`, json('PATCH', { role })),
  adminDeleteUser: (id) => request(`${AUTH_ROOT}/admin/users/${id}`, { method: 'DELETE' }),
  adminResetPassword: (id, new_password) => request(`${AUTH_ROOT}/admin/users/${id}/reset-password`, json('POST', { new_password })),

  // Workspaces & Studio
  health: () => request('/api/health'),
  list: () => request(WS_ROOT),
  create: (data) => request(WS_ROOT, json('POST', data)),
  remove: (id) => request(`${WS_ROOT}/${id}`, { method: 'DELETE' }),
  run: (id) => request(`${WS_ROOT}/${id}/run`),
  templates: (id) => request(`${WS_ROOT}/${id}/templates`),
  upload: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`${WS_ROOT}/${id}/templates`, { method: 'POST', body: form })
  },
  generate: (id) => request(`${WS_ROOT}/${id}/generate`, json('POST')),
  approve: (id, content) => request(`${WS_ROOT}/${id}/approve`, json('POST', { content_markdown: content })),
  streamUrl: (id) => {
    const origin = BASE || window.location.origin
    return origin.replace(/^http/, 'ws') + `${WS_ROOT}/${id}/stream`
  },
  fileUrl: (path) => BASE + path,
  deliverablePreview: (id) => request(`${WS_ROOT}/${id}/deliverable/preview`),
}
