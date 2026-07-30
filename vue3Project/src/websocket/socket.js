let ws = null
let onMessageCallback = null
let onStatusCallback = null
let reconnectTimer = null
let savedRoomId = ''
let savedToken = ''
let reconnectAttempts = 0
const MAX_RECONNECT = 10

function connect() {
  if (!savedRoomId || !savedToken) {
    console.warn('WebSocket: missing roomId or token')
    return
  }

  const encoded = encodeURIComponent(savedToken)
  const url = `ws://127.0.0.1:8000/ws/chat/${savedRoomId}?token=${encoded}`
  console.log('WebSocket connecting:', url)

  ws = new WebSocket(url)

  const timeout = setTimeout(() => {
    if (ws && ws.readyState === 0) {
      ws.close()
      ws = null
      console.warn('WebSocket connection timed out')
      if (onStatusCallback) onStatusCallback(false)
      scheduleReconnect()
    }
  }, 5000)

  ws.onopen = () => {
    clearTimeout(timeout)
    console.log('WebSocket connected')
    reconnectAttempts = 0
    if (onStatusCallback) onStatusCallback(true)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('WebSocket receive:', data)
      if (onMessageCallback) onMessageCallback(data)
    } catch (e) {
      console.error('WebSocket message parse error:', e)
    }
  }

  ws.onerror = () => {
    clearTimeout(timeout)
    console.error('WebSocket error')
  }

  ws.onclose = (event) => {
    clearTimeout(timeout)
    console.log('WebSocket closed:', event.code, event.reason)
    if (onStatusCallback) onStatusCallback(false)
    ws = null
    if (event.code !== 1000) scheduleReconnect()
  }
}

function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT) return
  reconnectAttempts++
  const delay = Math.min(1000 * reconnectAttempts, 10000)
  console.log(`WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttempts})`)
  clearTimeout(reconnectTimer)
  reconnectTimer = setTimeout(connect, delay)
}

export function createSocket(roomId, token, onMessage, onStatus) {
  closeSocket()
  savedRoomId = roomId
  savedToken = token
  onMessageCallback = onMessage
  onStatusCallback = onStatus
  reconnectAttempts = 0
  connect()
}

function send(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    const json = JSON.stringify(data)
    console.log('WebSocket send:', json)
    ws.send(json)
    return true
  }
  console.warn('WebSocket not open, state:', ws ? ws.readyState : 'null')
  return false
}

export function sendMessage(content) {
  return send({ type: 'message', content })
}

export function sendAgentMessage(content) {
  return send({ type: 'agent_message', agent: 'cognitive', content })
}

export function sendImage(url) {
  return send({ type: 'image', content: url })
}

export function closeSocket() {
  clearTimeout(reconnectTimer)
  reconnectTimer = null
  if (ws) {
    ws.onopen = null
    ws.onmessage = null
    ws.onerror = null
    ws.onclose = null
    ws.close()
    ws = null
  }
  savedRoomId = ''
  savedToken = ''
  onMessageCallback = null
  onStatusCallback = null
  reconnectAttempts = MAX_RECONNECT
}
