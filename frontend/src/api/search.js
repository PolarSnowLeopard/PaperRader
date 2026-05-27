import api from './request'

export const searchPapers = (data) => api.post('/search', data)

export const externalSearch = (data) => api.post('/search/external', data)
