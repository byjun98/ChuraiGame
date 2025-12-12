import axios from 'axios'

// API 기본 설정
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
})

// Request Interceptor - 토큰 자동 추가
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response Interceptor - 토큰 만료 처리
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // 401 에러이고 재시도하지 않은 요청이면 토큰 갱신 시도
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            try {
                const refreshToken = localStorage.getItem('refresh_token')
                if (refreshToken) {
                    const response = await axios.post(
                        `${api.defaults.baseURL}/auth/token/refresh/`,
                        { refresh: refreshToken }
                    )

                    const { access } = response.data
                    localStorage.setItem('access_token', access)

                    originalRequest.headers.Authorization = `Bearer ${access}`
                    return api(originalRequest)
                }
            } catch (refreshError) {
                // 리프레시 토큰도 만료됨 - 로그아웃 처리
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                window.location.href = '/login'
            }
        }

        return Promise.reject(error)
    }
)

export default api
