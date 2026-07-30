import request from './request'

export const getRoomList = () => {
  return request.get('/api/room/list')
}

export const enterRoom = (data) => {
  return request.post('/api/room/enter', data)
}

export const getRoomMembers = (roomId) => {
  return request.get(`/api/room/${roomId}/members`)
}

export const getMessages = (roomId) => {
  return request.get(`/api/messages/${roomId}`)
}

export const getMessageCount = (roomId) => {
  return request.get(`/api/messages/${roomId}/count`)
}

const tryFetch = async (url, token) => {
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
  return res
}

export const clearMessages = (roomId) => {
  return request.delete(`/api/messages/${roomId}/clear`)
}

export const deleteRoom = (roomId) => {
  return request.delete(`/api/room/${roomId}`)
}

export const exportMessages = async (roomId) => {
  const token = localStorage.getItem('token')
  const paths = [
    `/api/messages/${roomId}/export`,
    `/api/messages/${roomId}/export/`,
    `/api/messages/export/${roomId}`,
    `/api/messages/export/${roomId}/`,
    `/api/export/messages/${roomId}`,
    `/api/room/${roomId}/export`,
    `/api/export/${roomId}`,
    `/api/messages/${roomId}/download`,
    `/api/messages/export?room_id=${roomId}`
  ]
  for (const path of paths) {
    const res = await tryFetch(path, token)
    if (res.ok) return res.blob()
    if (res.status !== 404) {
      const text = await res.text().catch(() => '')
      throw new Error(text || `导出失败 (${res.status})`)
    }
  }
  throw new Error('导出接口不存在，请确认后端路径')
}
