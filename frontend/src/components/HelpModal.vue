<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <div class="header-title">
          <span class="header-icon">📘</span>
          <h3>使用说明</h3>
        </div>
        <button class="btn-icon-close" @click="close" title="关闭">✕</button>
      </div>
      
      <div class="modal-body">
        <div class="help-grid">
          <!-- Basic Operations - Full Width -->
          <div class="help-card full-width">
            <div class="card-header">
              <span class="card-icon">⚡</span>
              <h4>基本操作</h4>
            </div>
            <div class="card-body basic-ops-grid">
              <div class="ops-item">
                <div class="ops-icon">📂</div>
                <div class="ops-text">
                  <span class="ops-title">添加文件</span>
                  <span class="ops-desc">点击按钮或拖拽文件入窗</span>
                </div>
              </div>
              <div class="ops-item">
                <div class="ops-icon">🗑️</div>
                <div class="ops-text">
                  <span class="ops-title">清空列表</span>
                  <span class="ops-desc">一键清除待处理文件</span>
                </div>
              </div>
              <div class="ops-item">
                <div class="ops-icon">💾</div>
                <div class="ops-text">
                  <span class="ops-title">输出目录</span>
                  <span class="ops-desc">默认源目录，支持自定义</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Common & Safety -->
          <div class="help-card">
            <div class="card-header">
              <span class="card-icon">🛡️</span>
              <h4>常用 & 安全</h4>
            </div>
            <div class="card-body">
              <ul class="feature-list">
                <li><span class="dot"></span><strong>格式化：</strong>规范化 EPUB 结构，修复错误</li>
                <li><span class="dot"></span><strong>文件解密：</strong>解除 EPUB 文件保护</li>
                <li><span class="dot"></span><strong>文件加密：</strong>对文件进行加密保护</li>
              </ul>
            </div>
          </div>

          <!-- Font Tools -->
          <div class="help-card">
            <div class="card-header">
              <span class="card-icon">🔤</span>
              <h4>字体工具</h4>
            </div>
            <div class="card-body">
              <ul class="feature-list">
                <li><span class="dot"></span><strong>字体加密：</strong>混淆内嵌字体文件</li>
                <li><span class="dot"></span><strong>字体子集化：</strong>移除未用字符，减小体积</li>
              </ul>
            </div>
          </div>

          <!-- Image Tools -->
          <div class="help-card">
            <div class="card-header">
              <span class="card-icon">🖼️</span>
              <h4>图片工具</h4>
            </div>
            <div class="card-body">
              <ul class="feature-list">
                <li><span class="dot"></span><strong>转 WebP：</strong>图片转 WebP，大幅瘦身</li>
                <li><span class="dot"></span><strong>WebP 还原：</strong>转回 JPG/PNG 兼容老设备</li>
                <li><span class="dot"></span><strong>图片压缩：</strong>无损或有损压缩图片</li>
              </ul>
            </div>
          </div>

          <!-- Text Tools -->
          <div class="help-card">
            <div class="card-header">
              <span class="card-icon">📝</span>
              <h4>文本工具</h4>
            </div>
            <div class="card-body">
              <ul class="feature-list">
                <li><span class="dot"></span><strong>简繁转换：</strong>书籍内容简繁体互转</li>
                <li><span class="dot"></span><strong>生僻字注音：</strong>自动为生僻字添加拼音</li>
                <li><span class="dot"></span><strong>阅微转多看：</strong>转换注释为多看弹注格式</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn-primary" @click="close">我明白了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-content {
  background-color: var(--help-modal-content-bg);
  border-radius: 16px;
  width: 85%;
  max-width: 850px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid var(--help-modal-header-border);
  background-color: var(--help-modal-header-bg);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 1.5rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.btn-icon-close {
  background-color: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1.25rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon-close:hover {
  background-color: #f1f5f9;
  color: #ef4444;
}

/* Body */
.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  background-color: var(--help-modal-body-bg);
}

.help-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.2rem;
}

.help-card {
  background-color: var(--help-modal-card-bg);
  border-radius: 10px;
  border: 1px solid var(--help-modal-card-border);
  padding: 1.2rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.help-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
  border-color: #cbd5e1;
}

.full-width {
  grid-column: span 2;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--help-modal-header-border);
}

.card-icon {
  font-size: 1.4rem;
}

.help-card h4 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: #334155;
}

/* Basic Ops Grid */
.basic-ops-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.ops-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.ops-icon {
  font-size: 1.5rem;
  padding-top: 2px;
}

.ops-text {
  display: flex;
  flex-direction: column;
}

.ops-title {
  font-weight: 600;
  color: #475569;
  font-size: 0.95rem;
  margin-bottom: 2px;
}

.ops-desc {
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.3;
}

/* Feature List */
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  position: relative;
  padding-left: 1.2rem;
  margin-bottom: 0.6rem;
  font-size: 0.9rem;
  color: #64748b;
  line-height: 1.5;
}

.feature-list li:last-child {
  margin-bottom: 0;
}

.dot {
  position: absolute;
  left: 0;
  top: 9px;
  width: 6px;
  height: 6px;
  background-color: #3b82f6;
  border-radius: 50%;
}

.feature-list strong {
  color: #475569;
  margin-right: 4px;
}

/* Footer */
.modal-footer {
  padding: 1rem 1.5rem;
  background-color: var(--help-modal-footer-bg);
  border-top: 1px solid var(--help-modal-footer-border);
  display: flex;
  justify-content: flex-end;
}

.btn-primary {
  padding: 0.6rem 1.5rem;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.95rem;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Dark Mode Styles */
:global([data-theme="dark"]) .modal-content {
  background-color: var(--help-modal-content-bg);
  border: 1px solid var(--help-modal-card-border);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

:global([data-theme="dark"]) .modal-header {
  background-color: var(--help-modal-header-bg);
  border-bottom-color: var(--help-modal-header-border);
}

:global([data-theme="dark"]) .modal-body {
  background-color: var(--help-modal-body-bg);
}

:global([data-theme="dark"]) .btn-icon-close {
  color: #64748b;
}

:global([data-theme="dark"]) .btn-icon-close:hover {
  background-color: var(--help-modal-card-border);
  color: #ef4444;
}

:global([data-theme="dark"]) .help-card {
  background-color: var(--help-modal-card-bg);
  border-color: var(--help-modal-card-border);
}

:global([data-theme="dark"]) .help-card:hover {
  border-color: #475569;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
}

:global([data-theme="dark"]) .card-header {
  border-bottom-color: var(--help-modal-header-border);
}

:global([data-theme="dark"]) .help-card h4 {
  color: #e2e8f0;
}

:global([data-theme="dark"]) .ops-title {
  color: #cbd5e1;
}

:global([data-theme="dark"]) .ops-desc {
  color: #94a3b8;
}

:global([data-theme="dark"]) .feature-list li {
  color: #94a3b8;
}

:global([data-theme="dark"]) .feature-list strong {
  color: #cbd5e1;
}

:global([data-theme="dark"]) .dot {
  background-color: #60a5fa;
}

:global([data-theme="dark"]) .modal-footer {
  background-color: var(--help-modal-footer-bg);
  border-top-color: var(--help-modal-footer-border);
}

:global([data-theme="dark"]) .btn-primary {
  background-color: #3b82f6;
}

:global([data-theme="dark"]) .btn-primary:hover {
  background-color: #2563eb;
}
</style>