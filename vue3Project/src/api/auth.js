import request from './request'

export const login = (data) => {
  return request.post('/api/auth/login', data)
}

export const register = (data) => {
  return request.post('/api/auth/register', data)
}

export const logout = () => {
  return api.post('/logout')
}

export const getUserInfo = () => {
  return api.get('/user/info')
}