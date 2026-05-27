<script setup>
import { useRouter, useRoute } from 'vue-router'
import { BookOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
</script>

<template>
  <a-layout class="app-layout">
    <a-layout-header class="app-header">
      <div class="header-brand" @click="router.push('/')">
        <div class="brand-icon">
          <book-outlined />
        </div>
        <span class="brand-text">PaperRader</span>
      </div>
      <div style="flex: 1" />
      <a-button class="header-nav-btn" type="text" @click="router.push('/conference')">
        会议监控
      </a-button>
    </a-layout-header>
    <a-layout-content class="app-content">
      <router-view />
    </a-layout-content>
  </a-layout>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #1e1e2e 0%, #2d1b69 50%, #1e1e2e 100%) !important;
  padding: 0 24px !important;
  display: flex;
  align-items: center;
  height: var(--header-height) !important;
  line-height: var(--header-height) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 1px 12px rgba(0, 0, 0, 0.2);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.header-brand:hover {
  opacity: 0.85;
}

.brand-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #c4b5fd 0%, #a78bfa 50%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-nav-btn {
  color: rgba(255, 255, 255, 0.7) !important;
  font-size: 13px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.header-nav-btn:hover {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.1) !important;
}

.app-content {
  background: var(--bg-page);
}
</style>
