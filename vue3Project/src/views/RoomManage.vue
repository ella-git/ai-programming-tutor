<template>
  <div class="room-manage-container">
  <h3 class="page-title">房间管理</h3>
    <el-table :data="rooms" border stripe v-loading="loading">
      <el-table-column prop="room_code" label="房间号" min-width="120" />
      
      <el-table-column label="操作" width="320" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleExport(row)">导出聊天记录</el-button>
          <el-button type="danger" size="small" @click="handleClear(row)">清除消息</el-button>
          <el-button type="danger" size="small" @click="handleDeleteRoom(row)">删除房间</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoomList, exportMessages, clearMessages, deleteRoom } from '../api/room'

const loading = ref(false)
const rooms = ref([])



const handleClear = async (room) => {
  try {
    await ElMessageBox.confirm(`确定清除房间 ${room.room_code} 的所有消息吗？此操作不可恢复。`, '确认清除', {
      confirmButtonText: '确认清除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await clearMessages(room.room_id)
    ElMessage.success('消息已清除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('清除失败')
  }
}

const handleDeleteRoom = async (room) => {
  try {
    await ElMessageBox.confirm(`确定删除房间 ${room.room_code} 吗？此操作不可恢复。`, '确认删除', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteRoom(room.room_id)
    rooms.value = rooms.value.filter(r => r.room_id !== room.room_id)
    ElMessage.success('房间已删除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleExport = async (room) => {
  try {
    loading.value = true
    const blob = await exportMessages(room.room_id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${room.room_code}_messages.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('导出失败:', err)
    ElMessage.error(err.message || '导出失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getRoomList()
    rooms.value = Array.isArray(res) ? res : (res.rooms || res.data || [])
  } catch {
    rooms.value = []
  }
  loading.value = false
})
</script>

<style scoped>
.room-manage-container {
  background: white;
  border-radius: 8px;
  padding: 24px;
}

.page-title {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
</style>
