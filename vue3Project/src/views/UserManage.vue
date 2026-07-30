<template>
  <div class="user-manage-container">
    <h3 class="page-title">用户管理</h3>
    <div class="search-bar">
      <el-input
        v-model="searchId"
        placeholder="搜索用户名"
        clearable
        style="width: 200px"
        @keyup.enter="handleSearch"
        @clear="handleReset"
      />
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <el-table :data="userList" border stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" type="index" width="80" />
      <el-table-column prop="username" label="用户名" min-width="150" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="{ row }">
          <el-popconfirm
            title="确认删除该用户？"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[50]"
        layout="total, prev, pager, next"
        @current-change="fetchUsers"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUsersList, deleteUser } from '../api/user'

const loading = ref(false)
const userList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const searchId = ref('')

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    const res = await getUsersList(params)

    let list = res.users || res.items || res.data || []

    if (searchId.value.trim()) {
      list = list.filter(user =>
        String(user.username).includes(searchId.value.trim())
      )
    }

    userList.value = list
    total.value = list.length
  } catch (error) {
    ElMessage.error(error.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleReset = () => {
  searchId.value = ''
  currentPage.value = 1
  fetchUsers()
}

const handleDelete = async (userId) => {
  try {
    await deleteUser(userId)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.user-manage-container {
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

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
