import { defineStore } from 'pinia'
import { gamesApi } from '@/api/games'

export const useGamesStore = defineStore('games', {
    state: () => ({
        // 게임 목록들
        popularGames: [],
        topRatedGames: [],
        trendingGames: [],
        newReleases: [],
        saleGames: [],
        recommendations: [],

        // 위시리스트
        wishlist: [],

        // 검색 결과
        searchResults: [],
        searchQuery: '',

        // 현재 게임 상세
        currentGame: null,

        // 로딩 상태
        isLoading: false,

        // 활성 탭
        activeTab: 'discover'
    }),

    getters: {
        // 위시리스트에 있는지 확인
        isWishlisted: (state) => (gameId) => {
            return state.wishlist.some(g => g.id === gameId)
        },

        // 위시리스트 개수
        wishlistCount: (state) => state.wishlist.length
    },

    actions: {
        // 인기 게임 로드
        async fetchPopularGames(params = {}) {
            this.isLoading = true
            try {
                const data = await gamesApi.getPopularGames(params)
                this.popularGames = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 최고 평점 게임 로드
        async fetchTopRatedGames(params = {}) {
            this.isLoading = true
            try {
                const data = await gamesApi.getTopRatedGames(params)
                this.topRatedGames = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 트렌딩 게임 로드
        async fetchTrendingGames(params = {}) {
            this.isLoading = true
            try {
                const data = await gamesApi.getTrendingGames(params)
                this.trendingGames = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 신작 게임 로드
        async fetchNewReleases(params = {}) {
            this.isLoading = true
            try {
                const data = await gamesApi.getNewReleases(params)
                this.newReleases = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 세일 게임 로드
        async fetchSaleGames(params = {}) {
            this.isLoading = true
            try {
                const data = await gamesApi.getSaleGames(params)
                this.saleGames = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 추천 게임 로드
        async fetchRecommendations() {
            this.isLoading = true
            try {
                const data = await gamesApi.getRecommendations()
                this.recommendations = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 게임 검색
        async searchGames(query) {
            if (!query) {
                this.searchResults = []
                this.searchQuery = ''
                return
            }

            this.isLoading = true
            this.searchQuery = query
            try {
                const data = await gamesApi.searchGames(query)
                this.searchResults = data.results || data
            } finally {
                this.isLoading = false
            }
        },

        // 게임 상세 로드
        async fetchGameDetail(gameId) {
            this.isLoading = true
            try {
                this.currentGame = await gamesApi.getGameDetail(gameId)
            } finally {
                this.isLoading = false
            }
        },

        // 위시리스트 로드
        async fetchWishlist() {
            try {
                const data = await gamesApi.getWishlist()
                this.wishlist = data.results || data
            } catch (error) {
                console.error('Failed to fetch wishlist:', error)
            }
        },

        // 위시리스트 토글
        async toggleWishlist(game) {
            try {
                const result = await gamesApi.toggleWishlist(game.id)

                if (result.wishlisted) {
                    this.wishlist.push(game)
                } else {
                    this.wishlist = this.wishlist.filter(g => g.id !== game.id)
                }

                return result.wishlisted
            } catch (error) {
                console.error('Failed to toggle wishlist:', error)
                throw error
            }
        },

        // 게임 평점 주기
        async rateGame(gameId, score) {
            try {
                await gamesApi.rateGame(gameId, score)
                // 현재 게임 정보 업데이트
                if (this.currentGame?.id === gameId) {
                    this.currentGame.my_rating = score
                }
            } catch (error) {
                console.error('Failed to rate game:', error)
                throw error
            }
        },

        // 탭 변경
        setActiveTab(tab) {
            this.activeTab = tab
        }
    }
})
