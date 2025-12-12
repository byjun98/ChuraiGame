import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
    }),

    getters: {
        // 현재 사용자 이름
        username: (state) => state.user?.username || '',

        // Steam 연동 여부
        isSteamLinked: (state) => !!state.user?.steam_id,

        // 온보딩 완료 여부
        isOnboarded: (state) => state.user?.is_onboarded || false
    },

    actions: {
        // 로그인
        async login(username, password) {
            this.isLoading = true
            this.error = null

            try {
                const data = await authApi.login(username, password)
                localStorage.setItem('access_token', data.access)
                localStorage.setItem('refresh_token', data.refresh)

                await this.fetchUser()
                this.isAuthenticated = true
                return true
            } catch (error) {
                this.error = error.response?.data?.detail || '로그인에 실패했습니다.'
                return false
            } finally {
                this.isLoading = false
            }
        },

        // 회원가입
        async signup(userData) {
            this.isLoading = true
            this.error = null

            try {
                await authApi.signup(userData)
                // 회원가입 성공 후 자동 로그인
                return await this.login(userData.username, userData.password)
            } catch (error) {
                this.error = error.response?.data?.detail || '회원가입에 실패했습니다.'
                return false
            } finally {
                this.isLoading = false
            }
        },

        // 로그아웃
        async logout() {
            try {
                await authApi.logout()
            } finally {
                this.user = null
                this.isAuthenticated = false
            }
        },

        // 사용자 정보 조회
        async fetchUser() {
            try {
                this.user = await authApi.getCurrentUser()
                this.isAuthenticated = true
            } catch (error) {
                this.user = null
                this.isAuthenticated = false
            }
        },

        // 앱 시작 시 인증 상태 확인
        async initAuth() {
            const token = localStorage.getItem('access_token')
            if (token) {
                await this.fetchUser()
            }
        },

        // 프로필 업데이트
        async updateProfile(userData) {
            this.isLoading = true
            try {
                this.user = await authApi.updateProfile(userData)
                return true
            } catch (error) {
                this.error = error.response?.data?.detail || '프로필 업데이트에 실패했습니다.'
                return false
            } finally {
                this.isLoading = false
            }
        }
    }
})
