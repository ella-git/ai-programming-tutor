<template>
  <div class="join-room-container">
    <div class="room-card">
      <h3>加入聊天室</h3>
      <el-form :model="roomForm" label-width="80px" @submit.prevent="joinRoom">
        <el-form-item label="号码">
          <el-input v-model="roomForm.code" placeholder="请输入聊天室号码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" native-type="submit">加入聊天室</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { enterRoom } from '../api/room'

const router = useRouter()
const loading = ref(false)
const roomForm = reactive({
  code: ''
})

const joinRoom = async () => {
  if (!roomForm.code.trim()) {
    ElMessage.warning('请输入聊天室号码')
    return
  }

  loading.value = true
  try {
    const res = await enterRoom({ room_code: roomForm.code })
    localStorage.setItem('room_id', res.room_id)
    localStorage.setItem('room_code', roomForm.code)
    ElMessage.success('成功加入聊天室')
    router.push('/home/chat-room')
  } catch (error) {
    ElMessage.error(error.message || '加入聊天室失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.join-room-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #F7F8FA;
}

.room-card {
  width: 400px;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.room-card h3 {
  text-align: center;
  margin-bottom: 24px;
  color: #333333;
  font-size: 20px;
  font-weight: 600;
}
</style>