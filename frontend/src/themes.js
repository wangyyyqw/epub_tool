// 主题配置文件
export const themes = {
  light: {
    // 基础颜色
    'primary-color': '#3498db',
    'primary-hover': '#2980b9',
    'secondary-color': '#f8f9fa',
    'text-color': '#2c3e50',
    'text-light': '#7f8c8d',
    'bg-color': '#ffffff',
    'border-color': '#e9ecef',
    
    // 状态颜色
    'success-color': '#27ae60',
    'warning-color': '#f39c12',
    'error-color': '#e74c3c',
    
    // 组件颜色
    'sidebar-bg-start': '#f8fafc',
    'sidebar-bg-end': '#edf2f7',
    'card-bg': '#fff',
    'file-table-header-bg': '#fff',
    'file-table-row-hover': '#f8fbff',
    
    // 状态徽章颜色
    'status-pending-bg': '#f1f3f5',
    'status-pending-color': '#adb5bd',
    'status-processing-bg': '#e3f2fd',
    'status-processing-color': '#3498db',
    'status-success-bg': '#e8f5e9',
    'status-success-color': '#27ae60',
    'status-error-bg': '#ffebee',
    'status-error-color': '#e74c3c',
    'status-skip-bg': '#fff8e1',
    'status-skip-color': '#f39c12',
    
    // 滚动条颜色
    'scrollbar-thumb': '#d1d5db',
    'scrollbar-thumb-hover': '#9ca3af',
    
    // 模态框颜色
    'modal-overlay-bg': 'rgba(0, 0, 0, 0.4)',
    'modal-content-bg': '#ffffff',
    'modal-header-border': '#f1f5f9',
    'modal-header-bg': '#ffffff',
    'modal-body-bg': '#f8fafc',
    'modal-footer-bg': '#f8f9fa',
    'modal-footer-border': '#f1f5f9',
    
    // 帮助模态框颜色
    'help-modal-content-bg': '#ffffff',
    'help-modal-header-bg': '#ffffff',
    'help-modal-body-bg': '#f8fafc',
    'help-modal-card-bg': '#ffffff',
    'help-modal-card-border': '#e2e8f0',
    'help-modal-header-border': '#f1f5f9',
    'help-modal-footer-bg': '#ffffff',
    'help-modal-footer-border': '#f1f5f9',
    
    // 其他
    'shadow-sm': '0 2px 4px rgba(0,0,0,0.08)',
    'shadow-md': '0 6px 12px rgba(0,0,0,0.12)',
  },
  
  dark: {
    // 基础颜色
    'primary-color': '#42a5f5',
    'primary-hover': '#1e88e5',
    'secondary-color': '#1e1e1e',
    'text-color': '#e0e0e0',
    'text-light': '#9e9e9e',
    'bg-color': '#121212',
    'border-color': '#333',
    
    // 状态颜色
    'success-color': '#66bb6a',
    'warning-color': '#ffb74d',
    'error-color': '#ef5350',
    
    // 组件颜色
    'sidebar-bg-start': '#2d3748',
    'sidebar-bg-end': '#1a202c',
    'card-bg': '#2d2d2d',
    'file-table-header-bg': '#2d2d2d',
    'file-table-row-hover': '#333',
    
    // 状态徽章颜色
    'status-pending-bg': '#333',
    'status-pending-color': '#666',
    'status-processing-bg': '#1a237e',
    'status-processing-color': '#42a5f5',
    'status-success-bg': '#1b5e20',
    'status-success-color': '#81c784',
    'status-error-bg': '#b71c1c',
    'status-error-color': '#ffcdd2',
    'status-skip-bg': '#e65100',
    'status-skip-color': '#ffcc80',
    
    // 滚动条颜色
    'scrollbar-thumb': '#555',
    'scrollbar-thumb-hover': '#666',
    
    // 模态框颜色
    'modal-overlay-bg': 'rgba(0, 0, 0, 0.6)',
    'modal-content-bg': '#2d2d2d',
    'modal-header-border': '#333',
    'modal-header-bg': '#2d2d2d',
    'modal-body-bg': '#1a1a1a',
    'modal-footer-bg': '#2d2d2d',
    'modal-footer-border': '#333',
    
    // 帮助模态框颜色
    'help-modal-content-bg': '#2d2d2d',
    'help-modal-header-bg': '#2d2d2d',
    'help-modal-body-bg': '#0f172a',
    'help-modal-card-bg': '#1e293b',
    'help-modal-card-border': '#334155',
    'help-modal-header-border': '#334155',
    'help-modal-footer-bg': '#2d2d2d',
    'help-modal-footer-border': '#334155',
    
    // 其他
    'shadow-sm': '0 2px 4px rgba(0,0,0,0.3)',
    'shadow-md': '0 6px 12px rgba(0,0,0,0.3)',
  }
};

// 获取当前主题
export const getCurrentTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme;
  }
  
  // 如果没有保存的偏好，使用系统偏好
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
};

// 应用主题到CSS变量
export const applyTheme = (themeName) => {
  const theme = themes[themeName];
  if (!theme) return;

  const root = document.documentElement;
  Object.keys(theme).forEach(key => {
    root.style.setProperty(`--${key}`, theme[key]);
  });

  // 设置数据属性以应用主题
  root.setAttribute('data-theme', themeName);

  // 保存用户选择
  localStorage.setItem('theme', themeName);
};