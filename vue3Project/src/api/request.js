import axios from 'axios'

const request = axios.create({
  baseURL: '',
  timeout: 60000
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401 && localStorage.getItem('token')) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      let msg = '请求失败'
      try {
        msg = data?.detail || data?.message || JSON.stringify(data)
      } catch (_) {}
      const err = new Error(msg)
      err.status = status
      throw err
    }
    throw new Error('网络错误')
  }
)

export default request
