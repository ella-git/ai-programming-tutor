<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>
        <span class="conn-dot" :class="{ connected: connected }"></span>
        {{ roomName }}聊天室
      </h2>
      <div class="room-info">
        <el-button type="primary" @click="leaveRoom">离开聊天室</el-button>
      </div>
    </div>
    
    <div class="chat-body">
      <div class="chat-main">
        <div class="chat-messages" ref="messagesContainer">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            :class="['message', 
              message.type === 'system' ? 'system-message' : 
              message.type === 'agent' && message.agent === 'metacognitive' ? 'meta-message' :
              message.type === 'agent' ? 'agent-message' :
              message.username === currentUser ? 'own-message' : 'other-message'
            ]"
          >
            <template v-if="message.type === 'system'">
              {{ message.content }}
            </template>
            <template v-else-if="message.type === 'agent'">
              <div class="message-username">
                <template v-if="message.agent === 'metacognitive'">
                  {{ message.pending ? '正在分析...' : '小智同学' }}
                </template>
                <template v-else>
                  <el-icon style="margin-right:4px"><MagicStick /></el-icon>{{ message.pending ? `${message.username} 正在提问...` : message.username }}
                </template>
                <span class="message-time-inline">{{ formatTime(message.time) }}</span>
              </div>
              <div v-if="message.pending" class="message-content thinking-content">
                <span class="thinking-dot"></span>
                <span class="thinking-dot"></span>
                <span class="thinking-dot"></span>
              </div>
              <div v-else class="message-content">{{ message.content }}</div>
            </template>
            <template v-else-if="message.type === 'image'">
              <div class="message-username">{{ message.username }} <span class="message-time-inline">{{ formatTime(message.time) }}</span></div>
              <el-image :src="message.content" class="message-image" :preview-src-list="[message.content]" fit="contain" @load="scrollToBottom" />
            </template>
            <template v-else>
              <div class="message-username">{{ message.username }} <span class="message-time-inline">{{ formatTime(message.time) }}</span></div>
              <div class="message-content">{{ message.content }}</div>
            </template>
          </div>
        </div>
        
        <div class="chat-input">
          <input type="file" ref="fileInput" accept="image/*" hidden @change="handleFileSelect" />
          <el-button class="upload-btn" :class="{ 'is-loading': uploading }" @click="$refs.fileInput.click()">+</el-button>
          <el-button class="at-btn" @click="newMessage = '@认知智能体  ' + newMessage">@</el-button>
          <textarea
            v-model="newMessage"
            class="chat-textarea"
            rows="1"
            placeholder="输入消息... (Shift+Enter换行)"
            @keydown="handleInputKeydown"
          ></textarea>
          <el-button 
            type="primary" 
            @click="sendMessage"
          >
            发送
          </el-button>
        </div>
      </div>
      
      <div class="member-panel">
        <div class="member-title">
          <span>成员列表</span>
          <el-tag size="small" type="info">{{ memberCount }}人</el-tag>
        </div>
        <div class="member-msg-total">
          <el-icon style="margin-right:4px;vertical-align:middle;"><ChatDotRound /></el-icon>
          共 {{ totalMessages }} 条消息
        </div>
        <div class="member-list">
          <div v-for="(member, index) in members" :key="index" class="member-item">
            <span class="member-dot" :class="{ online: member.is_online }"></span>
            <span class="member-name">{{ member.username || member.name }}</span>
            <span class="member-msg-count">{{ getMemberMsgCount(member.username || member.name) }}条</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { getRoomMembers, getMessages, getMessageCount } from '../api/room'
import { createSocket, sendMessage as wsSend, sendImage as wsSendImage, closeSocket } from '../websocket/socket'
import request from '../api/request'

const router = useRouter()
const messages = ref([])
const newMessage = ref('')
const roomName = ref('')
const currentUser = ref('')
const messagesContainer = ref()
const connected = ref(false)
const members = ref([])
const memberCount = ref(0)
const totalMessages = ref(0)
const fileInput = ref()
const uploading = ref(false)

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}

const AGENT_PREFIX = '@认知智能体'

const handleInputKeydown = (e) => {
  if (e.isComposing) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const sendMessage = async () => {
  const text = newMessage.value
  if (!text.trim()) {
    newMessage.value = ''
    return
  }
  newMessage.value = ''
  if (text.startsWith(AGENT_PREFIX)) {
    const content = text.slice(AGENT_PREFIX.length).trim()
    if (!content) {
      ElMessage.warning('请输入您的问题')
      return
    }
    const client_id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
    messages.value = [...messages.value, {
      type: 'agent',
      username: currentUser.value,
      request_id: client_id,
      pending: true,
      content: '',
      time: new Date().toISOString(),
    }]
    totalMessages.value++
    nextTick(scrollToBottom)
    try {
      const roomId = localStorage.getItem('room_id')
      await request.post('/api/agent/chat', {
        room_id: Number(roomId),
        question: content,
        client_id: client_id,
      })
    } catch (e) {
      const idx = messages.value.findIndex(m => m.request_id === client_id)
      if (idx !== -1) {
        const updated = [...messages.value]
        updated[idx] = { ...updated[idx], pending: false, content: '智能体暂时无法回答，请稍后再试。' }
        messages.value = updated
      }
      ElMessage.error('智能体: ' + e.message)
    }
    return
  }
  wsSend(text)
}

const handleFileSelect = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await request.post('/api/upload/image', formData)
    const url = res.url || res.path || res.data || ''
    if (url) wsSendImage(url)
  } catch (err) {
    ElMessage.error(err.message || '图片上传失败')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function extractUsername(systemContent) {
  for (const m of members.value) {
    const name = m.username || m.name
    if (name && systemContent.includes(name)) return name
  }
  return null
}

const handleSocketMessage = (data) => {
  if (data.type === 'system') {
    messages.value = [...messages.value, { type: 'system', content: data.content, time: data.time }]
    const name = extractUsername(data.content)
    if (name) {
      const member = members.value.find(m => (m.username || m.name) === name)
      if (member) {
        member.is_online = data.content.includes('进入')
      }
    }
  } else if (data.type === 'agent_pending') {
    if (!messages.value.find(m => m.request_id === data.request_id)) {
      messages.value = [...messages.value, {
        type: 'agent',
        username: data.username,
        agent: data.agent,
        request_id: data.request_id,
        pending: true,
        content: '',
        time: data.time,
      }]
      totalMessages.value++
    }
  } else if (data.type === 'agent') {
    if (data.request_id != null) {
      const idx = messages.value.findIndex(m => m.request_id === data.request_id)
      if (idx !== -1) {
        const updated = [...messages.value]
        updated[idx] = {
          ...updated[idx],
          pending: false,
          content: data.content,
          username: data.username,
          agent: data.agent,
          time: data.time,
        }
        messages.value = updated
      } else {
        messages.value = [...messages.value, {
          type: 'agent',
          username: data.username,
          agent: data.agent,
          content: data.content,
          time: data.time,
        }]
        totalMessages.value++
      }
    } else {
      messages.value = [...messages.value, {
        type: 'agent',
        username: data.username,
        agent: data.agent,
        content: data.content,
        time: data.time,
      }]
      totalMessages.value++
    }
  } else if (data.type === 'image') {
    messages.value = [...messages.value, {
      type: 'image',
      username: data.username,
      content: data.content,
      time: data.time
    }]
    totalMessages.value++
  } else {
    messages.value = [...messages.value, {
      username: data.username,
      content: data.content,
      time: data.time
    }]
    totalMessages.value++
  }
  nextTick(scrollToBottom)
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const getMemberMsgCount = (username) => {
  return messages.value.filter(m => m.username === username).length
}

const leaveRoom = () => {
  closeSocket()
  router.push('/home/join-room')
}

const fetchMembers = async () => {
  const roomId = localStorage.getItem('room_id')
  if (!roomId) return
  try {
    const res = await getRoomMembers(roomId)
    let list
    if (Array.isArray(res)) {
      list = res
    } else {
      list = res.members || res.users || res.data || res.user_list || []
    }
    for (const m of list) {
      const name = m.username || m.name
      const existing = members.value.find(e => (e.username || e.name) === name)
      if (existing) {
        existing.is_online = m.is_online
      } else {
        members.value.push({ ...m })
      }
    }
    memberCount.value = members.value.length
  } catch (e) {
    console.error('获取成员列表失败', e)
  }
}

const normalizeMessage = (m) => {
  let msg = { ...m }
  if (!msg.time && msg.created_at) {
    msg.time = msg.created_at
  }
  if (!msg.time && msg.created_time) {
    msg.time = msg.created_time
  }
  if (!msg.time) {
    msg.time = new Date().toISOString()
  }
  if (!msg.username && msg.sender) {
    msg.username = msg.sender
  }
  if (msg.type === 'image' || msg.message_type === 'image') {
    msg.type = 'image'
  } else if (msg.type === 'agent' || msg.message_type === 'agent') {
    msg.type = 'agent'
    if (msg.agent === 'metacognitive' || msg.sender === '元认知智能体' || msg.username === '元认知智能体' || msg.sender === '小智同学' || msg.username === '小智同学') {
      msg.agent = 'metacognitive'
    }
  } else if (typeof msg.content === 'string' && msg.content.startsWith('/uploads/')) {
    msg.type = 'image'
  } else {
    msg.type = msg.type || 'text'
  }
  return msg
}

const fetchHistoryMessages = async () => {
  const roomId = localStorage.getItem('room_id')
  if (!roomId) return []
  try {
    const res = await getMessages(roomId)
    const list = Array.isArray(res) ? res : (res.messages || res.data || [])
    return list.map(normalizeMessage)
  } catch (e) {
    console.error('获取历史消息失败', e)
    return []
  }
}

const fetchMsgCount = async () => {
  const roomId = localStorage.getItem('room_id')
  if (!roomId) return
  try {
    const res = await getMessageCount(roomId)
    totalMessages.value = res.count ?? res.total ?? 0
  } catch (e) {
    console.error('获取消息数量失败', e)
  }
}

onMounted(async () => {
  currentUser.value = localStorage.getItem('username') || 'student'
  roomName.value = localStorage.getItem('room_code') || '聊天室'

  const roomId = localStorage.getItem('room_id')
  const token = localStorage.getItem('token')

  if (!roomId || !token) {
    ElMessage.error('连接信息不完整')
    return
  }

  // 1. 历史消息
  messages.value = await fetchHistoryMessages()
  nextTick(scrollToBottom)

  // 2. 成员列表
  await fetchMembers()

  // 3. 消息数量
  await fetchMsgCount()

  // 4. WebSocket
  createSocket(roomId, token, handleSocketMessage, (status) => {
    connected.value = status
    if (status) fetchMembers()
  })
})

onBeforeUnmount(() => {
  closeSocket()
})
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #F7F8FA;
}

.chat-header {
  background: white;
  padding: 16px 24px;
  border-bottom: 1px solid #E4E7ED;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chat-header h2 {
  margin: 0;
  color: #333333;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conn-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #F56C6C;
  flex-shrink: 0;
}

.conn-dot.connected {
  background: #67C23A;
}

.room-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.room-info span {
  color: #666666;
  font-size: 14px;
}

.message {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.own-message {
  align-self: flex-end;
  background: #409EFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.other-message {
  align-self: flex-start;
  background: white;
  color: #333333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.system-message {
  align-self: center;
  background: transparent;
  color: #909399;
  font-size: 12px;
  padding: 4px 12px;
  max-width: 100%;
  text-align: center;
}

.agent-message {
  align-self: flex-start;
  background: #FFF0F0;
  color: #333333;
  border-bottom-left-radius: 4px;
  border: 1px solid #FFD5D5;
}

.meta-message {
  align-self: flex-start;
  background: #F0F9FF;
  color: #333333;
  border-bottom-left-radius: 4px;
  border: 1px solid #B3E5FC;
}

.meta-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #409EFF;
  background: #E6F7FF;
  border: 1px solid #91D5FF;
  border-radius: 3px;
  padding: 0 5px;
  margin-right: 4px;
  line-height: 1.6;
}

.message-username {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
  opacity: 0.8;
}

.message-time-inline {
  font-weight: 400;
  opacity: 0.6;
  margin-left: 6px;
  font-size: 11px;
}

.message-content {
  font-size: 14px;
  line-height: 1.4;
  white-space: pre-wrap;
}

.message-time {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
  text-align: right;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-panel {
  width: 220px;
  background: white;
  border-left: 1px solid #E4E7ED;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.member-title {
  padding: 16px;
  border-bottom: 1px solid #E4E7ED;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.member-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.member-item {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
}

.member-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.member-msg-count {
  font-size: 12px;
  color: #C0C4CC;
  flex-shrink: 0;
}

.member-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #C0C4CC;
  flex-shrink: 0;
}

.member-dot.online {
  background: #F56C6C;
}

.member-msg-total {
  padding: 6px 16px;
  font-size: 12px;
  color: #909399;
  border-bottom: 1px solid #F2F2F2;
}

.upload-btn {
  width: 36px;
  height: 36px;
  font-size: 20px;
  font-weight: 600;
  padding: 0;
  border-radius: 50%;
  flex-shrink: 0;
}

.upload-btn.is-loading {
  opacity: 0.6;
  pointer-events: none;
}

.at-btn {
  width: 36px;
  height: 36px;
  font-size: 18px;
  font-weight: 700;
  padding: 0;
  border-radius: 50%;
  flex-shrink: 0;
  color: #409EFF;
}

.message-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  display: block;
  cursor: pointer;
}

.thinking-dot {
  width: 8px;
  height: 8px;
  background: #F56C6C;
  border-radius: 50%;
  animation: thinking-bounce 1.2s ease-in-out infinite;
}

.thinking-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.thinking-content {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 24px;
}

.chat-input {
  background: white;
  padding: 16px 24px;
  border-top: 1px solid #E4E7ED;
  display: flex;
  gap: 12px;
  align-items: center;
}

.chat-textarea {
  flex: 1;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  line-height: 1.5;
  white-space: pre-wrap;
  transition: border-color 0.2s;
}

.chat-textarea:focus {
  border-color: #409EFF;
}
</style>