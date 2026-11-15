import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

export default api

// Visit planning
export const planVisit = (data: object) => api.post('/visits/plan', data)
export const getVisit = (visitId: string) => api.get(`/visits/${visitId}`)
export const getTrace = (visitId: string) => api.get(`/visits/${visitId}/trace`)
export const completeStop = (visitId: string, exhibitId: string) =>
  api.post(`/visits/${visitId}/complete-stop`, { exhibit_id: exhibitId })
export const submitFeedback = (visitId: string, exhibitId: string, liked: boolean, comment: string) =>
  api.post(`/visits/${visitId}/feedback`, { exhibit_id: exhibitId, liked, comment })
export const replanVisit = (visitId: string, busyGalleryId: string) =>
  api.post(`/visits/${visitId}/replan`, { busy_gallery_id: busyGalleryId })
export const getSources = (visitId: string) => api.get(`/visits/${visitId}/sources`)

// Galleries
export const getGalleries = () => api.get('/galleries')
export const getCrowdStatus = () => api.get('/galleries/crowd')
export const updateCrowd = (galleryId: string, crowdState: string) =>
  api.patch(`/galleries/${galleryId}/crowd`, { crowd_state: crowdState })

// Exhibits
export const getExhibits = () => api.get('/exhibits')

// Visitor memory
export const getVisitor = (visitorId: string) => api.get(`/visitors/${visitorId}`)
export const updateVisitorPrefs = (visitorId: string, data: object) =>
  api.patch(`/visitors/${visitorId}/preferences`, data)
export const clearVisitorMemory = (visitorId: string) =>
  api.delete(`/visitors/${visitorId}/memory`)

// Evaluation
export const runEvaluation = () => api.post('/evaluation/run')
export const getLatestReport = () => api.get('/evaluation/latest')
export const getEvalProfiles = () => api.get('/evaluation/profiles')

// Admin
export const reindex = () => api.post('/admin/reindex')

// Health
export const healthCheck = () => api.get('/health')
