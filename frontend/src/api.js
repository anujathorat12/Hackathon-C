// Same-origin by default: Vite proxies /api in dev, FastAPI serves the build in demo mode.
const BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
const WS_ROOT = '/api/v1/workspaces'

async function request(path, options = {}) {
  const res = await fetch(BASE + path, options)
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try { detail = (await res.json()).detail || detail } catch { /* non-JSON error body */ }
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
  health: () => request('/api/health'),
  stats: () => request(`${WS_ROOT}/stats/summary`),
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
  sources: (id) => request(`${WS_ROOT}/${id}/sources`),
  uploadSource: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`${WS_ROOT}/${id}/sources`, { method: 'POST', body: form })
  },
  generate: (id) => request(`${WS_ROOT}/${id}/generate`, json('POST')),
  approve: (id, content) => request(`${WS_ROOT}/${id}/approve`, json('POST', { content_markdown: content })),
  preview: (id, content) => request(`${WS_ROOT}/${id}/preview`, json('POST', { content_markdown: content })),
  revise: (id, content, instruction, section) =>
    request(`${WS_ROOT}/${id}/revise`, json('POST', { content_markdown: content, instruction, section: section || null })),
  streamUrl: (id) => {
    const origin = BASE || window.location.origin
    return origin.replace(/^http/, 'ws') + `${WS_ROOT}/${id}/stream`
  },
  fileUrl: (path) => BASE + path,
}
