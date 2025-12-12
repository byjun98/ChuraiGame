<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  username: '',
  email: '',
  password: '',
  passwordConfirm: ''
})

const isLoading = ref(false)
const errorMessage = ref('')

const handleSignup = async () => {
  // Validation
  if (!formData.value.username || !formData.value.email || !formData.value.password) {
    errorMessage.value = '모든 필드를 입력해주세요.'
    return
  }

  if (formData.value.password !== formData.value.passwordConfirm) {
    errorMessage.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  if (formData.value.password.length < 8) {
    errorMessage.value = '비밀번호는 8자 이상이어야 합니다.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  const success = await authStore.signup({
    username: formData.value.username,
    email: formData.value.email,
    password: formData.value.password
  })

  isLoading.value = false

  if (success) {
    router.push('/')
  } else {
    errorMessage.value = authStore.error || '회원가입에 실패했습니다.'
  }
}
</script>

<template>
  <div class="signup-view">
    <div class="signup-container">
      <div class="signup-card">
        <!-- Header -->
        <div class="signup-header">
          <span class="signup-icon">🎮</span>
          <h1>회원가입</h1>
          <p>ChuraiGame과 함께 게임을 즐기세요</p>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSignup" class="signup-form">
          <div class="form-group">
            <label for="username">아이디</label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              placeholder="사용할 아이디를 입력하세요"
              autocomplete="username"
            />
          </div>

          <div class="form-group">
            <label for="email">이메일</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              placeholder="이메일 주소를 입력하세요"
              autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label for="password">비밀번호</label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              placeholder="비밀번호를 입력하세요 (8자 이상)"
              autocomplete="new-password"
            />
          </div>

          <div class="form-group">
            <label for="passwordConfirm">비밀번호 확인</label>
            <input
              id="passwordConfirm"
              v-model="formData.passwordConfirm"
              type="password"
              placeholder="비밀번호를 다시 입력하세요"
              autocomplete="new-password"
            />
          </div>

          <button 
            type="submit" 
            class="btn-submit" 
            :disabled="isLoading"
          >
            <span v-if="isLoading">가입 중...</span>
            <span v-else>회원가입</span>
          </button>
        </form>

        <!-- Footer -->
        <div class="signup-footer">
          <p>이미 계정이 있으신가요? <RouterLink to="/login">로그인</RouterLink></p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.signup-view {
  min-height: calc(100vh - 70px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.signup-container {
  width: 100%;
  max-width: 420px;
}

.signup-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  backdrop-filter: blur(10px);
}

.signup-header {
  text-align: center;
  margin-bottom: 32px;
}

.signup-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.signup-header h1 {
  font-size: 28px;
  color: #fff;
  margin-bottom: 8px;
}

.signup-header p {
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

.signup-form {
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

.signup-footer {
  text-align: center;
  margin-top: 28px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.signup-footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.signup-footer a:hover {
  text-decoration: underline;
}
</style>
