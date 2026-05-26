<script setup>
import { ref, onMounted } from 'vue'
import { getOverview } from '../api/stats'
import { triggerArxivSync, triggerDblpSync } from '../api/sync'
import { message } from 'ant-design-vue'

const stats = ref({ total_papers: 0, sources: {}, recent_week: 0, starred_count: 0 })
const syncing = ref(false)

onMounted(async () => {
  stats.value = await getOverview()
})

async function syncArxiv() {
  syncing.value = true
  try {
    await triggerArxivSync()
    message.success('arXiv 采集已启动（后台运行）')
  } catch (e) {
    message.error('采集失败')
  } finally {
    syncing.value = false
  }
}

async function syncDblp() {
  syncing.value = true
  try {
    const res = await triggerDblpSync()
    message.success(`DBLP 采集完成，新增 ${res.papers_added} 篇`)
    stats.value = await getOverview()
  } catch (e) {
    message.error('采集失败')
  } finally {
    syncing.value = false
  }
}
</script>

<template>
  <div>
    <a-page-header title="PaperRader" sub-title="科研论文助手">
      <template #extra>
        <a-button @click="syncArxiv" :loading="syncing">采集 arXiv</a-button>
        <a-button @click="syncDblp" :loading="syncing">采集 DBLP</a-button>
      </template>
    </a-page-header>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="6">
        <a-statistic title="论文总数" :value="stats.total_papers" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="本周新增" :value="stats.recent_week" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="已收藏" :value="stats.starred_count" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="数据源" :value="Object.keys(stats.sources).length" />
      </a-col>
    </a-row>

    <a-card title="数据源分布" style="margin-top: 24px">
      <a-tag v-for="(count, source) in stats.sources" :key="source" color="blue">
        {{ source }}: {{ count }}
      </a-tag>
    </a-card>
  </div>
</template>
