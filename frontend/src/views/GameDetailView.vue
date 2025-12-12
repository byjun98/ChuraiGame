<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGamesStore } from '@/stores/games'

const route = useRoute()
const gamesStore = useGamesStore()

const game = computed(() => gamesStore.currentGame)
const isLoading = computed(() => gamesStore.isLoading)

onMounted(() => {
  const gameId = route.params.id
  gamesStore.fetchGameDetail(gameId)
})
</script>

<template>
  <div class="game-detail-view">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>게임 정보를 불러오는 중...</p>
    </div>

    <template v-else-if="game">
      <!-- Hero Section -->
      <section class="hero-section">
        <div 
          class="hero-background" 
          :style="{ backgroundImage: `url(${game.background_image})` }"
        ></div>
        <div class="hero-content">
          <h1>{{ game.name }}</h1>
          <div class="game-meta">
            <span v-if="game.released" class="meta-item">
              📅 {{ game.released }}
            </span>
            <span v-if="game.metacritic" class="meta-item metacritic">
              ⭐ Metacritic: {{ game.metacritic }}
            </span>
            <span v-if="game.playtime" class="meta-item">
              ⏱️ 평균 {{ game.playtime }}시간
            </span>
          </div>
          <div class="game-genres">
            <span 
              v-for="genre in game.genres" 
              :key="genre.id"
              class="genre-tag"
            >
              {{ genre.name }}
            </span>
          </div>
        </div>
      </section>

      <!-- Actions -->
      <section class="actions-section">
        <button class="btn-wishlist">
          ❤️ 위시리스트에 추가
        </button>
        <a 
          v-if="game.steam_app_id"
          :href="`https://store.steampowered.com/app/${game.steam_app_id}`"
          target="_blank"
          class="btn-store"
        >
          🎮 Steam에서 보기
        </a>
      </section>

      <!-- Description -->
      <section class="description-section">
        <h2>게임 소개</h2>
        <div class="description" v-html="game.description"></div>
      </section>

      <!-- Screenshots -->
      <section v-if="game.screenshots?.length" class="screenshots-section">
        <h2>스크린샷</h2>
        <div class="screenshots-grid">
          <img 
            v-for="(screenshot, index) in game.screenshots" 
            :key="index"
            :src="screenshot.image"
            :alt="`${game.name} 스크린샷 ${index + 1}`"
          />
        </div>
      </section>

      <!-- Platforms -->
      <section v-if="game.platforms?.length" class="platforms-section">
        <h2>플랫폼</h2>
        <div class="platforms-list">
          <span 
            v-for="platform in game.platforms" 
            :key="platform.platform.id"
            class="platform-tag"
          >
            {{ platform.platform.name }}
          </span>
        </div>
      </section>
    </template>

    <!-- Not Found -->
    <div v-else class="not-found">
      <span class="not-found-icon">🎮</span>
      <h2>게임을 찾을 수 없습니다</h2>
      <RouterLink to="/" class="btn-home">홈으로 돌아가기</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.game-detail-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 60px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
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

/* Hero Section */
.hero-section {
  position: relative;
  height: 450px;
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 24px;
}

.hero-background {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  filter: brightness(0.4);
}

.hero-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 40px;
}

.hero-content h1 {
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 16px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.game-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}

.meta-item {
  color: rgba(255, 255, 255, 0.8);
  font-size: 15px;
}

.metacritic {
  background: rgba(102, 126, 234, 0.3);
  padding: 4px 12px;
  border-radius: 8px;
}

.game-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.genre-tag {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  color: #fff;
  font-size: 13px;
}

/* Actions */
.actions-section {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
}

.btn-wishlist {
  padding: 14px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-wishlist:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.btn-store {
  padding: 14px 28px;
  background: #1b2838;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-store:hover {
  background: #2a475e;
}

/* Sections */
.description-section,
.screenshots-section,
.platforms-section {
  margin-bottom: 40px;
}

.description-section h2,
.screenshots-section h2,
.platforms-section h2 {
  font-size: 22px;
  color: #fff;
  margin-bottom: 16px;
}

.description {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.8;
  font-size: 15px;
}

.screenshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.screenshots-grid img {
  width: 100%;
  border-radius: 12px;
  transition: transform 0.2s;
}

.screenshots-grid img:hover {
  transform: scale(1.02);
}

.platforms-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.platform-tag {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

/* Not Found */
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.not-found-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.not-found h2 {
  color: #fff;
  margin-bottom: 20px;
}

.btn-home {
  padding: 14px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
}
</style>
