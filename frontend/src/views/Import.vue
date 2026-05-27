<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { uploadPaper, importPaper } from '../api/papers'
import { externalSearch } from '../api/search'
import { getFolderTree, addPaperToFolder } from '../api/workspace'
import { message } from 'ant-design-vue'
import { UploadOutlined, LinkOutlined, ArrowLeftOutlined, SearchOutlined, DownloadOutlined } from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const wsId = Number(route.params.id)
const activeTab = ref('search')
const loading = ref(false)
const arxivId = ref('')
const doi = ref('')
const folderTree = ref([])
const selectedFolder = ref(null)
const importedPaper = ref(null)

// External search state
const searchQuery = ref('')
const searchSource = ref('arxiv')
const searchResults = ref([])
const searching = ref(false)
const importing = ref({})

async function loadFolders() {
  try {
    folderTree.value = await getFolderTree(wsId)
  } catch {
    folderTree.value = []
  }
}
loadFolders()

function transformTree(folders) {
  return folders.map(f => ({
    title: f.name,
    value: f.id,
    children: f.children?.length ? transformTree(f.children) : undefined,
  }))
}

async function handleExternalSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  searchResults.value = []
  try {
    const res = await externalSearch({
      query: searchQuery.value.trim(),
      source: searchSource.value,
      limit: 20,
    })
    searchResults.value = res.results
  } catch {
    message.error('搜索失败')
  } finally {
    searching.value = false
  }
}

async function handleQuickImport(item) {
  const key = item.arxiv_id || item.doi || item.title
  importing.value[key] = true
  try {
    const data = {}
    if (item.arxiv_id) data.arxiv_id = item.arxiv_id
    else if (item.doi) data.doi = item.doi
    else {
      message.warning('该论文无可用的 arXiv ID 或 DOI，无法导入')
      return
    }
    const paper = await importPaper(data)
    importedPaper.value = paper
    if (selectedFolder.value) {
      await addPaperToFolder(selectedFolder.value, paper.id)
    }
    message.success(`已导入：${paper.title.slice(0, 40)}...`)
  } catch (e) {
    message.error('导入失败：' + (e.response?.data?.detail || '未知错误'))
  } finally {
    importing.value[key] = false
  }
}

async function handleImportArxiv() {
  if (!arxivId.value.trim()) return
  loading.value = true
  try {
    const paper = await importPaper({ arxiv_id: arxivId.value.trim() })
    importedPaper.value = paper
    if (selectedFolder.value) {
      await addPaperToFolder(selectedFolder.value, paper.id)
    }
    message.success(`导入成功：${paper.title.slice(0, 40)}...`)
    arxivId.value = ''
  } catch (e) {
    message.error('导入失败：' + (e.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function handleImportDoi() {
  if (!doi.value.trim()) return
  loading.value = true
  try {
    const paper = await importPaper({ doi: doi.value.trim() })
    importedPaper.value = paper
    if (selectedFolder.value) {
      await addPaperToFolder(selectedFolder.value, paper.id)
    }
    message.success(`导入成功：${paper.title.slice(0, 40)}...`)
    doi.value = ''
  } catch (e) {
    message.error('导入失败：' + (e.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function handleUpload(info) {
  const file = info.file.originFileObj || info.file
  loading.value = true
  try {
    const paper = await uploadPaper(file)
    importedPaper.value = paper
    if (selectedFolder.value) {
      await addPaperToFolder(selectedFolder.value, paper.id)
    }
    message.success(`上传成功：${paper.title}`)
  } catch (e) {
    message.error('上传失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push(`/ws/${wsId}`)
}
</script>

<template>
  <div class="import-page">
    <div class="import-container">
      <div class="import-header">
        <a-button type="text" class="back-btn" @click="goBack">
          <template #icon><arrow-left-outlined /></template>
          返回工作空间
        </a-button>
      </div>

      <div class="import-card">
        <div class="card-accent"></div>
        <div class="card-header">
          <h2 class="card-title">导入论文</h2>
        </div>

        <div class="card-body">
          <div class="folder-select">
            <span class="folder-label">目标文件夹</span>
            <a-tree-select
              v-model:value="selectedFolder"
              :tree-data="transformTree(folderTree)"
              placeholder="选择文件夹（可选）"
              allow-clear
              style="width: 100%"
            />
          </div>

          <a-tabs v-model:activeKey="activeTab" class="import-tabs">
            <!-- External Search Tab -->
            <a-tab-pane key="search" tab="搜索导入">
              <div class="tab-content">
                <div class="source-toggle">
                  <a-radio-group v-model:value="searchSource" button-style="solid" size="small">
                    <a-radio-button value="arxiv">arXiv</a-radio-button>
                    <a-radio-button value="semantic_scholar">Semantic Scholar</a-radio-button>
                  </a-radio-group>
                </div>
                <a-input-search
                  v-model:value="searchQuery"
                  placeholder="输入关键词搜索论文..."
                  enter-button="搜索"
                  :loading="searching"
                  @search="handleExternalSearch"
                  class="search-box"
                />
                <a-list
                  :data-source="searchResults"
                  :loading="searching"
                  :locale="{ emptyText: searchQuery ? '无结果' : '输入关键词开始搜索' }"
                  size="small"
                  class="search-results"
                >
                  <template #renderItem="{ item }">
                    <a-list-item class="search-result-item">
                      <a-list-item-meta>
                        <template #title>
                          <span class="result-title">{{ item.title }}</span>
                        </template>
                        <template #description>
                          <div class="result-meta">
                            <a-tag v-if="item.year" :bordered="false" size="small">{{ item.year }}</a-tag>
                            <a-tag v-if="item.venue" color="blue" :bordered="false" size="small">{{ item.venue }}</a-tag>
                            <a-tag v-if="item.citation_count" color="orange" :bordered="false" size="small">引用 {{ item.citation_count }}</a-tag>
                            <span class="result-authors">{{ (item.authors || []).slice(0, 3).join(', ') }}</span>
                          </div>
                        </template>
                      </a-list-item-meta>
                      <template #actions>
                        <a-button
                          type="primary"
                          size="small"
                          :loading="importing[item.arxiv_id || item.doi || item.title]"
                          :disabled="!item.arxiv_id && !item.doi"
                          @click="handleQuickImport(item)"
                          class="import-btn"
                        >
                          <template #icon><download-outlined /></template>
                          导入
                        </a-button>
                      </template>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-tab-pane>

            <a-tab-pane key="arxiv" tab="arXiv ID">
              <div class="tab-content">
                <a-input
                  v-model:value="arxivId"
                  placeholder="输入 arXiv ID，如 2401.04088"
                  size="large"
                  @press-enter="handleImportArxiv"
                />
                <a-button type="primary" :loading="loading" @click="handleImportArxiv" block class="submit-btn">
                  <template #icon><link-outlined /></template>
                  导入
                </a-button>
              </div>
            </a-tab-pane>

            <a-tab-pane key="doi" tab="DOI">
              <div class="tab-content">
                <a-input
                  v-model:value="doi"
                  placeholder="输入 DOI，如 10.1234/xxxx"
                  size="large"
                  @press-enter="handleImportDoi"
                />
                <a-button type="primary" :loading="loading" @click="handleImportDoi" block class="submit-btn">
                  <template #icon><link-outlined /></template>
                  导入
                </a-button>
              </div>
            </a-tab-pane>

            <a-tab-pane key="upload" tab="上传 PDF">
              <div class="tab-content">
                <a-upload-dragger
                  :before-upload="() => false"
                  @change="handleUpload"
                  accept=".pdf"
                  :multiple="false"
                  class="upload-dragger"
                >
                  <p class="upload-icon"><upload-outlined /></p>
                  <p class="upload-text">点击或拖拽 PDF 文件到此区域上传</p>
                </a-upload-dragger>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </div>

      <div v-if="importedPaper" class="imported-card fade-in">
        <div class="card-accent" style="background: linear-gradient(135deg, #10b981, #059669)"></div>
        <div class="imported-body">
          <h3 class="imported-title">最近导入</h3>
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="标题">{{ importedPaper.title }}</a-descriptions-item>
            <a-descriptions-item label="作者">{{ (importedPaper.authors || []).slice(0, 5).join(', ') }}</a-descriptions-item>
            <a-descriptions-item label="PDF">
              <a-tag :color="importedPaper.pdf_path ? 'green' : 'default'" :bordered="false">
                {{ importedPaper.pdf_path ? '已下载' : '未下载' }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
          <a-button type="link" @click="router.push(`/ws/${wsId}/paper/${importedPaper.id}`)" style="padding: 0">
            查看详情 →
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-page {
  min-height: calc(100vh - var(--header-height));
  background: var(--bg-page);
  padding: 32px 24px;
}

.import-container {
  max-width: 800px;
  margin: 0 auto;
}

.import-header {
  margin-bottom: 20px;
}

.back-btn {
  color: var(--text-secondary) !important;
  font-size: 13px;
}

.back-btn:hover {
  color: var(--primary) !important;
}

.import-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-accent {
  height: 3px;
  background: var(--primary-gradient);
}

.card-header {
  padding: 20px 24px 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-body {
  padding: 16px 24px 24px;
}

.folder-select {
  margin-bottom: 20px;
}

.folder-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

:deep(.import-tabs .ant-tabs-ink-bar) {
  background: var(--primary-gradient) !important;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 4px;
}

.source-toggle {
  margin-bottom: 4px;
}

.result-title {
  font-size: 13px;
  color: var(--text-primary);
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.result-authors {
  color: var(--text-tertiary);
  font-size: 11px;
}

.import-btn {
  border-radius: var(--radius-sm) !important;
  background: var(--primary-gradient) !important;
  border: none !important;
}

.submit-btn {
  margin-top: 4px;
  border-radius: var(--radius-md) !important;
  background: var(--primary-gradient) !important;
  border: none !important;
  height: 40px;
  font-weight: 500;
}

.upload-dragger {
  border-radius: var(--radius-md) !important;
}

.upload-icon {
  font-size: 42px;
  color: var(--primary);
  margin-bottom: 8px;
}

.upload-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.imported-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  margin-top: 16px;
}

.imported-body {
  padding: 20px 24px;
}

.imported-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}
</style>
