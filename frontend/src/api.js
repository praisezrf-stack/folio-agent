const baseUrl = (import.meta.env.VITE_API_BASE_URL || '/backend').replace(/\/$/, '')

async function request(path, options) {
  const response = await fetch(`${baseUrl}${path}`, options)
  if (!response.ok) throw new Error(`请求失败（${response.status}），请检查接口服务`)
  return response.json()
}

export async function uploadDocument(file) {
  const body = new FormData()
  body.append('file', file)
  const result = await request('/documents', { method: 'POST', body })
  if (result.code !== 200) throw new Error(result.msg)
  return { id: result.content[0][0] }
}

export function getDocuments(id = '') {
  return request(`/documents?${new URLSearchParams({ id })}`)
}

export function askQuestion(question, documentIds, history) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, document_ids: documentIds, history }),
  })
}
