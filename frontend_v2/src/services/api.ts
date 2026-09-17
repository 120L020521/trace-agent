import axios from 'axios'
import type { Disruption, TripFormData, TripPlan, TripPlanResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    console.error('生成旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成旅行计划失败')
  }
}

export interface KnowledgeUploadResponse {
  success: boolean
  source_id: string
  source_name: string
  chunks: number
  extractor: string
  preview: string
}

export async function uploadKnowledge(file: File): Promise<KnowledgeUploadResponse> {
  const body = new FormData()
  body.append('file', file)
  body.append('category', 'user-trip-material')
  const response = await apiClient.post<KnowledgeUploadResponse>('/api/knowledge/upload', body, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function replanTrip(
  request: TripFormData,
  currentPlan: TripPlan,
  disruption: Disruption
): Promise<TripPlanResponse> {
  const response = await apiClient.post<TripPlanResponse>('/api/trip/replan', {
    request,
    current_plan: currentPlan,
    disruption
  })
  return response.data
}

export async function submitTripFeedback(
  traceId: string,
  accepted: boolean,
  rating?: number,
  comment = ''
): Promise<void> {
  await apiClient.post('/api/flywheel/feedback', {
    trace_id: traceId,
    accepted,
    rating,
    comment
  })
}

export async function getPlanningTrace(traceId: string): Promise<any> {
  const response = await apiClient.get(`/api/flywheel/trace/${traceId}`)
  return response.data.data
}

export async function getFlywheelStats(): Promise<any> {
  const response = await apiClient.get('/api/flywheel/stats')
  return response.data.data
}

export async function getHardCases(limit = 50): Promise<any[]> {
  const response = await apiClient.get('/api/flywheel/hard-cases', { params: { limit } })
  return response.data.data
}

export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient
