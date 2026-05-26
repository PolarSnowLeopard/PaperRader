import api from './request'

export const searchPapers = (data) => api.post('/search', data)
