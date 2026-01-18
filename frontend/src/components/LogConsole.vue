<template>
  <div class="log-container card">
    <div class="log-header">
      <span class="log-title">运行日志</span>
      <span class="log-count">{{ logs.length }} 条记录</span>
    </div>
    <div class="log-console" ref="consoleRef">
      <div v-for="(log, index) in logs" :key="index" class="log-entry">
        <span class="log-time">{{ log.time }}</span>
        <span :class="['log-msg', 'log-' + log.type]">{{ log.message }}</span>
      </div>
      <div v-if="logs.length === 0" class="log-empty">
        暂无日志...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    required: true
  }
})

const consoleRef = ref(null)

watch(() => props.logs.length, () => {
  nextTick(() => {
    if (consoleRef.value) {
      consoleRef.value.scrollTop = consoleRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.log-container {
  display: flex;
  flex-direction: column;
  height: 200px;
  background-color: #2b2b2b;
  flex-shrink: 0;
  border-radius: var(--radius);
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: #1e1e1e;
  border-bottom: 1px solid #333;
  color: #888;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-console {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.log-entry {
  display: flex;
  margin-bottom: 4px;
}

.log-time {
  color: #666;
  margin-right: 10px;
  min-width: 65px;
  user-select: none;
}

.log-msg {
  color: #d4d4d4;
  word-break: break-all;
}

.log-error {
  color: #ff6b6b;
}

.log-success {
  color: #69db7c;
}

.log-warning {
  color: #ffd43b;
}

.log-empty {
  color: #555;
  text-align: center;
  padding-top: 2rem;
  font-style: italic;
}

/* Scrollbar for dark theme */
.log-console::-webkit-scrollbar {
  width: 10px;
}
.log-console::-webkit-scrollbar-track {
  background: #1e1e1e;
}
.log-console::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 5px;
  border: 2px solid #1e1e1e;
}
</style>
