import request from './request'

export const getSemanticConfig = () => {
  return request.get('/api/semantic/config')
}

export const saveSemanticConfig = (intervalSeconds) => {
  return request.post('/api/semantic/config', { interval_seconds: intervalSeconds })
}

export const addKeyword = (keyword) => {
  return request.post('/api/semantic/keyword', { keyword })
}

export const deleteKeyword = (id) => {
  return request.delete(`/api/semantic/keyword/${id}`)
}
