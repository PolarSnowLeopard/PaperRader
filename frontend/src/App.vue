<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  HomeOutlined,
  ReadOutlined,
  SearchOutlined,
  BarChartOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const selectedKeys = ref(['home'])
const collapsed = ref(false)

const menuItems = [
  { key: 'home', icon: HomeOutlined, label: '总览', path: '/' },
  { key: 'feed', icon: ReadOutlined, label: '论文流', path: '/feed' },
  { key: 'search', icon: SearchOutlined, label: '智能搜索', path: '/search' },
  { key: 'stats', icon: BarChartOutlined, label: '趋势统计', path: '/stats' },
]

function onMenuClick({ key }) {
  const item = menuItems.find((m) => m.key === key)
  if (item) router.push(item.path)
}
</script>

<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="light">
      <div style="height: 48px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; color: #1677ff;">
        {{ collapsed ? 'PR' : 'PaperRader' }}
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        mode="inline"
        @click="onMenuClick"
      >
        <a-menu-item v-for="item in menuItems" :key="item.key">
          <component :is="item.icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-content style="padding: 24px; background: #f5f5f5;">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>
