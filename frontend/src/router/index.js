import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/feed', name: 'Feed', component: () => import('../views/Feed.vue') },
  { path: '/search', name: 'Search', component: () => import('../views/Search.vue') },
  { path: '/stats', name: 'Stats', component: () => import('../views/Stats.vue') },
  { path: '/paper/:id', name: 'PaperDetail', component: () => import('../views/PaperDetail.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
