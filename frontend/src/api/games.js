import api from './index'

export const gamesApi = {
    // 인기 게임 목록
    async getPopularGames(params = {}) {
        const response = await api.get('/games/popular/', { params })
        return response.data
    },

    // 최고 평점 게임
    async getTopRatedGames(params = {}) {
        const response = await api.get('/games/top-rated/', { params })
        return response.data
    },

    // 트렌딩 게임
    async getTrendingGames(params = {}) {
        const response = await api.get('/games/trending/', { params })
        return response.data
    },

    // 신작 게임
    async getNewReleases(params = {}) {
        const response = await api.get('/games/new-releases/', { params })
        return response.data
    },

    // 출시 예정 게임
    async getUpcomingGames(params = {}) {
        const response = await api.get('/games/upcoming/', { params })
        return response.data
    },

    // 게임 검색
    async searchGames(query, limit = 20) {
        const response = await api.get('/games/search/', {
            params: { q: query, limit }
        })
        return response.data
    },

    // 게임 상세 정보
    async getGameDetail(gameId) {
        const response = await api.get(`/games/${gameId}/`)
        return response.data
    },

    // 장르별 게임
    async getGamesByGenre(genreSlug, params = {}) {
        const response = await api.get(`/games/genre/${genreSlug}/`, { params })
        return response.data
    },

    // 장르 목록
    async getGenres() {
        const response = await api.get('/games/genres/')
        return response.data
    },

    // 위시리스트 토글
    async toggleWishlist(gameId) {
        const response = await api.post(`/games/${gameId}/wishlist/`)
        return response.data
    },

    // 위시리스트 조회
    async getWishlist() {
        const response = await api.get('/games/wishlist/')
        return response.data
    },

    // 게임 평점 주기
    async rateGame(gameId, score) {
        const response = await api.post(`/games/${gameId}/rate/`, { score })
        return response.data
    },

    // 세일 게임 목록
    async getSaleGames(params = {}) {
        const response = await api.get('/games/sales/', { params })
        return response.data
    },

    // 맞춤 추천 게임
    async getRecommendations() {
        const response = await api.get('/games/recommendations/')
        return response.data
    }
}
