<script setup>
const props = defineProps({
  tabs: {
    type: Array,
    required: true
  },
  activeTab: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['change'])

const handleTabClick = (tabId) => {
  emit('change', tabId)
}
</script>

<template>
  <nav class="tab-navigation">
    <div class="tab-container">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-button"
        :class="{ 'is-active': activeTab === tab.id }"
        @click="handleTabClick(tab.id)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-name">{{ tab.name }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.tab-navigation {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 8px;
}

.tab-container {
  display: flex;
  gap: 8px;
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 20px;
  background: transparent;
  border: none;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-button:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

.tab-button.is-active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  color: #fff;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
}

.tab-icon {
  font-size: 18px;
}

.tab-name {
  display: inline;
}

/* Responsive */
@media (max-width: 768px) {
  .tab-button {
    padding: 12px;
  }
  
  .tab-name {
    display: none;
  }
  
  .tab-icon {
    font-size: 22px;
  }
}
</style>
