<template>
  <div class="knowledge-upload">
    <div class="upload-area">
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :auto-upload="false"
        accept=".txt,.md,.pdf,.docx"
        :on-change="handleFileChange"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖拽到此处，或<em>点击选择</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 txt、md、pdf、docx 格式，单个文件不超过 50MB
          </div>
        </template>
      </el-upload>
      <div v-if="selectedFile" class="file-info">
        <el-icon><document /></el-icon>
        <span>{{ selectedFile.name }}</span>
        <el-button type="danger" size="small" @click="clearFile">移除</el-button>
      </div>
      <el-button
        type="primary"
        :disabled="!selectedFile || uploading"
        :loading="uploading"
        style="margin-top:12px"
        @click="submitUpload"
      >
        上传到服务器
      </el-button>
    </div>

    <el-divider />

    <div class="list-section">
      <div class="list-header">
        <span class="list-title">知识文件列表</span>
        <el-button size="small" @click="fetchList">刷新</el-button>
      </div>
      <div v-if="loading" class="list-loading">加载中...</div>
      <div v-else-if="fileListData.length === 0" class="list-empty">暂无知识文件</div>
      <div v-else class="file-list">
        <div v-for="item in fileListData" :key="item.id" class="file-item">
          <el-icon><document /></el-icon>
          <div class="file-item-info">
            <span class="file-item-name">{{ item.filename }}</span>
            <span class="file-item-type">.{{ item.file_type }}</span>
          </div>
          <span class="file-item-time">{{ formatTime(item.upload_time) }}</span>
          <div class="file-item-status">
            <span v-if="item.status === 'embedded'" class="status-badge status-done">
              <el-icon><CircleCheck /></el-icon> 向量化完成
            </span>
            <span v-else-if="item.status === 'processing'" class="status-badge status-processing">
              <el-icon class="status-spin"><Loading /></el-icon> 处理中
            </span>
            <span v-else-if="item.status === 'parse_failed' || item.status === 'failed'" class="status-badge status-failed">
              <el-icon><CircleClose /></el-icon> 处理失败
            </span>
            <span v-else class="status-badge status-pending">
              等待处理
            </span>
          </div>
          <el-button type="danger" size="small" @click="handleDelete(item.id, item.filename)">删除</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { uploadKnowledgeFile, getKnowledgeList, deleteKnowledgeFile, getEmbeddingStatus } from '../api/knowledge'

const uploadRef = ref(null)
const fileList = ref([])
const selectedFile = ref(null)
const uploading = ref(false)
const fileListData = ref([])
const loading = ref(false)
const pollTimers = {}

const formatTime = (isoStr) => {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN', { hour12: false })
}

const handleFileChange = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['txt', 'md', 'pdf', 'docx'].includes(ext)) {
    ElMessage.warning('不支持的文件格式')
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  selectedFile.value = file.raw || file
  return false
}

const clearFile = () => {
  selectedFile.value = null
  fileList.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const submitUpload = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const res = await uploadKnowledgeFile(selectedFile.value)
    ElMessage.success('上传成功')
    clearFile()
    const list = await getKnowledgeList()
    fileListData.value = updateListWithStatus(Array.isArray(list) ? list : [])
    const uploaded = fileListData.value[0]
    if (uploaded && (uploaded.status === 'processing')) {
      startPolling(uploaded.id, uploaded.filename)
    }
  } catch (e) {
    ElMessage.error('上传失败：' + (e.message || '未知错误'))
  } finally {
    uploading.value = false
  }
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getKnowledgeList()
    fileListData.value = updateListWithStatus(Array.isArray(res) ? res : [])
  } catch {
    fileListData.value = []
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id, filename) => {
  stopPolling(id)
  try {
    await deleteKnowledgeFile(id)
    ElMessage.success(`已删除 ${filename}`)
    await fetchList()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.message || '未知错误'))
  }
}

const refreshFileStatus = async (fileId, fileName) => {
  try {
    const res = await getEmbeddingStatus(fileId)
    const item = fileListData.value.find(f => f.id === fileId)
    if (!item) return
    if (res.status === 'completed') {
      item.status = 'embedded'
      delete pollTimers[fileId]
      ElMessage.success(`${fileName} 向量化完成`)
    } else if (res.status === 'processing' || res.status === 'no_chunks') {
      item.status = 'processing'
    }
  } catch {
    const item = fileListData.value.find(f => f.id === fileId)
    if (item) item.status = 'failed'
    delete pollTimers[fileId]
  }
}

const startPolling = (fileId, fileName) => {
  if (pollTimers[fileId]) return
  pollTimers[fileId] = setInterval(() => {
    refreshFileStatus(fileId, fileName)
  }, 5000)
}

const stopPolling = (fileId) => {
  if (pollTimers[fileId]) {
    clearInterval(pollTimers[fileId])
    delete pollTimers[fileId]
  }
}

const updateListWithStatus = (list) => {
  for (const item of list) {
    if (item.status === 'uploaded' || item.status === 'parsed') {
      item.status = 'processing'
      startPolling(item.id, item.filename)
    }
  }
  return list
}

onMounted(() => {
  fetchList()
})

onBeforeUnmount(() => {
  for (const key of Object.keys(pollTimers)) {
    clearInterval(pollTimers[key])
  }
})
</script>

<style scoped>
.knowledge-upload {
  width: 100%;
}

.upload-area {
  margin-bottom: 8px;
}

.upload-demo {
  width: 100%;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #F5F7FA;
  border-radius: 4px;
}

.list-section {
  margin-top: 8px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.list-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.list-loading,
.list-empty {
  text-align: center;
  padding: 24px;
  color: #909399;
  font-size: 14px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #F5F7FA;
  border-radius: 6px;
  transition: background 0.2s;
}

.file-item:hover {
  background: #ECF5FF;
}

.file-item-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.file-item-name {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item-type {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.file-item-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  min-width: 140px;
  text-align: right;
}

.file-item-status {
  flex-shrink: 0;
  min-width: 110px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.status-done {
  color: #67C23A;
  background: #F0F9EB;
}

.status-processing {
  color: #409EFF;
  background: #ECF5FF;
}

.status-failed {
  color: #F56C6C;
  background: #FEF0F0;
}

.status-pending {
  color: #909399;
  background: #F5F7FA;
}

.status-spin {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
