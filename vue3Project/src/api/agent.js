import request from './request'

export const getPrompt = (agentType) => {
  return request.get(`/api/agent/prompt/${agentType}`)
}

export const uploadPrompt = (agentType, file) => {
  const formData = new FormData()
  formData.append('agent_type', agentType)
  formData.append('file', file)
  return request.post('/api/agent/prompt/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const metacognitiveChat = (roomId, question) => {
  return request.post('/api/agent/metacognitive/chat', { room_id: roomId, question })
}
