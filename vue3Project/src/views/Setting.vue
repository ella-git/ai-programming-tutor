<template>
  <div class="setting-container">
    <div class="setting-tabs">
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="知识库管理" name="knowledge">
          <div class="setting-card">
            <h3>知识库管理</h3>
            <KnowledgeUpload />
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="Prompt设置" name="prompt">
          <div class="setting-card">
            <h3>认知智能体 — Prompt 管理</h3>
            <el-form label-width="120px">
              <el-form-item label="Prompt1">
                <el-upload
                  class="upload-demo"
                  drag
                  :auto-upload="false"
                  accept=".txt"
                  :on-change="(file) => handlePromptFileChange(file, 1)"
                  :file-list="prompt1FileList"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">
                    将 .txt 文件拖拽到此处，或<em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      仅支持 UTF-8 编码的 .txt 文件，单个文件不超过10MB
                    </div>
                  </template>
                </el-upload>
                <div v-if="prompt1File" class="file-info">
                  <el-icon><document /></el-icon>
                  <span>{{ prompt1File.name }}</span>
                  <el-button type="danger" size="small" @click="removePromptFile(1)">移除</el-button>
                </div>
                <el-button
                  type="primary"
                  :disabled="!selectedFile1 || uploading1"
                  :loading="uploading1"
                  style="margin-top:12px"
                  @click="submitUpload"
                >
                  上传到服务器
                </el-button>
              </el-form-item>

            </el-form>
          </div>

          <div class="setting-card" style="margin-top:20px">
            <h3>元认知智能体 — Prompt 管理</h3>
            <el-form label-width="120px">
              <el-form-item label="Prompt3">
                <el-upload
                  class="upload-demo"
                  drag
                  :auto-upload="false"
                  accept=".txt"
                  :on-change="(file) => handlePromptFileChange(file, 3)"
                  :file-list="prompt3FileList"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">
                    将 .txt 文件拖拽到此处，或<em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      仅支持 UTF-8 编码的 .txt 文件，单个文件不超过10MB
                    </div>
                  </template>
                </el-upload>
                <div v-if="prompt3File" class="file-info">
                  <el-icon><document /></el-icon>
                  <span>{{ prompt3File.name }}</span>
                  <el-button type="danger" size="small" @click="removePromptFile(3)">移除</el-button>
                </div>
                <el-button
                  type="primary"
                  :disabled="!selectedFile3 || uploading3"
                  :loading="uploading3"
                  style="margin-top:12px"
                  @click="submitMetaUpload"
                >
                  上传到服务器
                </el-button>
              </el-form-item>
            </el-form>
          </div>

        </el-tab-pane>
        <el-tab-pane label="语义分析设置" name="semantic">
          <SemanticSetting />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import { getPrompt, uploadPrompt } from '../api/agent'
import KnowledgeUpload from '../components/KnowledgeUpload.vue'
import SemanticSetting from '../components/SemanticSetting.vue'

const activeTab = ref('prompt')

// Prompt相关
const currentPrompt = ref(null)
const prompt1FileList = ref([])
const prompt3FileList = ref([])
const prompt1File = ref(null)
const prompt3File = ref(null)
const selectedFile1 = ref(null)
const selectedFile3 = ref(null)
const uploading1 = ref(false)
const uploading3 = ref(false)


const formatTime = (isoStr) => {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN', { hour12: false })
}

const fetchPrompt = async () => {
  try {
    const res = await getPrompt('cognitive')
    currentPrompt.value = res
    if (res?.filename) {
      prompt1File.value = {
        name: res.filename,
        size: 0,
        uploadTime: res.updated_time ? formatTime(res.updated_time) : '-'
      }
    }
  } catch {
    currentPrompt.value = null
  }
}

// Prompt文件上传处理
const handlePromptFileChange = (file, index) => {
  if (!file.name.endsWith('.txt')) {
    ElMessage.warning('仅支持 .txt 文件')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  const fileData = {
    name: file.name,
    size: file.size,
    uploadTime: new Date().toLocaleString()
  }
  if (index === 1) {
    selectedFile1.value = file.raw || file
    prompt1File.value = fileData
  } else {
    selectedFile3.value = file.raw || file
    prompt3File.value = fileData
  }
  return false
}

const removePromptFile = (index) => {
  if (index === 1) {
    prompt1File.value = null
    selectedFile1.value = null
    prompt1FileList.value = []
  } else {
    prompt3File.value = null
    selectedFile3.value = null
    prompt3FileList.value = []
  }
  ElMessage.success(`Prompt${index} 文件移除成功`)
}

const fetchMetaPrompt = async () => {
  try {
    const res = await getPrompt('metacognitive')
    if (res?.filename) {
      prompt3File.value = {
        name: res.filename,
        size: 0,
        uploadTime: res.updated_time ? formatTime(res.updated_time) : '-'
      }
    }
  } catch {
    prompt3File.value = null
  }
}

const submitMetaUpload = async () => {
  const file = selectedFile3.value
  if (!file) return
  uploading3.value = true
  try {
    await uploadPrompt('metacognitive', file)
    ElMessage.success('元认知提示词上传成功')
    removePromptFile(3)
    await fetchMetaPrompt()
  } catch (e) {
    ElMessage.error('上传失败：' + (e.message || '未知错误'))
  } finally {
    uploading3.value = false
  }
}

const submitUpload = async () => {
  const file = selectedFile1.value
  if (!file) return
  uploading1.value = true
  try {
    await uploadPrompt('cognitive', file)
    ElMessage.success('提示词上传成功，所有聊天室立即生效')
    removePromptFile(1)
    await fetchPrompt()
  } catch (e) {
    ElMessage.error('上传失败：' + (e.message || '未知错误'))
  } finally {
    uploading1.value = false
  }
}

onMounted(() => {
  fetchPrompt()
  fetchMetaPrompt()
})
</script>

<style scoped>
.setting-container {
  height: 100%;
  background-color: #F7F8FA;
  padding: 20px;
}

.setting-tabs {
  max-width: 800px;
  margin: 0 auto;
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



</style>