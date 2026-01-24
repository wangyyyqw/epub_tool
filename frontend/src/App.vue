<template>
  <div id="app">
    <!-- Drag Overlay -->
    <div v-if="isDragging" class="drag-overlay">
      <div class="drag-content">
        <div class="drag-icon">📂</div>
        <div class="drag-text">释放以添加文件</div>
      </div>
    </div>

    <!-- Help Modal -->
    <HelpModal 
      v-if="showHelpModal" 
      @close="showHelpModal = false" 
    />

    <!-- Log Viewer Modal -->
    <div v-if="showLogModal" class="modal-overlay" @click.self="showLogModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>📋 运行日志</h3>
          <div class="modal-actions">
            <button class="btn-sm" @click="refreshLog" title="刷新日志">
              <span class="btn-icon">🔄</span> 刷新
            </button>
            <button class="btn-sm" @click="copyLog" title="复制日志">
              <span class="btn-icon">📋</span> 复制
            </button>
            <button class="btn-sm" @click="openLogExternal" title="外部打开日志">
              <span class="btn-icon">📤</span> 外部打开
            </button>
            <button class="btn-sm btn-close" @click="showLogModal = false" title="关闭">
              ✕
            </button>
          </div>
        </div>
        <div class="modal-body">
          <pre class="log-content">{{ logContent || '暂无日志内容' }}</pre>
        </div>
      </div>
    </div>

    <Sidebar
      @add-files="addFiles"
      @add-dir="addDir"
      @clear-files="clearFiles"
      @run-task="runTask"
    />

    <div class="main-content">
      <div class="top-bar">
        <div class="top-bar-right">
          <button class="btn-icon-only" @click="showHelpModal = true" title="使用说明">
            ❓
          </button>
          <button class="btn-icon-only" @click="toggleTheme" :title="currentTheme === 'dark' ? '切换到日间模式' : '切换到夜间模式'">
            {{ currentTheme === 'dark' ? '🌙' : '☀️' }}
          </button>
        </div>
      </div>

      <!-- File List Area -->
      <div class="content-body">
        <FileList :files="files" />
      </div>

      <!-- Status and Progress Area -->
      <div class="status-progress-container">
        <div class="status-progress-card">
          <!-- Output Directory Control -->
          <div class="output-control">
            <span class="label">📁 输出目录:</span>
            <span class="path" :title="outputDir || '默认 (源文件目录)'">
              {{ outputDir || '默认 (源文件目录)' }}
            </span>
            <button class="btn-sm" @click="selectOutputDir" title="选择输出目录">
              <span class="btn-icon">📁</span> 更改
            </button>
            <button class="btn-sm btn-text" v-if="outputDir" @click="outputDir = ''" title="重置输出目录">
              <span class="btn-icon">↺</span> 重置
            </button>
            <div class="app-status">
              <span class="status-indicator" :class="{ 'status-active': progress.current > 0 && progress.current < progress.total }"></span>
              {{ progress.current > 0 && progress.current < progress.total ? '处理中...' : '就绪' }}
            </div>
          </div>

          <!-- Progress Section with Log Button -->
          <div class="progress-section">
            <ProgressBar
              :current="progress.current"
              :total="progress.total"
              @open-log="openLogViewer"
            />
          </div>
        </div>
      </div>

      <!-- Log Console -->
      <div class="log-console-container">
        <LogConsole :logs="logs" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import FileList from './components/FileList.vue'
import LogConsole from './components/LogConsole.vue'
import ProgressBar from './components/ProgressBar.vue'
import HelpModal from './components/HelpModal.vue'
import { getCurrentTheme, applyTheme } from './themes.js'

import { SelectFiles, SelectDir, RunTask, GetLogContent, OpenLogFile } from '../wailsjs/go/main/App'
import { EventsOn } from '../wailsjs/runtime/runtime'

const files = ref([])
const logs = ref([])
const outputDir = ref('')
const progress = ref({ current: 0, total: 0 })
const isDragging = ref(false)
const showLogModal = ref(false)
const showHelpModal = ref(false)
const logContent = ref('')
let dragCounter = 0

const addFiles = async () => {
  try {
    const selected = await SelectFiles()
    if (selected && selected.length > 0) {
      appendFiles(selected)
    }
  } catch (e) {
    addLog('Error selecting files: ' + e, 'error')
  }
}

const addDir = async () => {
    try {
        const dir = await SelectDir()
        if (dir) {
            addLog("Folder added: " + dir, "info")
            appendFiles([dir]) 
        }
    } catch (e) {
        addLog('Error selecting dir: ' + e, 'error')
    }
}

const appendFiles = (pathList) => {
  pathList.forEach(path => {
    if (!files.value.find(f => f.path === path)) {
      files.value.push({
        name: path.split(/[\\/]/).pop(),
        path: path,
        size: 'Pending',
        status: 'pending',
        statusText: '未处理'
      })
    }
  })
}

const clearFiles = () => {
  files.value = []
  logs.value = []
  progress.value = { current: 0, total: 0 }
}

const selectOutputDir = async () => {
  const dir = await SelectDir()
  if (dir) outputDir.value = dir
}

const runTask = async (taskName) => {
  console.log("runTask called with:", taskName)
  if (files.value.length === 0) {
    alert("请先选择文件")
    return
  }

  // Intercept TXT to EPUB for preview
  if (taskName === 'txt_to_epub') {
    // Robust default rules matching user's likely content
    const rules = [
      { pattern: '^\\s*第[一二三四五六七八九十零〇百千两0-9]+[卷].*', level: 1 },
      { pattern: '^\\s*第[一二三四五六七八九十零〇百千两0-9]+[章].*', level: 2 },
      { pattern: '^\\s*第[一二三四五六七八九十零〇百千两0-9]+节.*', level: 3 },
      { pattern: '^\\s*Chapter\\s+[0-9]+.*', level: 2 },
      { pattern: '^\\s*[0-9]+\\..*', level: 2 }
    ]
    
    // Execute task directly with rules
    const extra = { rules: rules }
    await startTaskExecution(taskName, extra)
    return
  }

  await startTaskExecution(taskName, {})
}

const startTaskExecution = async (taskName, extra) => {
  const paths = files.value.map(f => f.path)
  progress.value = { current: 0, total: paths.length }

  files.value.forEach(f => {
      f.status = 'processing'
      f.statusText = '处理中'
  })

  addLog(`开始任务: ${taskName} - 共 ${paths.length} 个文件...`, 'info')

  try {
      console.log("Calling RunTask with:", paths, taskName, outputDir.value, JSON.stringify(extra))
      await RunTask(paths, taskName, outputDir.value, JSON.stringify(extra))
      console.log("RunTask completed")
  } catch(e) {
      console.error("Error in RunTask:", e)
      addLog("任务启动失败: " + e, 'error')
  }
}

const addLog = (msg, type='info') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ time, message: msg, type })
}

// Log Viewer Functions
const openLogViewer = async () => {
  showLogModal.value = true
  await refreshLog()
}

const refreshLog = async () => {
  try {
    logContent.value = await GetLogContent()
  } catch (e) {
    logContent.value = 'Error loading log: ' + e
  }
}

const openLogExternal = async () => {
  try {
    await OpenLogFile()
  } catch (e) {
    addLog('Error opening log file: ' + e, 'error')
  }
}

const copyLog = async () => {
  try {
    if (logContent.value) {
      await navigator.clipboard.writeText(logContent.value)
      addLog('日志已复制到剪贴板', 'success')
    } else {
      addLog('没有可复制的日志内容', 'warning')
    }
  } catch (e) {
    addLog('复制日志失败: ' + e, 'error')
  }
}

// Theme Functions
const currentTheme = ref(getCurrentTheme())

// Apply initial theme
onMounted(() => {
  applyTheme(currentTheme.value)
})

// Check system theme
const checkSystemTheme = () => {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    setTheme('dark')
  } else {
    setTheme('light')
  }
}

// Set theme
const setTheme = (themeName) => {
  currentTheme.value = themeName
  applyTheme(themeName)
}

// Theme Toggle Function
const toggleTheme = () => {
  const newTheme = currentTheme.value === 'light' ? 'dark' : 'light'
  setTheme(newTheme)
}

// Drag and Drop Handlers
const handleDragEnter = (e) => {
    e.preventDefault()
    dragCounter++
    if (dragCounter > 0) {
        isDragging.value = true
    }
}

const handleDragLeave = (e) => {
    e.preventDefault()
    dragCounter--
    if (dragCounter <= 0) {
        dragCounter = 0
        isDragging.value = false
    }
}

const handleDragOver = (e) => {
    e.preventDefault()
}

const handleDrop = (e) => {
    e.preventDefault()
    dragCounter = 0
    isDragging.value = false
}

onMounted(() => {
  // Apply initial theme
  applyTheme(currentTheme.value)

  // Add system theme change listener
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', checkSystemTheme)
  }

  EventsOn("task_log", (msg) => addLog(msg))

  EventsOn("task_result", (result) => {
    const fileObj = files.value.find(f => f.path === result.file)
    if (fileObj) {
      fileObj.status = result.status
      if (result.status === 'success') fileObj.statusText = '完成'
      else if (result.status === 'skip') fileObj.statusText = '跳过'
      else fileObj.statusText = '错误'
    }
  })

  EventsOn("task_complete", () => {
    addLog("所有任务已完成。", "success")
    // Update progress to completed state
    progress.value = { current: progress.value.total, total: progress.value.total }
    // Optionally clear file list after task completion - commented out for user visibility
    // setTimeout(() => {
    //   files.value = []
    //   progress.value = { current: 0, total: 0 }
    // }, 1500) // Delay 1.5s to allow user to see the completion status
  })

  EventsOn("task_progress", (data) => {
      if (data && typeof data.current === 'number') {
          progress.value = {
              current: data.current,
              total: data.total
          }
      }
  })

  // Listen for Wails drag and drop event
  EventsOn("file_drop", (paths) => {
      dragCounter = 0
      isDragging.value = false
      if(paths && paths.length > 0) {
          addLog(`收到拖拽文件: ${paths.length} 个`, 'info')
          appendFiles(paths)
      }
  })

  // Add global drag listeners for visual feedback only
  // File drop handling is done through Wails OnFileDrop event
  window.addEventListener('dragenter', handleDragEnter)
  window.addEventListener('dragleave', handleDragLeave)
  window.addEventListener('dragover', handleDragOver)
  window.addEventListener('drop', handleDrop)
})

onUnmounted(() => {
    window.removeEventListener('dragenter', handleDragEnter)
    window.removeEventListener('dragleave', handleDragLeave)
    window.removeEventListener('dragover', handleDragOver)
    window.removeEventListener('drop', handleDrop)

    // Remove system theme change listener
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', checkSystemTheme)
    }
})
</script>

<style scoped>
.content-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin-bottom: 0.75rem;
  min-height: 200px;
}

.status-progress-container {
  padding: 0;
  margin-bottom: 0.75rem;
}

.status-progress-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.output-control {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #495057;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.output-control .app-status {
  margin-left: auto;
  color: #adb5bd;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 5px;
}

.progress-section {
  border-top: 1px solid #e9ecef;
}

.log-console-container {
  margin-bottom: 0.75rem;
}

.output-control .label {
  font-weight: 600;
}

.output-control .path {
  background: #e9ecef;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 0.8rem;
  border-radius: 4px;
  border: 1px solid #ced4da;
  background: white;
  cursor: pointer;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-sm:hover {
  background: #e9ecef;
}

.btn-text {
  border: none;
  background: transparent;
  color: #868e96;
}

.btn-text:hover {
  background: transparent;
  color: #495057;
  text-decoration: underline;
}

.btn-icon-only {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #ced4da;
  background: white;
  cursor: pointer;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.btn-icon-only:hover {
  background: #f8f9fa;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.btn-icon-only:active {
  transform: translateY(0);
}

.top-bar {
  display: flex;
  justify-content: flex-end;
  width: 100%;
  margin-bottom: 1rem;
}

.top-bar-right {
  display: flex;
  gap: 10px;
}

:global(.dark-mode) .btn-icon-only {
  background: #343a40;
  border-color: #495057;
  color: #ffffff;
}

:global(.dark-mode) .btn-icon-only:hover {
  background: #495057;
  border-color: #6c757d;
}

.app-status {
  color: #adb5bd;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #28a745;
  opacity: 0.3;
}

.status-indicator.status-active {
  opacity: 1;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.3; }
  50% { opacity: 1; }
  100% { opacity: 0.3; }
}

/* Drag Overlay */
.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(52, 152, 219, 0.85);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
  animation: fadeIn 0.2s ease;
  pointer-events: none;
}

.drag-content {
  text-align: center;
  color: white;
  pointer-events: none;
}

.drag-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
  animation: bounce 1s infinite;
}

.drag-text {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 1px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 80%;
  max-width: 900px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #2c3e50;
}

.modal-actions {
  display: flex;
  gap: 8px;
}

.btn-close {
  width: 28px;
  height: 28px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 1rem;
}

.btn-icon {
  font-size: 0.9em;
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.log-content {
  margin: 0;
  padding: 1rem;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  min-height: 400px;
}

/* Dark Mode Styles - 已迁移到CSS变量 */
/* 这些样式现在通过CSS变量自动应用，无需单独定义 */
</style>
