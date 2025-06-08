import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('../views/main.vue')
    },
    {
      path: '/login',
      component: () => import('../views/login.vue')
    },
    {
      path: '/chat',
      component: () => import('../views/chat.vue')
    },
  ],
})

export default router
