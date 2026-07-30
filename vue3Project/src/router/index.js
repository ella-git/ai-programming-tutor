import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'
import JoinRoom from '../views/JoinRoom.vue'
import ChatRoom from '../views/ChatRoom.vue'
import Setting from '../views/Setting.vue'
import UserManage from '../views/UserManage.vue'
import RoomManage from '../views/RoomManage.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    redirect: '/home/join-room',
    children: [
      {
        path: 'join-room',
        name: 'JoinRoom',
        component: JoinRoom
      },
      {
        path: 'chat-room',
        name: 'ChatRoom',
        component: ChatRoom
      },
      {
        path: 'setting',
        name: 'Setting',
        component: Setting
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: UserManage
      },
      {
        path: 'room-manage',
        name: 'RoomManage',
        component: RoomManage
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('token')
  
  if (to.path === '/login' || to.path === '/register') {
    if (isAuthenticated) {
      next('/home')
    } else {
      next()
    }
  } else {
    if (isAuthenticated) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router