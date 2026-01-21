<template>
  <div class="file-list-container">
    <div class="file-table-wrapper">
      <table class="file-table">
        <colgroup>
          <col style="width: 60px">
          <col>
          <col style="width: 100px">
        </colgroup>
        <thead>
          <tr>
            <th class="text-center">序号</th>
            <th>文件</th>
            <th class="text-center">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(file, index) in files" :key="file.path">
            <td class="text-center col-index">{{ index + 1 }}</td>
            <td class="col-file">
              <div class="file-info">
                <div class="file-name" :title="file.name">
                  <span class="file-icon">📘</span>
                  {{ file.name }}
                </div>
                <div class="file-path" :title="file.path">{{ file.path }}</div>
              </div>
            </td>
            <td class="text-center">
              <span :class="['status-badge', 'status-' + (file.status || 'pending')]">
                {{ file.statusText || file.status || 'Pending' }}
              </span>
            </td>
          </tr>
          <tr v-if="files.length === 0">
            <td colspan="3">
              <div class="empty-state">
                <h3>暂无文件</h3>
                <p>请点击左侧按钮或拖拽文件到此处</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  files: {
    type: Array,
    required: true
  }
})
</script>

<style scoped>
.text-center {
  text-align: center;
}

.file-list-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
  height: 100%;
}

.file-table-wrapper {
  height: 100%;
  overflow: auto;
}

.file-table {
  table-layout: fixed;
  width: 100%;
  border-collapse: collapse;
}

.file-table th {
  padding: 10px 12px;
  height: 36px;
  line-height: 1.2;
  background-color: #f8f9fa;
  font-weight: 600;
  font-size: 0.85rem;
  color: #495057;
  border-bottom: 1px solid #e9ecef;
  position: sticky;
  top: 0;
  z-index: 1;
}

.file-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f1f3f5;
}

/* Hover effect */
.file-table tbody tr:hover td {
  background-color: #f8f9fa;
}

.col-index {
  color: #adb5bd;
  font-size: 0.85rem;
}

.col-file {
  padding: 0.75rem 1rem !important;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-icon {
  flex-shrink: 0;
  font-size: 1.2em;
}

.file-path {
  font-size: 0.8rem;
  color: #95a5a6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 28px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: #adb5bd;
  min-height: 200px;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
  color: #495057;
}

.empty-state p {
  margin: 0;
  font-size: 0.9rem;
}

/* Dark Mode Styles */
:global(.dark-mode) .file-list-container {
  background-color: #2d2d2d;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

:global(.dark-mode) .file-table th {
  background-color: #333;
  color: #ffffff;
  border-bottom-color: #444;
}

:global(.dark-mode) .file-table td {
  background-color: #2d2d2d;
  color: #ffffff;
  border-bottom-color: #444;
}

:global(.dark-mode) .file-name {
  color: #ffffff;
  font-weight: 600;
}

:global(.dark-mode) .file-path {
  color: #cccccc;
}

:global(.dark-mode) .empty-state {
  color: #cccccc;
}

:global(.dark-mode) .empty-state h3 {
  color: #ffffff;
}

:global(.dark-mode) .col-index {
  color: #bbbbbb;
}

:global(.dark-mode) .file-table tbody tr:hover td {
  background-color: #3a3a3a;
}
</style>

