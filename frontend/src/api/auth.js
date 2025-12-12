import api from './index'

export const authApi = {
    // 로그인
    async login(username, password) {
        const response = await api.post('/auth/token/', { username, password })
        return response.data
    },

    // 회원가입
    async signup(userData) {
        const response = await api.post('/auth/signup/', userData)
        return response.data
    },

    // 로그아웃
    async logout() {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
            await api.post('/auth/logout/', { refresh: refreshToken })
        }
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
    },

    // 현재 사용자 정보 조회
    async getCurrentUser() {
        const response = await api.get('/auth/user/')
        return response.data
    },

    // 프로필 업데이트
    async updateProfile(userData) {
        const response = await api.patch('/auth/user/', userData)
        return response.data
    },

    // Steam 연동
    async linkSteam(steamId) {
        const response = await api.post('/auth/link-steam/', { steam_id: steamId })
        return response.data
    }
}
