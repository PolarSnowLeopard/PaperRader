import api from './request'

export const triggerArxivSync = (maxResults = 100) =>
  api.post('/sync/arxiv', null, { params: { max_results: maxResults } })

export const triggerDblpSync = (maxResults = 100) =>
  api.post('/sync/dblp', null, { params: { max_results: maxResults } })

export const triggerOpenReviewSync = (conference, maxResults = 200) =>
  api.post('/sync/openreview', null, { params: { conference, max_results: maxResults } })

export const triggerAclSync = (conference, maxResults = 200) =>
  api.post('/sync/acl', null, { params: { conference, max_results: maxResults } })

export const getSyncLogs = (limit = 20) => api.get('/sync/logs', { params: { limit } })

export const getConferenceStats = (venue) => api.get('/sync/conference-stats', { params: { venue } })

export const batchImportToWorkspace = (venue, folderId, limit = 50) =>
  api.post('/sync/batch-import', null, { params: { venue, folder_id: folderId, limit } })
