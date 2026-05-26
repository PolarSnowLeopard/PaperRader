import api from './request'

export const triggerArxivSync = (maxResults = 100) =>
  api.post('/sync/arxiv', null, { params: { max_results: maxResults } })

export const triggerDblpSync = (maxResults = 100) =>
  api.post('/sync/dblp', null, { params: { max_results: maxResults } })

export const getSyncLogs = (limit = 20) => api.get('/sync/logs', { params: { limit } })
