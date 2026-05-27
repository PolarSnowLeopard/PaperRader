<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { triggerOpenReviewSync, triggerAclSync, triggerDblpSync, getSyncLogs, getConferenceStats, batchImportToWorkspace } from '../api/sync'
import { getPapers } from '../api/papers'
import { getWorkspaces, getFolderTree } from '../api/workspace'
import { message } from 'ant-design-vue'
import { SyncOutlined, BarChartOutlined, ImportOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const loading = ref(false)
const papers = ref([])
const selectedConference = ref('')
const syncLogs = ref([])
const stats = ref(null)
const statsLoading = ref(false)

// Batch import state
const showImportModal = ref(false)
const workspaces = ref([])
const folderTree = ref([])
const selectedWorkspace = ref(null)
const selectedFolder = ref(null)
const importLimit = ref(50)
const importLoading = ref(false)

const openreviewConfs = [
  { label: 'ICML 2025', value: 'ICML2025' },
  { label: 'ICLR 2025', value: 'ICLR2025' },
  { label: 'NeurIPS 2025', value: 'NeurIPS2025' },
  { label: 'COLM 2025', value: 'COLM2025' },
  { label: 'ICML 2024', value: 'ICML2024' },
  { label: 'ICLR 2024', value: 'ICLR2024' },
  { label: 'NeurIPS 2024', value: 'NeurIPS2024' },
]

const aclConfs = [
  { label: 'ACL 2025', value: 'ACL2025' },
  { label: 'NAACL 2025', value: 'NAACL2025' },
  { label: 'EMNLP 2025', value: 'EMNLP2025' },
  { label: 'ACL 2024', value: 'ACL2024' },
  { label: 'EMNLP 2024', value: 'EMNLP2024' },
  { label: 'NAACL 2024', value: 'NAACL2024' },
  { label: 'COLING 2024', value: 'COLING2024' },
]

const customConf = ref('')

async function syncConference(conf) {
  loading.value = true
  selectedConference.value = conf
  try {
    const aclPrefixes = ['ACL', 'EMNLP', 'NAACL', 'EACL', 'COLING', 'FINDINGS']
    const isAcl = aclPrefixes.some(p => conf.toUpperCase().startsWith(p))
    if (isAcl) {
      await triggerAclSync(conf)
    } else {
      await triggerOpenReviewSync(conf)
    }
    message.success(`${conf} 同步已启动，请稍候刷新查看`)
    setTimeout(loadLogs, 3000)
  } catch {
    message.error('同步失败')
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  syncLogs.value = await getSyncLogs(10)
}
loadLogs()

async function loadStats(venue) {
  statsLoading.value = true
  stats.value = null
  try {
    stats.value = await getConferenceStats(venue)
    const res = await getPapers({ venue, page_size: 50 })
    papers.value = res.papers || []
  } catch {
    stats.value = null
  } finally {
    statsLoading.value = false
  }
}

async function openBatchImport(venue) {
  selectedConference.value = venue
  showImportModal.value = true
  workspaces.value = await getWorkspaces()
}

async function onWorkspaceChange(wsId) {
  selectedFolder.value = null
  if (wsId) {
    folderTree.value = await getFolderTree(wsId)
  } else {
    folderTree.value = []
  }
}

function transformTree(folders) {
  return folders.map(f => ({
    title: f.name,
    value: f.id,
    children: f.children?.length ? transformTree(f.children) : undefined,
  }))
}

async function handleBatchImport() {
  if (!selectedFolder.value) {
    message.warning('请选择目标文件夹')
    return
  }
  importLoading.value = true
  try {
    const res = await batchImportToWorkspace(selectedConference.value, selectedFolder.value, importLimit.value)
    message.success(`已导入 ${res.imported} 篇论文`)
    showImportModal.value = false
  } catch {
    message.error('导入失败')
  } finally {
    importLoading.value = false
  }
}
</script>

<template>
  <div class="conf-page">
    <div class="conf-container">
      <h2 class="conf-page-title">顶会论文采集与分析</h2>

      <!-- Sync cards -->
      <div class="sync-section">
        <div class="sync-card">
          <div class="sync-card-accent or"></div>
          <div class="sync-card-body">
            <h3 class="sync-card-title">OpenReview</h3>
            <p class="sync-card-desc">ICLR / NeurIPS / ICML</p>
            <div class="conf-buttons">
              <a-button
                v-for="conf in openreviewConfs"
                :key="conf.value"
                @click="syncConference(conf.value)"
                :loading="loading && selectedConference === conf.value"
                size="small"
                class="conf-btn"
              >
                <template #icon><sync-outlined /></template>
                {{ conf.label }}
              </a-button>
            </div>
          </div>
        </div>

        <div class="sync-card">
          <div class="sync-card-accent acl"></div>
          <div class="sync-card-body">
            <h3 class="sync-card-title">ACL Anthology</h3>
            <p class="sync-card-desc">ACL / EMNLP / NAACL</p>
            <div class="conf-buttons">
              <a-button
                v-for="conf in aclConfs"
                :key="conf.value"
                @click="syncConference(conf.value)"
                :loading="loading && selectedConference === conf.value"
                size="small"
                class="conf-btn"
              >
                <template #icon><sync-outlined /></template>
                {{ conf.label }}
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Custom sync -->
      <div class="custom-sync">
        <a-input-search
          v-model:value="customConf"
          placeholder="自定义会议 (如 NeurIPS2025, ACL2025)"
          enter-button="同步"
          @search="(v) => v && syncConference(v)"
          :loading="loading && selectedConference === customConf"
          style="max-width: 400px"
        />
      </div>

      <!-- Stats Section -->
      <div class="stats-card">
        <div class="stats-header">
          <h3 class="stats-title">会议分析</h3>
          <a-input-search
            placeholder="输入会议名 (如 ICLR, ACL)"
            enter-button="分析"
            style="width: 300px"
            @search="loadStats"
            :loading="statsLoading"
          />
        </div>

        <a-spin :spinning="statsLoading">
          <div v-if="stats && stats.total > 0" class="stats-content">
            <div class="stat-numbers">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">论文总数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ Object.keys(stats.categories).length }}</div>
                <div class="stat-label">领域类别</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.top_authors.length }}</div>
                <div class="stat-label">高产作者 (Top)</div>
              </div>
              <div class="stat-item stat-action">
                <a-button type="primary" @click="openBatchImport(stats.venue)" class="batch-import-btn">
                  <template #icon><import-outlined /></template>
                  批量导入
                </a-button>
              </div>
            </div>

            <div class="stats-detail">
              <div class="stats-col">
                <h4 class="stats-col-title">领域分布 (Top 15)</h4>
                <div v-for="(count, cat) in stats.categories" :key="cat" class="cat-row">
                  <a-tag color="blue" :bordered="false" size="small">{{ cat }}</a-tag>
                  <a-progress :percent="Math.round(count / stats.total * 100)" :stroke-width="6" style="flex: 1" size="small" :stroke-color="{ from: '#6366f1', to: '#8b5cf6' }" />
                  <span class="cat-count">{{ count }}</span>
                </div>
              </div>
              <div class="stats-col">
                <h4 class="stats-col-title">高产作者 (Top 20)</h4>
                <a-table
                  :data-source="stats.top_authors"
                  :columns="[
                    { title: '作者', dataIndex: 'name', key: 'name' },
                    { title: '论文数', dataIndex: 'count', key: 'count', width: 80 },
                  ]"
                  size="small"
                  :pagination="false"
                  :scroll="{ y: 300 }"
                  class="authors-table"
                />
              </div>
            </div>
          </div>
          <a-empty v-else-if="stats && stats.total === 0" description="暂无该会议论文数据，请先同步" />
        </a-spin>
      </div>

      <!-- Papers list -->
      <div v-if="papers.length" class="papers-card">
        <h3 class="section-title">论文列表</h3>
        <a-list :data-source="papers" size="small" :pagination="{ pageSize: 20 }">
          <template #renderItem="{ item }">
            <a-list-item class="paper-item">
              <a-list-item-meta>
                <template #title>
                  <span class="paper-title">{{ item.title }}</span>
                </template>
                <template #description>
                  <div class="paper-meta">
                    <a-tag v-if="item.venue" color="blue" :bordered="false" size="small">{{ item.venue }}</a-tag>
                    <a-tag v-if="item.year" :bordered="false" size="small">{{ item.year }}</a-tag>
                    <a-tag v-if="item.citation_count" color="orange" :bordered="false" size="small">引用 {{ item.citation_count }}</a-tag>
                    <span class="paper-authors">{{ (item.authors || []).slice(0, 3).join(', ') }}</span>
                  </div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </div>

      <!-- Sync Logs -->
      <div class="logs-card">
        <div class="logs-header">
          <h3 class="section-title">同步记录</h3>
          <a-button size="small" @click="loadLogs">刷新</a-button>
        </div>
        <a-table
          :data-source="syncLogs"
          :columns="[
            { title: '来源', dataIndex: 'source', key: 'source', width: 120 },
            { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
            { title: '新增', dataIndex: 'papers_added', key: 'added', width: 60 },
            { title: '时间', dataIndex: 'started_at', key: 'time' },
            { title: '错误', dataIndex: 'error_message', key: 'error', ellipsis: true },
          ]"
          size="small"
          :pagination="false"
          row-key="id"
          class="logs-table"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : record.status === 'failed' ? 'red' : 'blue'" :bordered="false">
                {{ record.status }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </div>

      <!-- Batch Import Modal -->
      <a-modal v-model:open="showImportModal" title="批量导入到工作空间" @ok="handleBatchImport" :confirm-loading="importLoading">
        <a-form layout="vertical" style="margin-top: 12px">
          <a-form-item label="会议">
            <a-input :value="selectedConference" disabled />
          </a-form-item>
          <a-form-item label="目标工作空间">
            <a-select v-model:value="selectedWorkspace" placeholder="选择工作空间" @change="onWorkspaceChange" style="width: 100%">
              <a-select-option v-for="ws in workspaces" :key="ws.id" :value="ws.id">{{ ws.name }}</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="目标文件夹" v-if="folderTree.length">
            <a-tree-select
              v-model:value="selectedFolder"
              :tree-data="transformTree(folderTree)"
              placeholder="选择文件夹"
              style="width: 100%"
            />
          </a-form-item>
          <a-form-item label="导入数量上限">
            <a-input-number v-model:value="importLimit" :min="10" :max="200" style="width: 100%" />
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </div>
</template>

<style scoped>
.conf-page {
  min-height: calc(100vh - var(--header-height));
  background: var(--bg-page);
  padding: 32px 24px;
}

.conf-container {
  max-width: 1100px;
  margin: 0 auto;
}

.conf-page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 24px;
}

/* --- Sync cards --- */
.sync-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.sync-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.sync-card-accent {
  height: 3px;
}

.sync-card-accent.or {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.sync-card-accent.acl {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}

.sync-card-body {
  padding: 20px;
}

.sync-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.sync-card-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0 0 14px;
}

.conf-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.conf-btn {
  border-radius: var(--radius-sm) !important;
  font-size: 12px;
}

.custom-sync {
  margin-bottom: 20px;
}

/* --- Stats --- */
.stats-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  margin-bottom: 20px;
}

.stats-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.stats-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.stat-numbers {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  background: var(--bg-inset);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--primary-gradient);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.stat-action {
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-action::before {
  display: none;
}

.batch-import-btn {
  border-radius: var(--radius-md) !important;
  background: var(--primary-gradient) !important;
  border: none !important;
}

.stats-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.stats-col-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}

.cat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.cat-count {
  font-size: 12px;
  color: var(--text-tertiary);
  width: 30px;
  text-align: right;
}

/* --- Papers --- */
.papers-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.paper-title {
  font-size: 13px;
  color: var(--text-primary);
}

.paper-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.paper-authors {
  color: var(--text-tertiary);
  font-size: 11px;
}

/* --- Logs --- */
.logs-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  padding: 24px;
}

.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
