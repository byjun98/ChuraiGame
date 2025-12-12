<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '아이디와 비밀번호를 입력해주세요.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  const success = await authStore.login(username.value, password.value)
  
  isLoading.value = false

  if (success) {
    // 리다이렉트 URL이 있으면 해당 페이지로, 없으면 홈으로
    const redirectTo = route.query.redirect || '/'
    router.push(redirectTo)
  } else {
    errorMessage.value = authStore.error || '로그인에 실패했습니다.'
  }
}
</script>

<template>
  <div class="login-view">
    <div class="login-container">
      <div class="login-card">
        <!-- Header -->
        <div class="login-header">
          <span class="login-icon">🎮</span>
          <h1>로그인</h1>
          <p>ChuraiGame에 오신 것을 환영합니다</p>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label for="username">아이디</label>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="아이디를 입력하세요"
              autocomplete="username"
            />
          </div>

          <div class="form-group">
            <label for="password">비밀번호</label>
            <input
              id="password"
              v-model="password"
              type="password"
              placeholder="비밀번호를 입력하세요"
              autocomplete="current-password"
            />
          </div>

          <button 
            type="submit" 
            class="btn-submit" 
            :disabled="isLoading"
          >
            <span v-if="isLoading">로그인 중...</span>
            <span v-else>로그인</span>
          </button>
        </form>

        <!-- Social Login -->
        <div class="social-login">
          <div class="divider">
            <span>또는</span>
          </div>
          <button class="btn-steam">
            <span class="steam-icon">🎮</span>
            Steam으로 로그인
          </button>
        </div>

        <!-- Footer -->
        <div class="login-footer">
          <p>계정이 없으신가요? <RouterLink to="/signup">회원가입</RouterLink></p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  min-height: calc(100vh - 70px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.login-header h1 {
  font-size: 28px;
  color: #fff;
  margin-bottom: 8px;
}

.login-header p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.error-message {
  background: rgba(255, 100, 100, 0.1);
  border: 1px solid rgba(255, 100, 100, 0.3);
  color: #ff6b6b;
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 14px;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.form-group input {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.08);
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.btn-submit {
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-top: 8px;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.btn-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.social-login {
  margin-top: 32px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.divider span {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.btn-steam {
  width: 100%;
  padding: 14px;
  background: #1b2838;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s;
}

.btn-steam:hover {
  background: #2a475e;
  border-color: rgba(255, 255, 255, 0.2);
}

.steam-icon {
  font-size: 20px;
}

.login-footer {
  text-align: center;
  margin-top: 28px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.login-footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>
