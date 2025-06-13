import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth';

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
      component: () => import('../views/chat.vue'),
      meta: { requiresAuth: true } 
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      redirect: '/',
    }
  ],
})

// check login
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth) {
    if (authStore.isAuthenticated) {
      next();
    } else {
      next({
        path: '/login',
        query: { redirect: to.fullPath } // return to the original page with params
      });
    }
  } else {
    if (to.path === '/login' && authStore.isAuthenticated) {
      next('/'); // if already logged in, return to homepage
    } else {
      next();
    }
  }
});

export default router
