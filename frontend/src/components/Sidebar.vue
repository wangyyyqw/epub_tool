<template>
  <div class="sidebar">
    <div class="sidebar-title">Epub Tool</div>

    <div class="sidebar-group">
      <div class="sidebar-group-title">文件操作</div>
      <div class="sidebar-group-buttons">
        <button class="btn" @click="$emit('add-files')">添加文件</button>
        <button class="btn" @click="$emit('add-dir')">添加文件夹</button>
        <button class="btn btn-danger" @click="$emit('clear-files')">清空列表</button>
      </div>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-title">常用</div>
      <div class="sidebar-group-buttons">
        <button class="btn" @click="$emit('run-task', 'reformat')">格式化</button>
      </div>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-title">安全</div>
      <div class="sidebar-group-buttons">
        <button class="btn" @click="$emit('run-task', 'decrypt')">文件解密</button>
        <button class="btn" @click="$emit('run-task', 'encrypt')">文件加密</button>
      </div>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-title">字体</div>
      <div class="sidebar-group-buttons">
        <button class="btn" @click="$emit('run-task', 'font_encrypt')">字体加密</button>
        <button class="btn" @click="$emit('run-task', 'font_subset')">字体子集化</button>
      </div>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-title">图片</div>
      <div class="sidebar-group-buttons">
        <button class="btn" @click="$emit('run-task', 'img_to_webp')">图片转WebP</button>
        <button class="btn" @click="$emit('run-task', 'webp_to_img')">WebP还原</button>
        <button class="btn" @click="$emit('run-task', 'img_compress')">图片压缩</button>
      </div>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-title">文本</div>
      <div class="sidebar-group-buttons">
        <button class="btn" @click="$emit('run-task', 's2t')">简转繁</button>
        <button class="btn" @click="$emit('run-task', 't2s')">繁转简</button>
        <button class="btn" @click="$emit('run-task', 'add_pinyin')">生僻字注音</button>
        <button class="btn" @click="$emit('run-task', 'yuewei_to_duokan')">阅微转多看</button>
      </div>
    </div>

  </div>
</template>

<script setup>
defineEmits(['add-files', 'add-dir', 'clear-files', 'run-task'])
</script>
