<script setup>
</script>

<template>
  <footer class="footer">
    <div class="footer-content">
      <div class="footer-brand">
        <span class="footer-logo">🎮 ChuraiGame</span>
        <p class="footer-desc">최고의 게임 추천 플랫폼</p>
      </div>
      
      <div class="footer-links">
        <a href="#" class="footer-link">이용약관</a>
        <a href="#" class="footer-link">개인정보처리방침</a>
        <a href="#" class="footer-link">문의하기</a>
      </div>
      
      <div class="footer-copyright">
        <p>© 2024 ChuraiGame. SSAFY 관통 프로젝트.</p>
        <p class="footer-api">Powered by RAWG API & CheapShark</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: rgba(10, 10, 20, 0.95);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 40px 24px;
  margin-top: auto;
}

.footer-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.footer-logo {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.footer-desc {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-link {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.footer-link:hover {
  color: #fff;
}

.footer-copyright {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.footer-api {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.3);
}
</style>
