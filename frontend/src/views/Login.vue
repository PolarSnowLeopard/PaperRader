<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="32" height="32">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
            <path d="M8 7h6" /><path d="M8 11h8" />
          </svg>
        </div>
        <h1 class="logo-text">PaperRader</h1>
        <p class="login-subtitle">AI-Powered Research Paper Platform</p>
      </div>

      <a-form layout="vertical" @finish="handleLogin" :model="form" class="login-form">
        <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
          <a-input
            v-model:value="form.username"
            placeholder="用户名"
            size="large"
            :prefix="h(UserOutlined)"
          />
        </a-form-item>
        <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
          <a-input-password
            v-model:value="form.password"
            placeholder="密码"
            size="large"
            :prefix="h(LockOutlined)"
            @pressEnter="handleLogin"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            block
            size="large"
            :loading="loading"
            class="login-btn"
          >
            登 录
          </a-button>
        </a-form-item>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { h, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { login } from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  loading.value = true
  try {
    const res = await login({ username: form.username, password: form.password })
    localStorage.setItem('token', res.token)
    localStorage.setItem('username', res.username)
    message.success('登录成功')
    router.push('/')
  } catch (err) {
    message.error(err.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e1e2e 0%, #2d1b69 50%, #1e1e2e 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15), transparent 70%);
  top: -200px;
  right: -100px;
}

.login-page::after {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.12), transparent 70%);
  bottom: -100px;
  left: -50px;
}

.login-card {
  width: 400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--primary-gradient);
  color: white;
  margin-bottom: 16px;
}

.logo-text {
  font-size: 26px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px;
}

.login-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.login-form :deep(.ant-input-affix-wrapper) {
  border-radius: var(--radius-md);
  border-color: var(--border-light);
  padding: 8px 12px;
}

.login-form :deep(.ant-input-affix-wrapper:hover),
.login-form :deep(.ant-input-affix-wrapper-focused) {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.login-btn {
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--primary-gradient);
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  transition: all var(--transition-base);
}

.login-btn:hover {
  background: var(--primary-gradient-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}
</style>
