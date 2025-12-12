<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGamesStore } from '@/stores/games'

const router = useRouter()
const authStore = useAuthStore()
const gamesStore = useGamesStore()

const searchQuery = ref('')
const isSearching = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.username)

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  isSearching.value = true
  await gamesStore.searchGames(searchQuery.value)
  isSearching.value = false
  
  router.push({ name: 'home', query: { search: searchQuery.value } })
}

const handleLogout = async () => {
  await authStore.logout()
  router.push({ name: 'home' })
}

const goToHome = () => {
  router.push({ name: 'home' })
}
</script>

<template>
  <header class="header">
    <div class="header-content">
      <!-- Logo -->
      <div class="logo" @click="goToHome">
        <span class="logo-icon">🎮</span>
        <span class="logo-text">ChuraiGame</span>
      </div>

      <!-- Search Bar -->
      <div class="search-container">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="게임 검색..."
          class="search-input"
          @keyup.enter="handleSearch"
        />
        <button class="search-btn" @click="handleSearch" :disabled="isSearching">
          <span v-if="isSearching">⏳</span>
          <span v-else>🔍</span>
        </button>
      </div>

      <!-- Nav Actions -->
      <nav class="nav-actions">
        <template v-if="isAuthenticated">
          <RouterLink to="/profile" class="nav-link">
            <span class="nav-icon">👤</span>
            <span class="nav-text">{{ username }}</span>
          </RouterLink>
          <button class="btn-logout" @click="handleLogout">
            로그아웃
          </button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn-login">로그인</RouterLink>
          <RouterLink to="/signup" class="btn-signup">회원가입</RouterLink>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: rgba(15, 15, 26, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 1000;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s;
}

.logo:hover {
  transform: scale(1.05);
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.search-container {
  flex: 1;
  max-width: 500px;
  display: flex;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 50px 12px 20px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 50px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 14px;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.1);
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-btn {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-50%) scale(1.1);
}

.search-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-icon {
  font-size: 18px;
}

.nav-text {
  font-weight: 500;
}

.btn-login {
  padding: 10px 20px;
  border-radius: 10px;
  color: #fff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-login:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-signup {
  padding: 10px 20px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-signup:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

.btn-logout {
  padding: 10px 20px;
  border: 1px solid rgba(255, 100, 100, 0.3);
  border-radius: 10px;
  background: transparent;
  color: rgba(255, 100, 100, 0.8);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: rgba(255, 100, 100, 0.1);
  border-color: rgba(255, 100, 100, 0.5);
  color: #ff6b6b;
}
</style>
