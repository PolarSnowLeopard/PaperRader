import api from './request'

export const login = (data) => api.post('/auth/login', data)

export const getMe = () => api.get('/auth/me')
