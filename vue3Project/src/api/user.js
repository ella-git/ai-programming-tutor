import request from './request'

export const getUsersList = (params) => {
  return request.get('/api/auth/usersList', { params })
}

export const deleteUser = (userId) => {
  return request.delete(`/api/auth/users/${userId}`)
}
