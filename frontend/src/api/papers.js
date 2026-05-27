import api from './request'

export const getPapers = (params) => api.get('/papers', { params })

export const getPaper = (id) => api.get(`/papers/${id}`)

export const uploadPaper = (file, title) => {
  const formData = new FormData()
  formData.append('file', file)
  if (title) formData.append('title', title)
  return api.post('/papers/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const importPaper = (data) => api.post('/papers/import', data)

export const deletePaper = (id) => api.delete(`/papers/${id}`)

export const getPaperPdfUrl = (id) => `/api/papers/${id}/pdf`

export const downloadPaperPdf = (id) => api.post(`/papers/${id}/download-pdf`)

export const generateReport = (id) => api.post(`/papers/${id}/report`)

export const getReport = (id) => api.get(`/papers/${id}/report`)

export const askPaperQuestion = (id, question) => api.post(`/papers/${id}/ask`, { question })
