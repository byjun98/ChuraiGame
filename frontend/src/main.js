import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

// Pinia 스토어 생성
const pinia = createPinia()

// Vue 앱 생성 및 마운트
const app = createApp(App)

app.use(pinia)
app.use(router)

// 앱 시작 시 인증 상태 확인
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.initAuth()

app.mount('#app')
