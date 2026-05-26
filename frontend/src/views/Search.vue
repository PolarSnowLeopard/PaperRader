<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchPapers } from '../api/search'
import { SearchOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const query = ref('')
const results = ref([])
const interpretation = ref('')
const searchTime = ref(0)
const totalCandidates = ref(0)
const loading = ref(false)

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  results.value = []
  try {
    const res = await searchPapers({ query: query.value, limit: 15 })
    results.value = res.results
    interpretation.value = res.query_interpretation
    searchTime.value = res.search_time_ms
    totalCandidates.value = res.total_candidates
  } catch (e) {
    results.value = []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <a-page-header title="智能搜索" sub-title="LLM 驱动的语义检索" />

    <a-input-search
      v-model:value="query"
      placeholder="用自然语言描述你想找的论文，如：最近关于 LLM agent 的强化学习论文"
      enter-button="搜索"
      size="large"
      :loading="loading"
      @search="doSearch"
      style="max-width: 700px; margin-bottom: 24px"
    />

    <div v-if="interpretation" style="margin-bottom: 16px; color: #666">
      <a-tag color="blue">意图理解</a-tag> {{ interpretation }}
      <span style="margin-left: 16px; font-size: 12px; color: #999">
        扫描 {{ totalCandidates }} 篇候选 | 耗时 {{ searchTime }}ms
      </span>
    </div>

    <a-list :data-source="results" :loading="loading">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta>
            <template #title>
              <a-space>
                <a-tag color="magenta">{{ item.score.toFixed(2) }}</a-tag>
                <a @click="router.push(`/paper/${item.paper.id}`)" style="cursor: pointer">
                  {{ item.paper.title }}
                </a>
              </a-space>
            </template>
            <template #description>
              <div>{{ item.reason }}</div>
              <a-space style="margin-top: 4px">
                <a-tag v-if="item.paper.venue" color="blue">{{ item.paper.venue }}</a-tag>
                <a-tag v-if="item.paper.year">{{ item.paper.year }}</a-tag>
                <span style="color: #999; font-size: 12px">
                  {{ (item.paper.authors || []).slice(0, 3).join(', ') }}
                </span>
              </a-space>
            </template>
          </a-list-item-meta>
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>
