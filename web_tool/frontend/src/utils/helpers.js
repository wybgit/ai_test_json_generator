// 工具函数模块

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 格式化相对时间
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return `${seconds}秒前`;
}

// 生成UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 防抖函数
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 显示Toast消息
function showToast(message, type = 'info', duration = 3000) {
    // 创建toast容器（如果不存在）
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" data-bs-delay="${duration}">
            <div class="toast-header">
                <i class="fas fa-${getToastIcon(type)} me-2 text-${type}"></i>
                <strong class="me-auto">${getToastTitle(type)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // 显示toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // 自动清理
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// 获取Toast图标
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 获取Toast标题
function getToastTitle(type) {
    const titles = {
        'success': '成功',
        'error': '错误',
        'warning': '警告',
        'info': '信息'
    };
    return titles[type] || '信息';
}

// 显示加载状态
function showLoading(text = '正在处理...') {
    const loadingModal = document.getElementById('loadingModal');
    const loadingText = document.getElementById('loadingText');
    
    if (loadingText) {
        loadingText.textContent = text;
    }
    
    if (loadingModal) {
        // 如果已经有modal实例，先隐藏
        const existingModal = bootstrap.Modal.getInstance(loadingModal);
        if (existingModal) {
            existingModal.hide();
        }
        
        const modal = new bootstrap.Modal(loadingModal);
        modal.show();
        return modal;
    }
}

// 隐藏加载状态
function hideLoading() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        const modal = bootstrap.Modal.getInstance(loadingModal);
        if (modal) {
            modal.hide();
        } else {
            // 如果没有实例，直接隐藏模态框
            loadingModal.style.display = 'none';
            loadingModal.classList.remove('show');
            document.body.classList.remove('modal-open');
            
            // 移除backdrop
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
    }
}

// 确认对话框
function confirmDialog(message, title = '确认') {
    return new Promise((resolve) => {
        const confirmed = confirm(`${title}\\n\\n${message}`);
        resolve(confirmed);
    });
}

// 复制到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('已复制到剪贴板', 'success');
        return true;
    } catch (err) {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showToast('已复制到剪贴板', 'success');
            return true;
        } catch (err) {
            showToast('复制失败', 'error');
            return false;
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

// 下载文件
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || '';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 文件拖放处理
function setupFileDrop(element, callback) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.classList.add('dragover');
    });
    
    element.addEventListener('dragleave', (e) => {
        e.preventDefault();
        element.classList.remove('dragover');
    });
    
    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0 && callback) {
            callback(files[0]);
        }
    });
}

// 验证文件类型
function validateFileType(file, allowedTypes) {
    const fileExtension = file.name.split('.').pop().toLowerCase();
    return allowedTypes.includes(fileExtension);
}

// 解析CSV数据
function parseCSV(text) {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length === 0) return [];
    
    const headers = lines[0].split(',').map(h => h.trim());
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        if (values.length === headers.length) {
            const row = {};
            headers.forEach((header, index) => {
                row[header] = values[index];
            });
            data.push(row);
        }
    }
    
    return data;
}

// 转义HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 高亮语法
function highlightCode(code, language = 'json') {
    if (window.Prism) {
        return Prism.highlight(code, Prism.languages[language] || Prism.languages.text, language);
    }
    return escapeHtml(code);
}

// 滚动到底部
function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

// 平滑滚动到元素
function scrollToElement(element, offset = 0) {
    const elementTop = element.offsetTop - offset;
    window.scrollTo({
        top: elementTop,
        behavior: 'smooth'
    });
}

// 检查是否为移动设备
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// 获取查询参数
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// 设置查询参数
function setQueryParam(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.pushState({}, '', url);
}
