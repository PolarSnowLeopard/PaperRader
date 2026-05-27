<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getWorkspaces, createWorkspace, deleteWorkspace } from '../api/workspace'
import { message } from 'ant-design-vue'
import { PlusOutlined, FolderOpenOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const workspaces = ref([])
const showCreate = ref(false)
const newName = ref('')
const newDesc = ref('')

onMounted(loadWorkspaces)

async function loadWorkspaces() {
  try {
    workspaces.value = await getWorkspaces()
  } catch {
    workspaces.value = []
  }
}

async function handleCreate() {
  if (!newName.value.trim()) return
  await createWorkspace({ name: newName.value.trim(), description: newDesc.value.trim() || null })
  message.success('工作空间已创建')
  showCreate.value = false
  newName.value = ''
  newDesc.value = ''
  await loadWorkspaces()
}

async function handleDelete(id) {
  await deleteWorkspace(id)
  message.success('已删除')
  await loadWorkspaces()
}

function openWorkspace(id) {
  router.push(`/ws/${id}`)
}
</script>

<template>
  <div class="workspace-page">
    <!-- Hero section -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">我的工作空间</h1>
        <p class="hero-subtitle">管理你的论文研究项目</p>
        <a-button class="hero-btn" size="large" @click="showCreate = true">
          <template #icon><plus-outlined /></template>
          新建工作空间
        </a-button>
      </div>
    </div>

    <!-- Workspace cards -->
    <div class="cards-section">
      <a-row :gutter="[20, 20]">
        <a-col :span="8" v-for="ws in workspaces" :key="ws.id">
          <div class="ws-card card-hover" @click="openWorkspace(ws.id)">
            <div class="ws-card-accent"></div>
            <div class="ws-card-body">
              <div class="ws-card-header">
                <div class="ws-card-icon">
                  <folder-open-outlined />
                </div>
                <a-popconfirm title="确定删除？" @confirm.stop="handleDelete(ws.id)">
                  <a-button type="text" size="small" class="ws-delete-btn" @click.stop>
                    <template #icon><delete-outlined /></template>
                  </a-button>
                </a-popconfirm>
              </div>
              <h3 class="ws-card-title">{{ ws.name }}</h3>
              <p class="ws-card-desc">{{ ws.description || '暂无描述' }}</p>
              <div class="ws-card-footer">
                <span class="ws-paper-count">{{ ws.paper_count }} 篇论文</span>
              </div>
            </div>
          </div>
        </a-col>
      </a-row>

      <div v-if="!workspaces.length" class="empty-state fade-in">
        <div class="empty-icon">
          <folder-open-outlined />
        </div>
        <p class="empty-title">还没有工作空间</p>
        <p class="empty-desc">创建一个工作空间来开始管理你的论文</p>
        <a-button type="primary" @click="showCreate = true">
          <template #icon><plus-outlined /></template>
          创建工作空间
        </a-button>
      </div>
    </div>

    <a-modal v-model:open="showCreate" title="新建工作空间" @ok="handleCreate" :width="420">
      <a-form layout="vertical" style="margin-top: 16px">
        <a-form-item label="名称" required>
          <a-input v-model:value="newName" placeholder="如：LLM Agent 调研" size="large" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="newDesc" :rows="3" placeholder="简要描述研究方向..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.workspace-page {
  min-height: calc(100vh - var(--header-height));
}

.hero-section {
  background: linear-gradient(135deg, #1e1e2e 0%, #2d1b69 40%, #4338ca 100%);
  padding: 60px 24px 56px;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.hero-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  margin: 0 0 28px;
}

.hero-btn {
  background: rgba(255, 255, 255, 0.12) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
  border-radius: var(--radius-md) !important;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.hero-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.35) !important;
  transform: translateY(-1px);
}

.cards-section {
  max-width: 940px;
  margin: -24px auto 48px;
  padding: 0 24px;
  position: relative;
  z-index: 2;
}

.ws-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  height: 180px;
  display: flex;
  flex-direction: column;
}

.ws-card-accent {
  height: 4px;
  background: var(--primary-gradient);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.ws-card:hover .ws-card-accent {
  opacity: 1;
}

.ws-card-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.ws-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.ws-card-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  font-size: 16px;
}

.ws-delete-btn {
  opacity: 0;
  color: var(--text-tertiary) !important;
  transition: opacity var(--transition-fast);
}

.ws-card:hover .ws-delete-btn {
  opacity: 1;
}

.ws-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
  line-height: 1.3;
}

.ws-card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  flex: 1;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.ws-card-footer {
  margin-top: 12px;
}

.ws-paper-count {
  font-size: 12px;
  color: var(--primary);
  font-weight: 500;
  background: #f0edff;
  padding: 2px 10px;
  border-radius: 10px;
}

.empty-state {
  text-align: center;
  padding: 80px 24px;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  background: var(--bg-inset);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 28px;
  color: var(--text-tertiary);
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.empty-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 24px;
}
</style>
