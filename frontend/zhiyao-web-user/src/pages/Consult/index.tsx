import { useState, useRef, useEffect } from 'react'
import { Input, Button, Avatar, Spin, Typography, message } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined, ReloadOutlined, MedicineBoxOutlined } from '@ant-design/icons'
import { sendMessage, ChatMessage, getUserLatestSession } from '../../services/consult'
import useUserStore from '../../stores/userStore'
import './Consult.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

// 快捷问题
const quickQuestions = [
  '感冒发烧吃什么药？',
  '头痛吃什么药好？',
  '阿莫西林的用法用量？',
  '布洛芬和对乙酰氨基酚可以一起吃吗？',
  '孕妇可以吃什么感冒药？',
  '儿童退烧药怎么选？',
]

const Consult = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [initLoading, setInitLoading] = useState(true)
  const [sessionId, setSessionId] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { isLoggedIn } = useUserStore()

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 页面加载时获取历史对话
  useEffect(() => {
    const loadHistory = async () => {
      if (!isLoggedIn) {
        setInitLoading(false)
        return
      }
      try {
        const res = await getUserLatestSession()
        if (res.data && res.data.messages && res.data.messages.length > 0) {
          setMessages(res.data.messages)
          setSessionId(res.data.sessionId || '')
        }
      } catch (error) {
        console.error('加载历史对话失败:', error)
      } finally {
        setInitLoading(false)
      }
    }
    loadHistory()
  }, [isLoggedIn])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 发送消息
  const handleSend = async (content?: string) => {
    const messageContent = content || inputValue.trim()
    if (!messageContent) return

    // 添加用户消息
    const userMessage: ChatMessage = { role: 'user', content: messageContent }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      const res = await sendMessage(messageContent, messages, sessionId)
      if (res.data) {
        const aiMessage: ChatMessage = { role: 'assistant', content: res.data.reply }
        setMessages(prev => [...prev, aiMessage])
        if (res.data.sessionId) {
          setSessionId(res.data.sessionId)
        }
      }
    } catch (error) {
      console.error('发送失败:', error)
      message.error('发送失败，请重试')
      // 添加错误消息
      const errorMessage: ChatMessage = { 
        role: 'assistant', 
        content: '抱歉，我暂时无法回复，请稍后再试 😅' 
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  // 新建对话
  const handleNewChat = () => {
    setMessages([])
    setSessionId('')
    setInputValue('')
  }

  // 快捷问题点击
  const handleQuickQuestion = (question: string) => {
    handleSend(question)
  }

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="consult-page">
      <div className="consult-card">
        {/* 头部 */}
        <div className="consult-header">
          <div className="header-left">
            <Avatar size={48} icon={<RobotOutlined />} className="ai-avatar" />
            <div className="header-info">
              <Title level={4} style={{ margin: 0 }}>小智 - AI用药助手</Title>
              <Text type="secondary">知药专业用药咨询</Text>
            </div>
          </div>
          <Button icon={<ReloadOutlined />} onClick={handleNewChat}>
            新对话
          </Button>
        </div>

        {/* 消息区域 */}
        <div className="messages-container">
          {initLoading ? (
            <div className="welcome-section">
              <Spin size="large" />
              <Text type="secondary" style={{ marginTop: 16 }}>正在加载对话历史...</Text>
            </div>
          ) : messages.length === 0 ? (
            <div className="welcome-section">
              <div className="welcome-icon">
                <MedicineBoxOutlined />
              </div>
              <Title level={3}>您好，我是小智 👋</Title>
              <Paragraph type="secondary" style={{ fontSize: 16 }}>
                您的专业用药咨询助手，可以帮您解答用药问题、分析症状、查询药品信息
              </Paragraph>
              <div className="quick-questions">
                <Text strong style={{ marginBottom: 12, display: 'block' }}>快速开始：</Text>
                <div className="questions-grid">
                  {quickQuestions.map((q, idx) => (
                    <Button 
                      key={idx} 
                      className="quick-btn"
                      onClick={() => handleQuickQuestion(q)}
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="disclaimer">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ⚠️ 温馨提示：AI建议仅供参考，具体用药请遵医嘱
                </Text>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg, idx) => (
                <div 
                  key={idx} 
                  className={`message-item ${msg.role === 'user' ? 'user-message' : 'ai-message'}`}
                >
                  <Avatar 
                    size={36}
                    icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    className={msg.role === 'user' ? 'user-avatar' : 'ai-avatar'}
                  />
                  <div className="message-content">
                    <div className="message-bubble">
                      <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {msg.content}
                      </Paragraph>
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message-item ai-message">
                  <Avatar size={36} icon={<RobotOutlined />} className="ai-avatar" />
                  <div className="message-content">
                    <div className="message-bubble loading-bubble">
                      <Spin size="small" />
                      <Text type="secondary" style={{ marginLeft: 8 }}>小智正在思考...</Text>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="input-container">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="请输入您的用药问题..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
            className="message-input"
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || loading}
            className="send-btn"
          >
            发送
          </Button>
        </div>
      </div>
    </div>
  )
}

export default Consult
