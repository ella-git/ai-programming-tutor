<template>
  <div class="home-container">
    <div class="top-bar">
      <div class="top-bar-left">
       
        <span class="app-title">智能体编程系统</span>
         <el-button text @click="toggleSidebar" class="toggle-btn">
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
      </div>
      <div class="top-bar-right">
        <span class="welcome-text">欢迎 {{ username }}</span>
        <el-button type="danger" size="small" @click="handleLogout">退出登录</el-button>
      </div>
    </div>
    <div class="layout-body">
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
     
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="join-room">
          <el-icon><ChatDotRound /></el-icon>
          <span>协作讨论</span>
        </el-menu-item>
        <el-menu-item index="room-manage">
          <el-icon><Document /></el-icon>
          <span>房间管理</span>
        </el-menu-item>
        <el-menu-item index="user-manage">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="setting">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </div>
    
    <div class="main-content">
      <router-view />
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Setting, Fold, Expand, User, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const username = ref(localStorage.getItem('username') || '用户')
const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const activeMenu = computed(() => route.path.split('/').pop() || 'join-room')

const handleMenuSelect = (index) => {
  router.push(`/home/${index}`)
}

const handleLogout = async () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #F7F8FA;
}

.top-bar {
  height: 60px;
  background: white;
  border-bottom: 1px solid #E4E7ED;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-btn {
  font-size: 20px;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: #333333;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome-text {
  font-size: 14px;
  color: #606266;
}

.layout-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #E4E7ED;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 0;
  border-right: none;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #E4E7ED;
}

.sidebar-header h3 {
  margin: 0;
  color: #333333;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  flex: 1;
  border: none;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
  color: #333333;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: #F5F7FA;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #409EFF;
  color: white;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>