import api from './request'

export const getOverview = () => api.get('/stats/overview')

export const getTrends = (days = 30) => api.get('/stats/trends', { params: { days } })

export const getTopics = (limit = 20) => api.get('/stats/topics', { params: { limit } })

export const getVenues = (limit = 20) => api.get('/stats/venues', { params: { limit } })
