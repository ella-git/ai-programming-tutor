import request from './request'

export const uploadKnowledgeFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getKnowledgeList = () => {
  return request.get('/api/knowledge/list')
}

export const deleteKnowledgeFile = (id) => {
  return request.delete(`/api/knowledge/${id}`)
}

export const getEmbeddingStatus = (fileId) => {
  return request.get(`/api/knowledge/embedding/status/${fileId}`)
}
