import api from './request'

export const getChatSessions = (wsId) => api.get(`/workspaces/${wsId}/chat`)

export const createChatSession = (wsId, title) => api.post(`/workspaces/${wsId}/chat`, { title })

export const deleteChatSession = (sessionId) => api.delete(`/chat/${sessionId}`)

export const getMessages = (sessionId) => api.get(`/chat/${sessionId}/messages`)

export const sendMessage = (sessionId, content) => api.post(`/chat/${sessionId}/messages`, { content })
