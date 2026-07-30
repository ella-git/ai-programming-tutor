<template>
  <div class="semantic-setting">
    <div class="setting-card">
      <h3>检测周期设置</h3>
      <el-form label-width="120px">
        <el-form-item label="检测周期（秒）">
          <el-input-number
            v-model="intervalSeconds"
            :min="1"
            :max="3600"
            style="width:200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="saving"
            :disabled="saving"
            @click="handleSaveConfig"
          >
            保存
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="setting-card" style="margin-top:20px">
      <h3>关键词管理</h3>
      <div class="add-keyword-row">
        <el-input
          v-model="newKeyword"
          placeholder="输入关键词"
          style="width:300px"
          @keyup.enter="handleAddKeyword"
        />
        <el-button
          type="primary"
          :disabled="!newKeyword.trim() || adding"
          :loading="adding"
          @click="handleAddKeyword"
        >
          添加关键词
        </el-button>
      </div>
      <div v-if="loading" class="list-loading">加载中...</div>
      <div v-else-if="keywords.length === 0" class="list-empty">暂无关键词</div>
      <div v-else class="keyword-list">
        <div v-for="item in keywords" :key="item.id" class="keyword-item">
          <el-icon><Collection /></el-icon>
          <span class="keyword-text">{{ item.keyword }}</span>
          <span class="keyword-time">添加时间：{{ item.created_at ? formatTime(item.created_at) : '-' }}</span>
          <el-button
            type="danger"
            size="small"
            @click="handleDeleteKeyword(item.id, item.keyword)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Collection } from '@element-plus/icons-vue'
import { getSemanticConfig, saveSemanticConfig, addKeyword, deleteKeyword } from '../api/semantic'

const intervalSeconds = ref(20)
const saving = ref(false)
const keywords = ref([])
const newKeyword = ref('')
const adding = ref(false)
const loading = ref(false)

const formatTime = (isoStr) => {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN', { hour12: false })
}

const fetchConfig = async () => {
  loading.value = true
  try {
    const res = await getSemanticConfig()
    intervalSeconds.value = res.interval_seconds
    keywords.value = Array.isArray(res.keywords) ? res.keywords : []
  } catch {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const handleSaveConfig = async () => {
  saving.value = true
  try {
    await saveSemanticConfig(intervalSeconds.value)
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败：' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleAddKeyword = async () => {
  const kw = newKeyword.value.trim()
  if (!kw) return
  adding.value = true
  try {
    await addKeyword(kw)
    ElMessage.success('添加成功')
    newKeyword.value = ''
    await fetchConfig()
  } catch (e) {
    ElMessage.error('添加失败：' + (e.message || '未知错误'))
  } finally {
    adding.value = false
  }
}

const handleDeleteKeyword = async (id, keyword) => {
  try {
    await deleteKeyword(id)
    ElMessage.success(`已删除 ${keyword}`)
    await fetchConfig()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.message || '未知错误'))
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<style scoped>
.semantic-setting {
  width: 100%;
}

.setting-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.setting-card h3 {
  text-align: center;
  margin-bottom: 24px;
  color: #333333;
  font-size: 20px;
  font-weight: 600;
}

.add-keyword-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.list-loading,
.list-empty {
  text-align: center;
  padding: 24px;
  color: #909399;
  font-size: 14px;
}

.keyword-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.keyword-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #F5F7FA;
  border-radius: 6px;
  transition: background 0.2s;
}

.keyword-item:hover {
  background: #ECF5FF;
}

.keyword-text {
  flex: 1;
  font-size: 14px;
  color: #333;
}

.keyword-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  min-width: 180px;
  text-align: right;
}
</style>
