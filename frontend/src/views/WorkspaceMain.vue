<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getFolderTree, createFolder, deleteFolder, getFolderPapers,
  addPaperToFolder, removePaperFromFolder, getWorkspacePapers
} from '../api/workspace'
import { getWorkspace } from '../api/workspace'
import {
  PlusOutlined, SearchOutlined, ImportOutlined, FolderAddOutlined,
  DeleteOutlined, FileTextOutlined, MessageOutlined,
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const wsId = ref(Number(route.params.id))
const workspace = ref(null)
const folderTree = ref([])
const selectedFolder = ref(null)
const papers = ref([])
const selectedPaper = ref(null)
const loading = ref(false)
const showNewFolder = ref(false)
const newFolderName = ref('')
const newFolderParent = ref(null)

onMounted(async () => {
  await loadWorkspace()
  await loadFolders()
  await loadAllPapers()
})

async function loadWorkspace() {
  try {
    workspace.value = await getWorkspace(wsId.value)
  } catch {
    workspace.value = { name: '加载失败' }
  }
}

async function loadFolders() {
  try {
    folderTree.value = await getFolderTree(wsId.value)
  } catch {
    folderTree.value = []
  }
}

function transformTree(folders) {
  return folders.map(f => ({
    title: f.name,
    key: f.id,
    children: f.children ? transformTree(f.children) : [],
  }))
}

async function loadAllPapers() {
  loading.value = true
  try {
    papers.value = await getWorkspacePapers(wsId.value)
  } catch {
    papers.value = []
  } finally {
    loading.value = false
  }
}

async function onSelectFolder(keys) {
  if (!keys.length) {
    selectedFolder.value = null
    await loadAllPapers()
    return
  }
  selectedFolder.value = keys[0]
  loading.value = true
  try {
    papers.value = await getFolderPapers(keys[0])
  } finally {
    loading.value = false
  }
}

async function handleCreateFolder() {
  if (!newFolderName.value.trim()) return
  await createFolder(wsId.value, {
    name: newFolderName.value.trim(),
    parent_id: newFolderParent.value || null,
  })
  showNewFolder.value = false
  newFolderName.value = ''
  newFolderParent.value = null
  await loadFolders()
  message.success('文件夹已创建')
}

async function handleDeleteFolder(folderId) {
  await deleteFolder(folderId)
  if (selectedFolder.value === folderId) {
    selectedFolder.value = null
    papers.value = []
  }
  await loadFolders()
  message.success('已删除')
}

function openPaper(paper) {
  router.push(`/ws/${wsId.value}/paper/${paper.id}`)
}

function selectPaper(paper) {
  selectedPaper.value = paper
}
</script>

<template>
  <div class="ws-main">
    <!-- Left: Sidebar -->
    <div class="sidebar dark-scroll">
      <div class="sidebar-header">
        <span class="sidebar-title">{{ workspace?.name || '...' }}</span>
        <a-tooltip title="新建文件夹">
          <a-button type="text" size="small" class="sidebar-icon-btn" @click="showNewFolder = true">
            <template #icon><folder-add-outlined /></template>
          </a-button>
        </a-tooltip>
      </div>

      <div class="sidebar-tree">
        <a-tree
          v-if="folderTree.length"
          :tree-data="transformTree(folderTree)"
          :selected-keys="selectedFolder ? [selectedFolder] : []"
          @select="onSelectFolder"
          default-expand-all
          block-node
          class="dark-tree"
        />
        <div v-else class="sidebar-empty">
          <p>暂无文件夹</p>
          <a-button size="small" ghost @click="showNewFolder = true">创建文件夹</a-button>
        </div>
      </div>

      <div class="sidebar-actions">
        <div class="sidebar-action-btn" @click="router.push(`/ws/${wsId}/search`)">
          <search-outlined class="action-icon" />
          <span>搜索</span>
        </div>
        <div class="sidebar-action-btn" @click="router.push(`/ws/${wsId}/import`)">
          <import-outlined class="action-icon" />
          <span>导入论文</span>
        </div>
        <div class="sidebar-action-btn" @click="router.push(`/ws/${wsId}/chat`)">
          <message-outlined class="action-icon" />
          <span>AI 问答</span>
        </div>
      </div>
    </div>

    <!-- Middle: Paper list -->
    <div class="paper-list">
      <div class="paper-list-header" v-if="papers.length || selectedFolder">
        <span class="paper-list-label">{{ selectedFolder ? '文件夹论文' : '全部论文' }}</span>
        <span class="paper-list-count">{{ papers.length }} 篇</span>
      </div>
      <a-spin :spinning="loading">
        <div class="paper-list-inner">
          <div
            v-for="item in papers" :key="item.id"
            class="paper-card"
            :class="{ 'paper-card-active': selectedPaper?.id === item.id }"
            @click="selectPaper(item)"
            @dblclick="openPaper(item)"
          >
            <div class="paper-card-accent"></div>
            <div class="paper-card-content">
              <div class="paper-card-title">
                <file-text-outlined class="paper-icon" />
                {{ item.title }}
              </div>
              <div class="paper-card-meta">
                <a-tag v-if="item.venue" color="blue" :bordered="false" size="small">{{ item.venue }}</a-tag>
                <a-tag v-if="item.year" :bordered="false" size="small">{{ item.year }}</a-tag>
                <span class="paper-authors">
                  {{ (item.authors || []).slice(0, 3).join(', ') }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="!papers.length && !loading" class="paper-list-empty" style="padding-top: 60px">
            <div class="empty-folder-icon">
              <file-text-outlined />
            </div>
            <p style="color: var(--text-tertiary)">{{ selectedFolder ? '此文件夹暂无论文' : '暂无论文，去导入吧' }}</p>
          </div>
        </div>
      </a-spin>
    </div>

    <!-- Right: Preview panel -->
    <div v-if="selectedPaper" class="preview-panel">
      <div class="preview-accent"></div>
      <div class="preview-content">
        <h3 class="preview-title">{{ selectedPaper.title }}</h3>
        <a-divider style="margin: 14px 0" />
        <div class="preview-field">
          <span class="preview-label">作者</span>
          <span>{{ (selectedPaper.authors || []).join(', ') }}</span>
        </div>
        <div v-if="selectedPaper.venue" class="preview-field">
          <span class="preview-label">会议</span>
          <span>{{ selectedPaper.venue }} {{ selectedPaper.year }}</span>
        </div>
        <div v-if="selectedPaper.abstract" class="preview-abstract">
          <span class="preview-label">摘要</span>
          <p>{{ selectedPaper.abstract.slice(0, 300) }}{{ selectedPaper.abstract.length > 300 ? '...' : '' }}</p>
        </div>
        <a-divider style="margin: 14px 0" />
        <a-button type="primary" block @click="openPaper(selectedPaper)" class="preview-open-btn">
          打开详情
        </a-button>
      </div>
    </div>

    <!-- New folder modal -->
    <a-modal v-model:open="showNewFolder" title="新建文件夹" @ok="handleCreateFolder" width="360px">
      <a-input v-model:value="newFolderName" placeholder="文件夹名称" style="margin-top: 12px" />
    </a-modal>
  </div>
</template>

<style scoped>
.ws-main {
  height: calc(100vh - var(--header-height));
  display: flex;
}

/* --- Sidebar --- */
.sidebar {
  width: 250px;
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  padding: 16px 18px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-on-dark);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.sidebar-icon-btn {
  color: var(--text-on-dark-secondary) !important;
  transition: color var(--transition-fast);
}

.sidebar-icon-btn:hover {
  color: #fff !important;
  background: var(--bg-sidebar-hover) !important;
}

.sidebar-tree {
  flex: 1;
  padding: 8px 10px;
  overflow-y: auto;
}

:deep(.dark-tree) {
  background: transparent;
  color: var(--text-on-dark-secondary);
}

:deep(.dark-tree .ant-tree-treenode) {
  color: var(--text-on-dark-secondary);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

:deep(.dark-tree .ant-tree-treenode:hover) {
  background: var(--bg-sidebar-hover);
}

:deep(.dark-tree .ant-tree-node-selected) {
  background: var(--bg-sidebar-active) !important;
  color: #fff;
}

:deep(.dark-tree .ant-tree-node-content-wrapper) {
  color: inherit;
}

:deep(.dark-tree .ant-tree-node-content-wrapper.ant-tree-node-selected) {
  background: transparent !important;
  color: #fff;
}

:deep(.dark-tree .ant-tree-switcher) {
  color: var(--text-on-dark-secondary);
}

.sidebar-empty {
  text-align: center;
  padding-top: 40px;
  color: var(--text-on-dark-secondary);
  font-size: 13px;
}

.sidebar-actions {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding: 8px 10px;
}

.sidebar-action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  border-radius: var(--radius-sm);
  color: var(--text-on-dark-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.sidebar-action-btn:hover {
  background: var(--bg-sidebar-hover);
  color: #fff;
}

.sidebar-action-btn:hover::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: var(--primary-gradient);
}

.action-icon {
  font-size: 14px;
}

/* --- Paper list --- */
.paper-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-page);
}

.paper-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.paper-list-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.paper-list-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.paper-list-empty {
  text-align: center;
  padding-top: 120px;
  color: var(--text-tertiary);
}

.empty-folder-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  background: var(--bg-inset);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 24px;
  color: var(--text-tertiary);
}

.paper-list-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.paper-card {
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  cursor: pointer;
  display: flex;
  overflow: hidden;
  transition: all var(--transition-fast);
}

.paper-card:hover {
  box-shadow: var(--shadow-md);
  border-color: #ddd;
}

.paper-card-active {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 1px var(--primary);
}

.paper-card-accent {
  width: 3px;
  flex-shrink: 0;
  background: transparent;
  transition: background var(--transition-fast);
}

.paper-card:hover .paper-card-accent {
  background: var(--primary-gradient);
}

.paper-card-content {
  padding: 14px 16px;
  flex: 1;
  min-width: 0;
}

.paper-card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 8px;
}

.paper-icon {
  color: var(--primary);
  margin-right: 6px;
  font-size: 13px;
}

.paper-card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.paper-authors {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* --- Preview panel --- */
.preview-panel {
  width: 320px;
  border-left: 1px solid var(--border-light);
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.preview-accent {
  height: 3px;
  background: var(--primary-gradient);
  flex-shrink: 0;
}

.preview-content {
  padding: 20px;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  margin: 0;
}

.preview-field {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.6;
}

.preview-label {
  display: block;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.preview-abstract {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-top: 8px;
}

.preview-abstract p {
  margin: 4px 0 0;
}

.preview-open-btn {
  border-radius: var(--radius-md) !important;
  background: var(--primary-gradient) !important;
  border: none !important;
  font-weight: 500;
  height: 38px;
}

.preview-open-btn:hover {
  background: var(--primary-gradient-hover) !important;
}
</style>
