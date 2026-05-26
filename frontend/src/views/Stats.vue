<script setup>
import { ref, onMounted } from 'vue'
import { getOverview, getVenues, getTopics } from '../api/stats'

const overview = ref({})
const venues = ref([])
const topics = ref([])

onMounted(async () => {
  const [ov, ve, tp] = await Promise.all([getOverview(), getVenues(), getTopics()])
  overview.value = ov
  venues.value = ve.venues
  topics.value = tp.topics
})
</script>

<template>
  <div>
    <a-page-header title="趋势统计" sub-title="论文收录数据概览" />

    <a-row :gutter="16">
      <a-col :span="12">
        <a-card title="会议/期刊分布">
          <a-table
            :data-source="venues"
            :columns="[
              { title: '会议', dataIndex: 'venue', key: 'venue' },
              { title: '论文数', dataIndex: 'count', key: 'count', sorter: (a, b) => a.count - b.count },
            ]"
            :pagination="false"
            size="small"
          />
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="类目分布 (arXiv categories)">
          <a-table
            :data-source="topics"
            :columns="[
              { title: '类目', dataIndex: 'topic', key: 'topic' },
              { title: '论文数', dataIndex: 'count', key: 'count', sorter: (a, b) => a.count - b.count },
            ]"
            :pagination="false"
            size="small"
          />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>
