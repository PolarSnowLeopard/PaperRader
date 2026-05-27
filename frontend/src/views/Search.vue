<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchPapers } from '../api/search'
import { ArrowLeftOutlined } from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const wsId = Number(route.params.id)
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
    const res = await searchPapers({ query: query.value, limit: 15, workspace_id: wsId })
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

function openPaper(paper) {
  router.push(`/ws/${wsId}/paper/${paper.id}`)
}

function goBack() {
  router.push(`/ws/${wsId}`)
}
</script>

<template>
  <div class="search-page">
    <!-- Hero search section -->
    <div class="search-hero">
      <a-button type="text" class="search-back-btn" @click="goBack">
        <template #icon><arrow-left-outlined /></template>
        返回
      </a-button>
      <h1 class="search-title">智能搜索</h1>
      <p class="search-subtitle">用自然语言描述你想找的论文</p>
      <div class="search-input-wrapper">
        <a-input-search
          v-model:value="query"
          placeholder="如：关于 LLM agent 的最新进展..."
          enter-button="搜索"
          size="large"
          :loading="loading"
          @search="doSearch"
          class="search-input"
        />
      </div>
    </div>

    <!-- Results -->
    <div class="search-results">
      <div v-if="interpretation" class="search-meta fade-in">
        <div class="meta-interpretation">
          <a-tag color="purple" :bordered="false">意图理解</a-tag>
          <span>{{ interpretation }}</span>
        </div>
        <span class="meta-stats">
          扫描 {{ totalCandidates }} 篇候选 | 耗时 {{ searchTime }}ms
        </span>
      </div>

      <div class="results-list">
        <div
          v-for="item in results" :key="item.paper.id"
          class="result-card card-hover"
          @click="openPaper(item.paper)"
        >
          <div class="result-score">
            <span class="score-value">{{ item.score.toFixed(1) }}</span>
          </div>
          <div class="result-content">
            <h3 class="result-title">{{ item.paper.title }}</h3>
            <p class="result-reason">{{ item.reason }}</p>
            <div class="result-meta">
              <a-tag v-if="item.paper.venue" color="blue" :bordered="false" size="small">{{ item.paper.venue }}</a-tag>
              <a-tag v-if="item.paper.year" :bordered="false" size="small">{{ item.paper.year }}</a-tag>
              <span class="result-authors">{{ (item.paper.authors || []).slice(0, 3).join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!results.length && !loading && query" class="no-results fade-in">
        <p>没有找到匹配的论文</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  min-height: calc(100vh - var(--header-height));
}

/* --- Hero --- */
.search-hero {
  background: linear-gradient(135deg, #1e1e2e 0%, #2d1b69 40%, #4338ca 100%);
  padding: 40px 24px 48px;
  text-align: center;
  position: relative;
}

.search-back-btn {
  position: absolute;
  top: 16px;
  left: 24px;
  color: rgba(255, 255, 255, 0.6) !important;
  font-size: 13px;
}

.search-back-btn:hover {
  color: #fff !important;
}

.search-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 6px;
}

.search-subtitle {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  margin: 0 0 28px;
}

.search-input-wrapper {
  max-width: 600px;
  margin: 0 auto;
}

:deep(.search-input .ant-input) {
  border-radius: var(--radius-md) !important;
  height: 46px;
  font-size: 15px;
}

:deep(.search-input .ant-btn) {
  background: var(--primary-gradient) !important;
  border: none !important;
  height: 46px;
  border-radius: 0 var(--radius-md) var(--radius-md) 0 !important;
  font-size: 15px;
  padding: 0 24px;
}

/* --- Results --- */
.search-results {
  max-width: 700px;
  margin: -16px auto 48px;
  padding: 0 24px;
  position: relative;
  z-index: 2;
}

.search-meta {
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-interpretation {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-stats {
  font-size: 12px;
  color: var(--text-tertiary);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-card {
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  padding: 16px 20px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.result-score {
  flex-shrink: 0;
}

.score-value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--primary-gradient);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
  line-height: 1.4;
}

.result-reason {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 10px;
  line-height: 1.5;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.result-authors {
  font-size: 12px;
  color: var(--text-tertiary);
}

.no-results {
  text-align: center;
  padding: 60px 0;
  color: var(--text-tertiary);
}
</style>
