import request from '../utils/request'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  sessionId: string
  timestamp: number
}

// 发送咨询消息
export const sendMessage = (message: string, history: ChatMessage[], sessionId?: string) => {
  return request.post<ChatResponse>('/consult/chat', {
    message,
    history,
    sessionId
  })
}

// 获取对话历史
export const getChatHistory = (sessionId: string) => {
  return request.get<ChatMessage[]>(`/consult/history/${sessionId}`)
}

// 创建新会话
export const createSession = () => {
  return request.post<{ sessionId: string }>('/consult/session/new')
}

// 获取用户最近的对话历史
export const getUserLatestSession = () => {
  return request.get<{ sessionId: string; messages: ChatMessage[] }>('/consult/user/latest')
}
