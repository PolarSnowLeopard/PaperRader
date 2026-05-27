<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPaper, getPaperPdfUrl, generateReport, getReport, askPaperQuestion } from '../api/papers'
import { getNote, saveNote } from '../api/workspace'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined, FilePdfOutlined, LinkOutlined, SendOutlined } from '@ant-design/icons-vue'
import { MdEditor, MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

const route = useRoute()
const router = useRouter()
const wsId = Number(route.params.id)
const paperId = Number(route.params.pid)
const paper = ref(null)
const activeTab = ref('info')
const noteContent = ref('')
const saving = ref(false)
const reportContent = ref('')
const reportLoading = ref(false)
const question = ref('')
const qaHistory = ref([])
const qaLoading = ref(false)

onMounted(async () => {
  try {
    paper.value = await getPaper(paperId)
  } catch {
    paper.value = { title: '加载失败' }
  }
  try {
    const note = await getNote(paperId, wsId)
    if (note) noteContent.value = note.content || ''
  } catch {}
  try {
    const r = await getReport(paperId)
    reportContent.value = r.content
  } catch {}
})

const pdfUrl = getPaperPdfUrl(paperId)

async function handleSaveNote() {
  saving.value = true
  try {
    await saveNote(paperId, { content: noteContent.value, workspace_id: wsId })
    message.success('笔记已保存')
  } finally {
    saving.value = false
  }
}

async function handleGenerateReport() {
  reportLoading.value = true
  try {
    const r = await generateReport(paperId)
    reportContent.value = r.content
    message.success('报告已生成')
  } catch (e) {
    message.error('生成失败：' + (e.response?.data?.detail || '未知错误'))
  } finally {
    reportLoading.value = false
  }
}

async function handleAsk() {
  if (!question.value.trim()) return
  const q = question.value.trim()
  question.value = ''
  qaHistory.value.push({ role: 'user', content: q })
  qaLoading.value = true
  try {
    const res = await askPaperQuestion(paperId, q)
    qaHistory.value.push({ role: 'assistant', content: res.answer })
  } catch {
    qaHistory.value.push({ role: 'assistant', content: '抱歉，无法回答该问题。' })
  } finally {
    qaLoading.value = false
  }
}

function goBack() {
  router.push(`/ws/${wsId}`)
}
</script>

<template>
  <div class="detail-page">
    <!-- Top bar -->
    <div class="detail-topbar">
      <a-button type="text" class="back-btn" @click="goBack">
        <template #icon><arrow-left-outlined /></template>
      </a-button>
      <span class="topbar-title">{{ paper?.title || '加载中...' }}</span>
      <a-button v-if="paper?.abs_url" :href="paper.abs_url" target="_blank" size="small" class="topbar-link-btn">
        <template #icon><link-outlined /></template>原文
      </a-button>
    </div>

    <!-- Main content: PDF left + Tabs right -->
    <div class="detail-body">
      <!-- PDF Viewer -->
      <div class="pdf-viewer">
        <iframe
          v-if="paper?.pdf_path"
          :src="pdfUrl"
          class="pdf-iframe"
        />
        <iframe
          v-else-if="paper?.pdf_url"
          :src="paper.pdf_url"
          class="pdf-iframe"
        />
        <div v-else class="pdf-empty">
          <file-pdf-outlined class="pdf-empty-icon" />
          <p>暂无 PDF</p>
        </div>
      </div>

      <!-- Right panel: Tabs -->
      <div class="detail-panel">
        <a-tabs v-model:activeKey="activeTab" class="detail-tabs" :tab-bar-style="{ padding: '0 20px', marginBottom: 0 }">
          <a-tab-pane key="info" tab="信息">
            <div class="tab-scroll" v-if="paper">
              <a-descriptions :column="1" size="small" bordered class="info-table">
                <a-descriptions-item label="作者">
                  {{ (paper.authors || []).join(', ') }}
                </a-descriptions-item>
                <a-descriptions-item label="会议/期刊">{{ paper.venue || '-' }}</a-descriptions-item>
                <a-descriptions-item label="年份">{{ paper.year || '-' }}</a-descriptions-item>
                <a-descriptions-item label="arXiv ID">{{ paper.arxiv_id || '-' }}</a-descriptions-item>
                <a-descriptions-item label="DOI">{{ paper.doi || '-' }}</a-descriptions-item>
                <a-descriptions-item label="引用数">{{ paper.citation_count ?? '-' }}</a-descriptions-item>
                <a-descriptions-item label="来源">
                  <a-tag :bordered="false">{{ paper.source }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="类目">
                  <a-tag v-for="cat in (paper.categories || [])" :key="cat" color="green" :bordered="false" style="margin: 2px">{{ cat }}</a-tag>
                </a-descriptions-item>
              </a-descriptions>
              <div v-if="paper.abstract" class="info-section">
                <h4 class="info-section-title">摘要</h4>
                <p class="info-section-text">{{ paper.abstract }}</p>
              </div>
              <div v-if="paper.tldr" class="info-section">
                <h4 class="info-section-title">TLDR</h4>
                <p class="info-section-text" style="color: var(--primary)">{{ paper.tldr }}</p>
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="notes" tab="笔记" class="notes-tab">
            <div class="notes-container">
              <MdEditor v-model="noteContent" language="zh-CN" class="notes-editor" :toolbarsExclude="['github']" />
              <a-button type="primary" class="save-note-btn" @click="handleSaveNote" :loading="saving">
                保存笔记
              </a-button>
            </div>
          </a-tab-pane>

          <a-tab-pane key="report" tab="AI 报告">
            <div class="tab-scroll">
              <div v-if="!reportContent && !reportLoading" class="report-empty">
                <div class="report-empty-icon">AI</div>
                <p class="report-empty-text">基于论文全文生成结构化阅读报告</p>
                <a-button type="primary" @click="handleGenerateReport" class="generate-btn">生成 AI 报告</a-button>
              </div>
              <a-spin v-if="reportLoading" style="display: block; text-align: center; padding-top: 60px" tip="正在生成报告..." />
              <div v-if="reportContent && !reportLoading">
                <div style="margin-bottom: 12px; display: flex; justify-content: flex-end">
                  <a-button size="small" @click="handleGenerateReport" :loading="reportLoading">重新生成</a-button>
                </div>
                <div class="report-content">
                  <MdPreview :modelValue="reportContent" language="zh-CN" />
                </div>
              </div>

              <div v-if="reportContent" class="qa-section">
                <a-divider><span class="qa-divider-text">追问</span></a-divider>
                <div class="qa-history">
                  <div v-for="(msg, idx) in qaHistory" :key="idx" class="qa-msg" :class="msg.role">
                    <span class="qa-role">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
                    <span>{{ msg.content }}</span>
                  </div>
                </div>
                <a-input-search
                  v-model:value="question"
                  placeholder="对这篇论文提问..."
                  enter-button="提问"
                  :loading="qaLoading"
                  @search="handleAsk"
                />
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  height: calc(100vh - var(--header-height));
  display: flex;
  flex-direction: column;
}

/* --- Top bar --- */
.detail-topbar {
  padding: 0 20px;
  height: 50px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 10;
}

.back-btn {
  color: var(--text-secondary) !important;
}

.back-btn:hover {
  color: var(--primary) !important;
}

.topbar-title {
  font-weight: 500;
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}

.topbar-link-btn {
  border-radius: var(--radius-sm) !important;
  font-size: 12px;
}

/* --- Body --- */
.detail-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.pdf-viewer {
  flex: 1;
  background: #404040;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.pdf-empty {
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  padding-top: 200px;
}

.pdf-empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: rgba(255, 255, 255, 0.3);
}

.pdf-external-link {
  color: var(--primary-light);
}

/* --- Right panel --- */
.detail-panel {
  width: 420px;
  border-left: 1px solid var(--border-light);
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
}

:deep(.detail-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.detail-tabs .ant-tabs-content) {
  flex: 1;
  overflow: hidden;
}

:deep(.detail-tabs .ant-tabs-tabpane) {
  height: 100%;
  overflow-y: auto;
}

:deep(.detail-tabs .ant-tabs-ink-bar) {
  background: var(--primary-gradient) !important;
}

.tab-scroll {
  padding: 20px;
}

/* --- Info tab --- */
.info-section {
  margin-top: 20px;
}

.info-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.info-section-text {
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-secondary);
  margin: 0;
}

/* --- Notes tab --- */
.notes-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px;
  height: 100%;
}

.notes-editor {
  flex: 1;
}

.save-note-btn {
  margin-top: 8px;
  align-self: flex-end;
  border-radius: var(--radius-sm) !important;
  background: var(--primary-gradient) !important;
  border: none !important;
}

/* --- Report tab --- */
.report-empty {
  text-align: center;
  padding-top: 60px;
}

.report-empty-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--primary-gradient);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.report-empty-text {
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.generate-btn {
  border-radius: var(--radius-md) !important;
  background: var(--primary-gradient) !important;
  border: none !important;
}

.report-content {
  background: #faf8ff;
  border: 1px solid #ede9fe;
  border-radius: var(--radius-md);
  padding: 4px;
  position: relative;
}

.report-content::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--primary-gradient);
  border-radius: 3px 0 0 3px;
}

/* --- QA section --- */
.qa-section {
  margin-top: 16px;
}

.qa-divider-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

.qa-history {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.qa-msg {
  font-size: 13px;
  margin-bottom: 10px;
  line-height: 1.6;
}

.qa-msg.user {
  color: var(--primary);
}

.qa-msg.assistant {
  color: var(--text-primary);
}

.qa-role {
  font-weight: 600;
  margin-right: 6px;
}
</style>
