import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/LoginPage.vue';
import AskMePage from '../views/AskMePage.vue';

function isAuthenticated() {
  return localStorage.getItem('userIsAuthenticated') === 'true';
}

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage
  },
  {
    path: '/ask-me',
    name: 'AskMePage',
    component: AskMePage,
    meta: {
      requiresAuth: true
    }
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated()) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;


