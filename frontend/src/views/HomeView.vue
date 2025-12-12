<script setup>
import { ref, onMounted, computed } from 'vue'
import { useGamesStore } from '@/stores/games'
import { useAuthStore } from '@/stores/auth'
import GameCard from '@/components/GameCard.vue'
import TabNavigation from '@/components/TabNavigation.vue'

const gamesStore = useGamesStore()
const authStore = useAuthStore()

const activeTab = ref('discover')
const tabs = [
  { id: 'discover', name: '🎮 게임 발견', icon: '🎮' },
  { id: 'sale', name: '🏷️ 현재 세일', icon: '🏷️' },
  { id: 'recommend', name: '✨ 맞춤 추천', icon: '✨' },
  { id: 'community', name: '💬 커뮤니티', icon: '💬' }
]

const isLoading = computed(() => gamesStore.isLoading)
const popularGames = computed(() => gamesStore.popularGames)
const trendingGames = computed(() => gamesStore.trendingGames)
const newReleases = computed(() => gamesStore.newReleases)
const saleGames = computed(() => gamesStore.saleGames)
const recommendations = computed(() => gamesStore.recommendations)
const isAuthenticated = computed(() => authStore.isAuthenticated)

const changeTab = (tabId) => {
  activeTab.value = tabId
  loadTabData(tabId)
}

const loadTabData = async (tabId) => {
  switch (tabId) {
    case 'discover':
      await Promise.all([
        gamesStore.fetchPopularGames({ limit: 12 }),
        gamesStore.fetchTrendingGames({ limit: 12 }),
        gamesStore.fetchNewReleases({ limit: 12 })
      ])
      break
    case 'sale':
      await gamesStore.fetchSaleGames({ limit: 20 })
      break
    case 'recommend':
      if (isAuthenticated.value) {
        await gamesStore.fetchRecommendations()
      }
      break
  }
}

onMounted(() => {
  loadTabData('discover')
})
</script>

<template>
  <div class="home-view">
    <!-- Tab Navigation -->
    <TabNavigation 
      :tabs="tabs" 
      :activeTab="activeTab" 
      @change="changeTab" 
    />

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Discover Tab -->
      <div v-if="activeTab === 'discover'" class="discover-tab">
        <!-- Loading State -->
        <div v-if="isLoading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>게임을 불러오는 중...</p>
        </div>

        <template v-else>
          <!-- Popular Games Section -->
          <section class="game-section">
            <h2 class="section-title">
              <span class="title-icon">🔥</span>
              요즘 뜨는 게임
            </h2>
            <div class="game-grid">
              <GameCard 
                v-for="game in popularGames" 
                :key="game.id" 
                :game="game" 
              />
            </div>
          </section>

          <!-- Trending Games Section -->
          <section class="game-section">
            <h2 class="section-title">
              <span class="title-icon">⭐</span>
              최고 평점 게임
            </h2>
            <div class="game-grid">
              <GameCard 
                v-for="game in trendingGames" 
                :key="game.id" 
                :game="game" 
              />
            </div>
          </section>

          <!-- New Releases Section -->
          <section class="game-section">
            <h2 class="section-title">
              <span class="title-icon">🆕</span>
              신작 게임
            </h2>
            <div class="game-grid">
              <GameCard 
                v-for="game in newReleases" 
                :key="game.id" 
                :game="game" 
              />
            </div>
          </section>
        </template>
      </div>

      <!-- Sale Tab -->
      <div v-if="activeTab === 'sale'" class="sale-tab">
        <div v-if="isLoading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>세일 정보를 불러오는 중...</p>
        </div>

        <template v-else>
          <section class="game-section">
            <h2 class="section-title">
              <span class="title-icon">🏷️</span>
              현재 세일 중
            </h2>
            <div class="game-grid">
              <GameCard 
                v-for="game in saleGames" 
                :key="game.id" 
                :game="game"
                :showSaleInfo="true"
              />
            </div>
          </section>
        </template>
      </div>

      <!-- Recommend Tab -->
      <div v-if="activeTab === 'recommend'" class="recommend-tab">
        <div v-if="!isAuthenticated" class="auth-required">
          <div class="auth-icon">🔐</div>
          <h3>로그인이 필요합니다</h3>
          <p>맞춤 추천을 받으려면 로그인해주세요.</p>
          <RouterLink to="/login" class="btn-login">로그인하기</RouterLink>
        </div>

        <template v-else>
          <div v-if="isLoading" class="loading-state">
            <div class="loading-spinner"></div>
            <p>추천 게임을 분석하는 중...</p>
          </div>

          <section v-else class="game-section">
            <h2 class="section-title">
              <span class="title-icon">✨</span>
              당신을 위한 추천
            </h2>
            <div class="game-grid">
              <GameCard 
                v-for="game in recommendations" 
                :key="game.id" 
                :game="game"
                :showScore="true"
              />
            </div>
          </section>
        </template>
      </div>

      <!-- Community Tab -->
      <div v-if="activeTab === 'community'" class="community-tab">
        <div class="coming-soon">
          <div class="coming-soon-icon">🚧</div>
          <h3>커뮤니티 준비 중</h3>
          <p>곧 멋진 커뮤니티 기능이 추가됩니다!</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.tab-content {
  margin-top: 24px;
}

/* Game Section */
.game-section {
  margin-bottom: 48px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 20px;
}

.title-icon {
  font-size: 28px;
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: rgba(255, 255, 255, 0.7);
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Auth Required */
.auth-required {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.auth-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.auth-required h3 {
  font-size: 24px;
  color: #fff;
  margin-bottom: 10px;
}

.auth-required p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 24px;
}

.auth-required .btn-login {
  padding: 14px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
}

.auth-required .btn-login:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

/* Coming Soon */
.coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.coming-soon-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.coming-soon h3 {
  font-size: 24px;
  color: #fff;
  margin-bottom: 10px;
}

.coming-soon p {
  color: rgba(255, 255, 255, 0.6);
}
</style>
