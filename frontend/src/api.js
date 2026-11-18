const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options) {
  const response = await fetch(`${baseUrl}${path}`, options)
  if (!response.ok) throw new Error(`请求失败（${response.status}），请检查接口服务`)
  return response.json()
}

export function uploadDocument(file) {
  const body = new FormData()
  body.append('file', file)
  return request('/api/documents', { method: 'POST', body })
}

export function askQuestion(question, documentIds, history) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, document_ids: documentIds, history }),
  })
}
