<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useGamesStore } from '@/stores/games'

const authStore = useAuthStore()
const gamesStore = useGamesStore()

const user = computed(() => authStore.user)
const wishlist = computed(() => gamesStore.wishlist)
const isSteamLinked = computed(() => authStore.isSteamLinked)

onMounted(() => {
  gamesStore.fetchWishlist()
})
</script>

<template>
  <div class="profile-view">
    <div class="profile-container">
      <!-- Profile Header -->
      <section class="profile-header">
        <div class="avatar-container">
          <div class="avatar">
            {{ user?.username?.[0]?.toUpperCase() || '?' }}
          </div>
          <div class="steam-badge" v-if="isSteamLinked">
            🎮 Steam 연동됨
          </div>
        </div>
        <div class="profile-info">
          <h1>{{ user?.username }}</h1>
          <p class="profile-email">{{ user?.email }}</p>
          <div class="profile-stats">
            <div class="stat-item">
              <span class="stat-value">{{ wishlist.length }}</span>
              <span class="stat-label">위시리스트</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ user?.rated_games_count || 0 }}</span>
              <span class="stat-label">평가한 게임</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Steam Connection -->
      <section class="profile-section">
        <h2>Steam 연동</h2>
        <div class="steam-card">
          <template v-if="isSteamLinked">
            <div class="steam-connected">
              <span class="steam-icon">✅</span>
              <div>
                <strong>Steam 계정이 연동되어 있습니다</strong>
                <p>Steam 라이브러리 기반 추천을 받을 수 있습니다.</p>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="steam-not-connected">
              <span class="steam-icon">🎮</span>
              <div>
                <strong>Steam 계정을 연동하세요</strong>
                <p>Steam 라이브러리를 기반으로 더 정확한 추천을 받을 수 있습니다.</p>
              </div>
              <button class="btn-link-steam">Steam 연동</button>
            </div>
          </template>
        </div>
      </section>

      <!-- Wishlist -->
      <section class="profile-section">
        <h2>위시리스트</h2>
        <div v-if="wishlist.length === 0" class="empty-state">
          <span class="empty-icon">📋</span>
          <p>위시리스트가 비어있습니다</p>
        </div>
        <div v-else class="wishlist-grid">
          <div 
            v-for="game in wishlist" 
            :key="game.id"
            class="wishlist-item"
          >
            <img :src="game.background_image" :alt="game.name" />
            <div class="wishlist-item-info">
              <h4>{{ game.name }}</h4>
              <RouterLink :to="`/games/${game.id}`" class="btn-view">
                상세보기
              </RouterLink>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.profile-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 24px;
}

.profile-header {
  display: flex;
  gap: 32px;
  padding: 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  margin-bottom: 32px;
}

.avatar-container {
  position: relative;
}

.avatar {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: 700;
  color: #fff;
}

.steam-badge {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  background: #1b2838;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 11px;
  color: #fff;
  white-space: nowrap;
}

.profile-info {
  flex: 1;
}

.profile-info h1 {
  font-size: 32px;
  color: #fff;
  margin-bottom: 8px;
}

.profile-email {
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 20px;
}

.profile-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.profile-section {
  margin-bottom: 32px;
}

.profile-section h2 {
  font-size: 20px;
  color: #fff;
  margin-bottom: 16px;
}

.steam-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.steam-connected,
.steam-not-connected {
  display: flex;
  align-items: center;
  gap: 16px;
}

.steam-icon {
  font-size: 36px;
}

.steam-connected strong,
.steam-not-connected strong {
  color: #fff;
  display: block;
  margin-bottom: 4px;
}

.steam-connected p,
.steam-not-connected p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.btn-link-steam {
  margin-left: auto;
  padding: 12px 24px;
  background: #1b2838;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-link-steam:hover {
  background: #2a475e;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px;
  color: rgba(255, 255, 255, 0.5);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.wishlist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.wishlist-item {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16/9;
}

.wishlist-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wishlist-item-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.9));
}

.wishlist-item h4 {
  color: #fff;
  font-size: 16px;
  margin-bottom: 8px;
}

.btn-view {
  display: inline-block;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #fff;
  text-decoration: none;
  font-size: 13px;
  transition: background 0.2s;
}

.btn-view:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
