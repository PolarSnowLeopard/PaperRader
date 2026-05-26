<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getPaper, updateUserPaper } from '../api/papers'
import { message } from 'ant-design-vue'
import { StarOutlined, StarFilled, LinkOutlined, FilePdfOutlined } from '@ant-design/icons-vue'

const route = useRoute()
const paper = ref(null)
const starred = ref(false)
const notes = ref('')

onMounted(async () => {
  paper.value = await getPaper(route.params.id)
})

async function toggleStar() {
  starred.value = !starred.value
  await updateUserPaper(paper.value.id, { is_starred: starred.value })
  message.success(starred.value ? '已收藏' : '已取消收藏')
}

async function saveNotes() {
  await updateUserPaper(paper.value.id, { user_notes: notes.value })
  message.success('笔记已保存')
}
</script>

<template>
  <div v-if="paper">
    <a-page-header :title="paper.title" @back="$router.back()">
      <template #extra>
        <a-button @click="toggleStar">
          <template #icon>
            <star-filled v-if="starred" style="color: #faad14" />
            <star-outlined v-else />
          </template>
          {{ starred ? '已收藏' : '收藏' }}
        </a-button>
        <a-button v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" type="primary">
          <template #icon><file-pdf-outlined /></template>
          PDF
        </a-button>
        <a-button v-if="paper.abs_url" :href="paper.abs_url" target="_blank">
          <template #icon><link-outlined /></template>
          原文
        </a-button>
      </template>
    </a-page-header>

    <a-descriptions bordered :column="2" style="margin-top: 16px">
      <a-descriptions-item label="作者" :span="2">
        {{ (paper.authors || []).join(', ') }}
      </a-descriptions-item>
      <a-descriptions-item label="会议/期刊">{{ paper.venue || '-' }}</a-descriptions-item>
      <a-descriptions-item label="年份">{{ paper.year || '-' }}</a-descriptions-item>
      <a-descriptions-item label="arXiv ID">{{ paper.arxiv_id || '-' }}</a-descriptions-item>
      <a-descriptions-item label="引用数">{{ paper.citation_count ?? '-' }}</a-descriptions-item>
      <a-descriptions-item label="来源">
        <a-tag :color="paper.source === 'arxiv' ? 'orange' : 'purple'">{{ paper.source }}</a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="类目">
        <a-tag v-for="cat in (paper.categories || [])" :key="cat" color="green">{{ cat }}</a-tag>
      </a-descriptions-item>
    </a-descriptions>

    <a-card title="摘要" style="margin-top: 16px" v-if="paper.abstract">
      <p style="line-height: 1.8; white-space: pre-wrap">{{ paper.abstract }}</p>
    </a-card>

    <a-card title="TLDR" style="margin-top: 16px" v-if="paper.tldr">
      <p>{{ paper.tldr }}</p>
    </a-card>

    <a-card title="笔记" style="margin-top: 16px">
      <a-textarea v-model:value="notes" :rows="4" placeholder="添加你的阅读笔记..." />
      <a-button type="primary" style="margin-top: 8px" @click="saveNotes">保存笔记</a-button>
    </a-card>
  </div>
</template>
