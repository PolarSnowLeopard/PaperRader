import api from './request'

export const getWorkspaces = () => api.get('/workspaces')

export const createWorkspace = (data) => api.post('/workspaces', data)

export const getWorkspace = (id) => api.get(`/workspaces/${id}`)

export const updateWorkspace = (id, data) => api.patch(`/workspaces/${id}`, data)

export const deleteWorkspace = (id) => api.delete(`/workspaces/${id}`)

export const getWorkspacePapers = (wsId) => api.get(`/workspaces/${wsId}/papers`)

// Folders
export const getFolderTree = (wsId) => api.get(`/workspaces/${wsId}/folders`)

export const createFolder = (wsId, data) => api.post(`/workspaces/${wsId}/folders`, data)

export const updateFolder = (id, data) => api.patch(`/folders/${id}`, data)

export const deleteFolder = (id) => api.delete(`/folders/${id}`)

export const getFolderPapers = (folderId) => api.get(`/folders/${folderId}/papers`)

export const addPaperToFolder = (folderId, paperId) =>
  api.post(`/folders/${folderId}/papers`, null, { params: { paper_id: paperId } })

export const removePaperFromFolder = (folderId, paperId) =>
  api.delete(`/folders/${folderId}/papers/${paperId}`)

// Tags
export const getTags = (wsId) => api.get(`/workspaces/${wsId}/tags`)

export const createTag = (wsId, data) => api.post(`/workspaces/${wsId}/tags`, data)

export const updateTag = (id, data) => api.patch(`/tags/${id}`, data)

export const deleteTag = (id) => api.delete(`/tags/${id}`)

export const addTagToPaper = (paperId, tagId) =>
  api.post(`/papers/${paperId}/tags`, null, { params: { tag_id: tagId } })

export const removeTagFromPaper = (paperId, tagId) =>
  api.delete(`/papers/${paperId}/tags/${tagId}`)

// Notes
export const getNote = (paperId, wsId) =>
  api.get(`/papers/${paperId}/notes`, { params: { workspace_id: wsId } })

export const saveNote = (paperId, data) => api.put(`/papers/${paperId}/notes`, data)
