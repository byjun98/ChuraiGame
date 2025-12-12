<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGamesStore } from '@/stores/games'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  game: {
    type: Object,
    required: true
  },
  showSaleInfo: {
    type: Boolean,
    default: false
  },
  showScore: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()
const gamesStore = useGamesStore()
const authStore = useAuthStore()

const isWishlisted = computed(() => gamesStore.isWishlisted(props.game.id))

const handleClick = () => {
  router.push({ name: 'game-detail', params: { id: props.game.id } })
}

const handleWishlist = async (e) => {
  e.stopPropagation()
  
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  
  await gamesStore.toggleWishlist(props.game)
}

const formatRating = (rating) => {
  return rating ? rating.toFixed(1) : 'N/A'
}

const formatDiscount = (discount) => {
  return `-${Math.round(discount)}%`
}
</script>

<template>
  <div class="game-card" @click="handleClick">
    <!-- Image -->
    <div class="card-image">
      <img 
        :src="game.background_image || '/placeholder-game.jpg'" 
        :alt="game.name"
        loading="lazy"
      />
      
      <!-- Sale Badge -->
      <div v-if="showSaleInfo && game.discount" class="sale-badge">
        {{ formatDiscount(game.discount) }}
      </div>
      
      <!-- Rating Badge -->
      <div v-if="game.metacritic" class="rating-badge">
        {{ game.metacritic }}
      </div>

      <!-- Wishlist Button -->
      <button 
        class="btn-wishlist"
        :class="{ 'is-active': isWishlisted }"
        @click="handleWishlist"
      >
        <span v-if="isWishlisted">❤️</span>
        <span v-else>🤍</span>
      </button>
    </div>

    <!-- Content -->
    <div class="card-content">
      <h3 class="game-title">{{ game.name }}</h3>
      
      <!-- Genres -->
      <div class="game-genres" v-if="game.genres?.length">
        <span 
          v-for="genre in game.genres.slice(0, 2)" 
          :key="genre.id"
          class="genre-tag"
        >
          {{ genre.name }}
        </span>
      </div>

      <!-- Rating -->
      <div class="game-rating" v-if="game.rating">
        <span class="stars">
          <span 
            v-for="i in 5" 
            :key="i"
            :class="{ filled: i <= Math.round(game.rating) }"
          >★</span>
        </span>
        <span class="rating-value">{{ formatRating(game.rating) }}</span>
      </div>

      <!-- Sale Price -->
      <div v-if="showSaleInfo && game.sale_price" class="price-info">
        <span class="original-price">₩{{ game.original_price?.toLocaleString() }}</span>
        <span class="sale-price">₩{{ game.sale_price?.toLocaleString() }}</span>
      </div>

      <!-- Recommendation Score -->
      <div v-if="showScore && game.recommendation_score" class="rec-score">
        추천 점수: {{ Math.round(game.recommendation_score) }}점
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s, border-color 0.3s;
}

.game-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  border-color: rgba(102, 126, 234, 0.5);
}

.card-image {
  position: relative;
  aspect-ratio: 16/9;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.game-card:hover .card-image img {
  transform: scale(1.05);
}

.sale-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.rating-badge {
  position: absolute;
  top: 12px;
  right: 50px;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.btn-wishlist {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: transform 0.2s, background 0.2s;
}

.btn-wishlist:hover {
  transform: scale(1.1);
  background: rgba(0, 0, 0, 0.8);
}

.btn-wishlist.is-active {
  background: rgba(255, 100, 100, 0.3);
}

.card-content {
  padding: 16px;
}

.game-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.game-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.genre-tag {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
}

.game-rating {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stars {
  color: rgba(255, 255, 255, 0.2);
  font-size: 14px;
  letter-spacing: 2px;
}

.stars .filled {
  color: #ffc107;
}

.rating-value {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.price-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.original-price {
  color: rgba(255, 255, 255, 0.4);
  text-decoration: line-through;
  font-size: 13px;
}

.sale-price {
  color: #4cd964;
  font-weight: 700;
  font-size: 16px;
}

.rec-score {
  margin-top: 10px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-radius: 8px;
  color: #667eea;
  font-size: 12px;
  font-weight: 500;
}
</style>
