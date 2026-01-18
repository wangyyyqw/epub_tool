<template>
  <div class="progress-container">
    <div class="progress-row">
      <div class="progress-main">
        <div class="progress-info">
          <span>进度</span>
          <span>{{ percent }}%</span>
        </div>
        <div class="progress-bar-bg">
          <div 
            class="progress-bar-fill" 
            :style="{ width: percent + '%' }"
            :class="{ 'progress-complete': percent === 100 }"
          ></div>
        </div>
        <div class="progress-details" v-if="total > 0">
          正在处理: {{ current }} / {{ total }}
        </div>
      </div>
      <button class="log-btn" @click="$emit('open-log')" title="查看日志">
        日志
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: {
    type: Number,
    default: 0
  },
  total: {
    type: Number,
    default: 0
  }
})

defineEmits(['open-log'])

const percent = computed(() => {
  if (props.total === 0) return 0
  return Math.floor((props.current / props.total) * 100)
})
</script>

<style scoped>
.progress-container {
  padding: 0.75rem 1rem;
  background-color: transparent;
  flex-shrink: 0;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-main {
  flex: 1;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #495057;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.progress-bar-bg {
  height: 8px;
  background-color: #f1f3f5;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background-color: #007bff;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-complete {
  background-color: #28a745;
}

.progress-details {
  text-align: right;
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.5rem;
}

.log-btn {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  background: #f8f9fa;
  cursor: pointer;
  color: #495057;
  white-space: nowrap;
  transition: all 0.2s;
}

.log-btn:hover {
  background: #e9ecef;
  border-color: #ced4da;
}

/* Dark Mode Styles */
:global(.dark-mode) .progress-info {
  color: #e0e0e0;
}

:global(.dark-mode) .progress-bar-bg {
  background-color: #444;
}

:global(.dark-mode) .progress-details {
  color: #9e9e9e;
}

:global(.dark-mode) .log-btn {
  border-color: #444;
  background: #333;
  color: #e0e0e0;
}

:global(.dark-mode) .log-btn:hover {
  background: #444;
  border-color: #555;
}
</style>
