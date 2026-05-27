<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getChatSessions, createChatSession, deleteChatSession, getMessages, sendMessage } from '../api/chat'
import { message } from 'ant-design-vue'
import {
  ArrowLeftOutlined, PlusOutlined, DeleteOutlined, SendOutlined, MessageOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const wsId = Number(route.params.id)
const sessions = ref([])
const activeSession = ref(null)
const messages_list = ref([])
const inputText = ref('')
const loading = ref(false)
const sendingMsg = ref(false)
const messagesContainer = ref(null)

onMounted(async () => {
  await loadSessions()
})

async function loadSessions() {
  try {
    sessions.value = await getChatSessions(wsId)
  } catch {
    sessions.value = []
  }
}

async function handleNewSession() {
  const session = await createChatSession(wsId, '新对话')
  sessions.value.unshift(session)
  selectSession(session)
}

async function selectSession(session) {
  activeSession.value = session
  loading.value = true
  try {
    messages_list.value = await getMessages(session.id)
    await nextTick()
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

async function handleDeleteSession(session) {
  await deleteChatSession(session.id)
  if (activeSession.value?.id === session.id) {
    activeSession.value = null
    messages_list.value = []
  }
  await loadSessions()
  message.success('已删除')
}

async function handleSend() {
  if (!inputText.value.trim() || !activeSession.value) return
  const content = inputText.value.trim()
  inputText.value = ''
  messages_list.value.push({ role: 'user', content, id: Date.now() })
  await nextTick()
  scrollToBottom()

  sendingMsg.value = true
  try {
    const reply = await sendMessage(activeSession.value.id, content)
    messages_list.value.push(reply)
    await nextTick()
    scrollToBottom()
  } catch {
    messages_list.value.push({ role: 'assistant', content: '抱歉，发生错误，请重试。', id: Date.now() + 1 })
  } finally {
    sendingMsg.value = false
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function goBack() {
  router.push(`/ws/${wsId}`)
}
</script>

<template>
  <div class="chat-page">
    <!-- Left: Session list -->
    <div class="chat-sidebar dark-scroll">
      <div class="chat-sidebar-header">
        <a-button type="text" size="small" class="sidebar-back-btn" @click="goBack">
          <template #icon><arrow-left-outlined /></template>
        </a-button>
        <span class="chat-sidebar-title">AI 问答</span>
        <a-button size="small" class="new-chat-btn" @click="handleNewSession">
          <template #icon><plus-outlined /></template>
        </a-button>
      </div>
      <div class="chat-session-list">
        <div
          v-for="session in sessions" :key="session.id"
          @click="selectSession(session)"
          class="chat-session-item"
          :class="{ active: activeSession?.id === session.id }"
        >
          <message-outlined class="session-icon" />
          <span class="session-title">{{ session.title }}</span>
          <a-popconfirm title="删除此对话？" @confirm.stop="handleDeleteSession(session)">
            <delete-outlined class="session-delete" @click.stop />
          </a-popconfirm>
        </div>
        <div v-if="!sessions.length" class="chat-session-empty">
          <p>暂无对话</p>
          <a-button size="small" ghost @click="handleNewSession">开始新对话</a-button>
        </div>
      </div>
    </div>

    <!-- Right: Chat area -->
    <div class="chat-area">
      <div v-if="!activeSession" class="chat-welcome">
        <div class="welcome-icon">
          <message-outlined />
        </div>
        <p class="welcome-title">选择或创建一个对话开始提问</p>
        <p class="welcome-desc">AI 可以访问当前工作空间内所有论文的内容</p>
      </div>

      <template v-if="activeSession">
        <!-- Messages -->
        <div ref="messagesContainer" class="chat-messages">
          <a-spin v-if="loading" style="display: block; text-align: center; margin-top: 40px" />
          <div v-for="msg in messages_list" :key="msg.id" class="msg-row" :class="msg.role">
            <div class="msg-bubble" :class="msg.role">
              <span v-if="msg.role === 'assistant'" class="ai-badge">AI</span>
              {{ msg.content }}
            </div>
          </div>
          <div v-if="sendingMsg" class="msg-row assistant">
            <div class="msg-bubble assistant thinking">
              <span class="ai-badge">AI</span>
              <a-spin size="small" /> 思考中...
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="chat-input-area">
          <a-input-search
            v-model:value="inputText"
            placeholder="输入你的问题..."
            enter-button="发送"
            size="large"
            :loading="sendingMsg"
            @search="handleSend"
            class="chat-input"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  height: calc(100vh - var(--header-height));
  display: flex;
}

/* --- Sidebar --- */
.chat-sidebar {
  width: 270px;
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.chat-sidebar-header {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-back-btn {
  color: var(--text-on-dark-secondary) !important;
}

.sidebar-back-btn:hover {
  color: #fff !important;
  background: var(--bg-sidebar-hover) !important;
}

.chat-sidebar-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-on-dark);
  flex: 1;
}

.new-chat-btn {
  background: var(--primary-gradient) !important;
  border: none !important;
  color: #fff !important;
  border-radius: var(--radius-sm) !important;
}

.chat-session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-session-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-on-dark-secondary);
  transition: all var(--transition-fast);
}

.chat-session-item:hover {
  background: var(--bg-sidebar-hover);
  color: var(--text-on-dark);
}

.chat-session-item.active {
  background: var(--bg-sidebar-active);
  color: #fff;
}

.session-icon {
  font-size: 13px;
  flex-shrink: 0;
}

.session-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-delete {
  font-size: 11px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.chat-session-item:hover .session-delete {
  opacity: 0.6;
}

.session-delete:hover {
  opacity: 1 !important;
}

.chat-session-empty {
  text-align: center;
  padding-top: 60px;
  color: var(--text-on-dark-secondary);
  font-size: 13px;
}

/* --- Chat area --- */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
}

.chat-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-xl);
  background: var(--bg-inset);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: var(--text-tertiary);
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0 0 6px;
}

.welcome-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

/* --- Messages --- */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.msg-row {
  display: flex;
  margin-bottom: 16px;
}

.msg-row.user {
  justify-content: flex-end;
}

.msg-row.assistant {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  position: relative;
}

.msg-bubble.user {
  background: var(--primary-gradient);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg-bubble.assistant {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  border-bottom-left-radius: 4px;
  box-shadow: var(--shadow-sm);
}

.ai-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  color: var(--primary);
  background: #f0edff;
  padding: 1px 6px;
  border-radius: 4px;
  margin-right: 8px;
  vertical-align: middle;
}

.msg-bubble.thinking {
  color: var(--text-tertiary);
}

/* --- Input area --- */
.chat-input-area {
  padding: 16px 32px;
  background: var(--bg-surface);
  border-top: 1px solid var(--border-light);
}

:deep(.chat-input .ant-input) {
  border-radius: var(--radius-md) !important;
}

:deep(.chat-input .ant-input:focus) {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
}

:deep(.chat-input .ant-btn) {
  background: var(--primary-gradient) !important;
  border: none !important;
  border-radius: 0 var(--radius-md) var(--radius-md) 0 !important;
}
</style>
