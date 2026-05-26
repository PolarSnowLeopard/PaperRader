<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getPapers } from '../api/papers'
import { StarOutlined, StarFilled } from '@ant-design/icons-vue'

const router = useRouter()
const papers = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = ref({ source: undefined, year: undefined, q: '' })

async function fetchPapers() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      sort_by: 'created_at',
      ...Object.fromEntries(
        Object.entries(filters.value).filter(([_, v]) => v)
      ),
    }
    const res = await getPapers(params)
    papers.value = res.papers
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(fetchPapers)
watch([page, pageSize], fetchPapers)

function goToDetail(id) {
  router.push(`/paper/${id}`)
}
</script>

<template>
  <div>
    <a-page-header title="论文流" sub-title="最新收录的论文" />

    <a-space style="margin-bottom: 16px">
      <a-input-search
        v-model:value="filters.q"
        placeholder="关键词过滤"
        @search="fetchPapers"
        style="width: 250px"
      />
      <a-select v-model:value="filters.source" placeholder="数据源" allow-clear style="width: 120px" @change="fetchPapers">
        <a-select-option value="arxiv">arXiv</a-select-option>
        <a-select-option value="dblp">DBLP</a-select-option>
      </a-select>
      <a-input-number v-model:value="filters.year" placeholder="年份" :min="2015" :max="2026" @change="fetchPapers" />
    </a-space>

    <a-list
      :loading="loading"
      :data-source="papers"
      :pagination="{
        current: page,
        pageSize,
        total,
        onChange: (p, ps) => { page = p; pageSize = ps },
        showSizeChanger: true,
      }"
    >
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta>
            <template #title>
              <a @click="goToDetail(item.id)" style="cursor: pointer">{{ item.title }}</a>
            </template>
            <template #description>
              <a-space>
                <a-tag v-if="item.venue" color="blue">{{ item.venue }}</a-tag>
                <a-tag v-if="item.year">{{ item.year }}</a-tag>
                <a-tag v-for="cat in (item.categories || []).slice(0, 3)" :key="cat" color="green">{{ cat }}</a-tag>
                <span v-if="item.authors && item.authors.length" style="color: #999; font-size: 12px">
                  {{ item.authors.slice(0, 3).join(', ') }}{{ item.authors.length > 3 ? ' et al.' : '' }}
                </span>
              </a-space>
            </template>
          </a-list-item-meta>
          <template #extra>
            <a-tag :color="item.source === 'arxiv' ? 'orange' : 'purple'">{{ item.source }}</a-tag>
          </template>
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>
