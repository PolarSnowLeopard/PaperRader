import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'WorkspaceList', component: () => import('../views/WorkspaceList.vue') },
  { path: '/ws/:id', name: 'WorkspaceMain', component: () => import('../views/WorkspaceMain.vue') },
  { path: '/ws/:id/paper/:pid', name: 'PaperDetail', component: () => import('../views/PaperDetail.vue') },
  { path: '/ws/:id/search', name: 'Search', component: () => import('../views/Search.vue') },
  { path: '/ws/:id/import', name: 'Import', component: () => import('../views/Import.vue') },
  { path: '/ws/:id/chat', name: 'Chat', component: () => import('../views/Chat.vue') },
  { path: '/conference', name: 'Conference', component: () => import('../views/Conference.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
