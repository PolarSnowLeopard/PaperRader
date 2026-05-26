import api from './request'

export const getPapers = (params) => api.get('/papers', { params })

export const getPaper = (id) => api.get(`/papers/${id}`)

export const updateUserPaper = (id, data) => api.patch(`/papers/${id}/user`, data)

export const deletePaper = (id) => api.delete(`/papers/${id}`)
