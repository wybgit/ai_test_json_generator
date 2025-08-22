// AI JSON Generator Web Interface - Main JavaScript

class AIJsonGeneratorApp {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.templates = [];
        this.csvFiles = [];
        this.currentVariables = [];
        this.isBatchMode = false;
        this.currentCsvData = [];
        this.isGenerating = false;
        this.autoScroll = true;
        this.typingIndicatorId = null;
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.bindEvents();
        this.loadTemplates();
        this.loadCsvFiles();
        this.updateStatus('准备就绪，等待生成任务...', 'info');
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', (data) => {
            console.log('WebSocket connected');
            this.addChatMessage('WebSocket 连接已建立，准备就绪！', 'success', 'system');
        });
        
        this.socket.on('connected', (data) => {
            this.sessionId = data.session_id;
            console.log('Session ID:', this.sessionId);
        });
        
        this.socket.on('log_message', (data) => {
            if (data.session_id === this.sessionId) {
                this.addChatMessage(data.message, data.level, 'system');
            }
        });
        
        this.socket.on('generation_complete', (data) => {
            if (data.session_id === this.sessionId) {
                this.isGenerating = false;
                this.hideLoading();
                
                if (data.success) {
                    this.updateStatus('生成完成！', 'success');
                    this.showResults();
                    this.loadResults();
                } else {
                    this.updateStatus(`生成失败: ${data.error}`, 'danger');
                }
                
                this.updateGenerateButton();
            }
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.addChatMessage('连接已断开，请刷新页面重新连接', 'warning', 'system');
        });
    }
    
    bindEvents() {
        // Template selection
        document.getElementById('loadTemplateBtn').addEventListener('click', () => {
            this.loadSelectedTemplate();
        });
        
        // Template parsing
        document.getElementById('parseTemplateBtn').addEventListener('click', () => {
            this.parseTemplate();
        });
        
        // Batch mode toggle
        document.getElementById('toggleBatchMode').addEventListener('click', () => {
            this.toggleBatchMode();
        });
        
        // CSV loading
        document.getElementById('loadCsvBtn').addEventListener('click', () => {
            this.loadSelectedCsv();
        });
        
        // CSV preview toggle
        document.getElementById('toggleCsvPreview').addEventListener('click', () => {
            this.toggleCsvPreview();
        });
        
        // Generation
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateTestCases();
        });
        
        // Clear functions
        document.getElementById('clearVariablesBtn').addEventListener('click', () => {
            this.clearVariables();
        });
        
        document.getElementById('clearLogsBtn').addEventListener('click', () => {
            this.clearChat();
        });
        
        // Auto scroll toggle
        document.getElementById('autoScrollBtn').addEventListener('click', () => {
            this.toggleAutoScroll();
        });
        
        // Advanced options
        document.getElementById('temperature').addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });
        
        // Results
        document.getElementById('refreshResultsBtn').addEventListener('click', () => {
            this.loadResults();
        });
        
        document.getElementById('downloadAllBtn').addEventListener('click', () => {
            this.downloadAllResults();
        });
    }
    
    async loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            const templates = await response.json();
            this.templates = templates;
            
            const select = document.getElementById('templateSelect');
            select.innerHTML = '<option value="">选择预置模板...</option>';
            
            templates.forEach((template, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = template.name;
                select.appendChild(option);
            });
            
            this.addChatMessage(`已加载 ${templates.length} 个模板文件`, 'info', 'system');
        } catch (error) {
            console.error('Loading templates failed:', error);
            this.addChatMessage('加载模板失败: ' + error.message, 'error', 'system');
        }
    }
    
    async loadCsvFiles() {
        try {
            const response = await fetch('/api/csv_files');
            const csvFiles = await response.json();
            this.csvFiles = csvFiles;
            
            const select = document.getElementById('csvSelect');
            select.innerHTML = '<option value="">选择预置 CSV...</option>';
            
            csvFiles.forEach((csvFile, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${csvFile.name} (${csvFile.rows.length} 行)`;
                select.appendChild(option);
            });
            
            this.addLogMessage(`已加载 ${csvFiles.length} 个 CSV 文件`, 'info');
        } catch (error) {
            console.error('Loading CSV files failed:', error);
            this.addLogMessage('加载 CSV 文件失败: ' + error.message, 'error');
        }
    }
    
    async loadSelectedTemplate() {
        const select = document.getElementById('templateSelect');
        const selectedIndex = select.value;
        
        if (selectedIndex === '') {
            this.showAlert('请选择一个模板', 'warning');
            return;
        }
        
        const template = this.templates[selectedIndex];
        document.getElementById('templateContent').value = template.content;
        
        this.addChatMessage(`✅ 已加载模板: ${template.name}`, 'success', 'system');
        
        // 自动解析变量
        this.addChatMessage('🔍 正在自动解析模板变量...', 'info', 'system');
        await this.parseTemplate();
    }
    
    async parseTemplate() {
        const templateContent = document.getElementById('templateContent').value.trim();
        
        if (!templateContent) {
            this.addChatMessage('⚠️ 请输入模板内容', 'warning', 'system');
            return;
        }
        
        // 添加加载指示器
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/parse_template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template_content: templateContent
                })
            });
            
            const result = await response.json();
            this.removeTypingIndicator();
            
            if (result.success) {
                this.currentVariables = result.variables;
                this.renderVariableInputs();
                if (result.variables.length > 0) {
                    this.addChatMessage(`✅ 解析到 ${result.variables.length} 个变量: ${result.variables.join(', ')}`, 'success', 'system');
                } else {
                    this.addChatMessage('ℹ️ 模板中未发现变量，可以直接生成', 'info', 'system');
                }
            } else {
                this.addChatMessage('❌ 模板解析失败: ' + result.error, 'error', 'system');
            }
        } catch (error) {
            this.removeTypingIndicator();
            console.error('Parse template failed:', error);
            this.addChatMessage('❌ 模板解析失败: ' + error.message, 'error', 'system');
        }
    }
    
    renderVariableInputs() {
        const container = document.getElementById('variableInputs');
        container.innerHTML = '';
        
        if (this.currentVariables.length === 0) {
            container.innerHTML = '<p class="text-muted">没有检测到变量</p>';
            return;
        }
        
        this.currentVariables.forEach(variable => {
            const inputGroup = document.createElement('div');
            inputGroup.className = 'variable-input-group';
            
            inputGroup.innerHTML = `
                <label class="variable-label" for="var_${variable}">
                    <i class="fas fa-tag me-1"></i>
                    ${variable}
                </label>
                <input type="text" class="form-control" id="var_${variable}" 
                       name="${variable}" placeholder="输入 ${variable} 的值...">
            `;
            
            container.appendChild(inputGroup);
        });
    }
    
    toggleBatchMode() {
        this.isBatchMode = !this.isBatchMode;
        
        const singleMode = document.getElementById('singleVariableMode');
        const batchMode = document.getElementById('batchMode');
        const toggleBtn = document.getElementById('toggleBatchMode');
        
        if (this.isBatchMode) {
            singleMode.style.display = 'none';
            batchMode.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-user me-1"></i>单变量模式';
            toggleBtn.className = 'btn btn-outline-info btn-sm me-2';
            this.addLogMessage('已切换到批量模式', 'info');
        } else {
            singleMode.style.display = 'block';
            batchMode.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-list me-1"></i>批量模式';
            toggleBtn.className = 'btn btn-outline-warning btn-sm me-2';
            this.addLogMessage('已切换到单变量模式', 'info');
        }
    }
    
    loadSelectedCsv() {
        const select = document.getElementById('csvSelect');
        const selectedIndex = select.value;
        
        if (selectedIndex === '') {
            this.showAlert('请选择一个 CSV 文件', 'warning');
            return;
        }
        
        const csvFile = this.csvFiles[selectedIndex];
        this.currentCsvData = csvFile.rows;
        
        this.renderCsvPreview(csvFile);
        document.getElementById('csvDataContainer').style.display = 'block';
        
        this.addLogMessage(`已加载 CSV: ${csvFile.name} (${csvFile.rows.length} 行)`, 'success');
        this.showAlert(`已加载 CSV: ${csvFile.name}`, 'success');
    }
    
    renderCsvPreview(csvFile) {
        const table = document.getElementById('csvTable');
        table.innerHTML = '';
        
        if (csvFile.headers.length === 0) {
            table.innerHTML = '<tr><td>没有数据</td></tr>';
            return;
        }
        
        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        csvFile.headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Body
        const tbody = document.createElement('tbody');
        csvFile.rows.forEach((row, index) => {
            const tr = document.createElement('tr');
            csvFile.headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header] || '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
            
            // Limit preview to 10 rows
            if (index >= 9) {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = csvFile.headers.length;
                td.className = 'text-center text-muted';
                td.textContent = `... 还有 ${csvFile.rows.length - 10} 行`;
                tr.appendChild(td);
                tbody.appendChild(tr);
                return false;
            }
        });
        table.appendChild(tbody);
    }
    
    toggleCsvPreview() {
        const preview = document.getElementById('csvPreview');
        const btn = document.getElementById('toggleCsvPreview');
        
        if (preview.style.display === 'none') {
            preview.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-eye-slash me-1"></i>隐藏数据';
        } else {
            preview.style.display = 'none';
            btn.innerHTML = '<i class="fas fa-eye me-1"></i>显示数据';
        }
    }
    
    async generateTestCases() {
        if (this.isGenerating) {
            return;
        }
        
        const templateContent = document.getElementById('templateContent').value.trim();
        if (!templateContent) {
            this.showAlert('请输入模板内容', 'warning');
            return;
        }
        
        // 收集所有配置参数
        let requestData = {
            template_content: templateContent,
            batch_mode: this.isBatchMode,
            convert_to_onnx: document.getElementById('convertToOnnx').checked,
            max_retries: parseInt(document.getElementById('maxRetries').value),
            debug: document.getElementById('debugMode').checked,
            temperature: parseFloat(document.getElementById('temperature').value),
            max_tokens: parseInt(document.getElementById('maxTokens').value)
        };
        
        if (this.isBatchMode) {
            if (this.currentCsvData.length === 0) {
                this.showAlert('批量模式下请先加载 CSV 数据', 'warning');
                return;
            }
            requestData.csv_data = this.currentCsvData;
        } else {
            // Single variable mode
            const variables = {};
            this.currentVariables.forEach(variable => {
                const input = document.getElementById(`var_${variable}`);
                if (input) {
                    variables[variable] = input.value;
                }
            });
            requestData.variables = variables;
        }
        
        // 添加用户操作消息
        if (this.isBatchMode) {
            this.addUserMessage(`开始批量生成 ${this.currentCsvData.length} 个测试用例`);
        } else {
            const varSummary = this.currentVariables.map(v => {
                const input = document.getElementById(`var_${v}`);
                return `${v}: ${input ? input.value : '(空)'}`;
            }).join(', ');
            this.addUserMessage(`开始生成测试用例 (${varSummary})`);
        }
        
        this.isGenerating = true;
        this.updateGenerateButton();
        this.updateStatus('正在生成测试用例...', 'warning');
        this.showLoading('正在生成测试用例...');
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addChatMessage('✅ 生成任务已启动，正在处理中...', 'success', 'system');
                this.updateStatus('生成中，实时日志将自动显示...', 'info');
                // The completion will be handled by WebSocket
            } else {
                this.isGenerating = false;
                this.hideLoading();
                this.removeTypingIndicator();
                this.updateGenerateButton();
                this.updateStatus('生成失败: ' + result.error, 'danger');
                this.addChatMessage('❌ 生成失败: ' + result.error, 'error', 'system');
                this.showAlert('生成失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.isGenerating = false;
            this.hideLoading();
            this.updateGenerateButton();
            console.error('Generate failed:', error);
            this.removeTypingIndicator();
            this.updateStatus('生成失败: ' + error.message, 'danger');
            this.addChatMessage('生成失败: ' + error.message, 'error', 'system');
            this.showAlert('生成失败: ' + error.message, 'danger');
        }
    }
    
    async loadResults() {
        if (!this.sessionId) {
            return;
        }
        
        try {
            const response = await fetch(`/api/results/${this.sessionId}`);
            const result = await response.json();
            
            if (result.success) {
                this.renderResults(result.results);
            } else {
                this.addLogMessage('加载结果失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Load results failed:', error);
            this.addLogMessage('加载结果失败: ' + error.message, 'error');
        }
    }
    
    renderResults(results) {
        const container = document.getElementById('resultsList');
        container.innerHTML = '';
        
        if (results.length === 0) {
            container.innerHTML = '<div class="list-group-item text-center text-muted">暂无结果</div>';
            return;
        }
        
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const fileIcon = this.getFileIcon(result.name);
            const fileSize = this.formatFileSize(result.size);
            
            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="${fileIcon} me-2"></i>
                    <div>
                        <div class="fw-bold">${result.name}</div>
                        <small class="text-muted">${result.path}</small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <span class="badge bg-secondary file-size-badge me-2">${fileSize}</span>
                    ${result.preview ? `<button class="btn btn-sm btn-outline-info file-preview-btn me-2" onclick="app.showFilePreview('${result.name}', \`${result.preview.replace(/`/g, '\\`')}\`)">
                        <i class="fas fa-eye"></i>
                    </button>` : ''}
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'json':
                return 'fas fa-file-code text-primary';
            case 'onnx':
                return 'fas fa-cube text-success';
            case 'csv':
                return 'fas fa-table text-info';
            case 'txt':
                return 'fas fa-file-alt text-secondary';
            default:
                return 'fas fa-file text-muted';
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showFilePreview(filename, content) {
        document.getElementById('previewModalTitle').textContent = filename;
        document.getElementById('previewContent').textContent = content;
        new bootstrap.Modal(document.getElementById('previewModal')).show();
    }
    
    async downloadAllResults() {
        if (!this.sessionId) {
            this.showAlert('没有可下载的结果', 'warning');
            return;
        }
        
        this.showLoading('正在打包下载...');
        
        try {
            const response = await fetch(`/api/download/${this.sessionId}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `test_results_${this.sessionId}.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.hideLoading();
                this.addLogMessage('下载完成', 'success');
                this.showAlert('下载完成', 'success');
            } else {
                throw new Error('下载失败');
            }
        } catch (error) {
            this.hideLoading();
            console.error('Download failed:', error);
            this.addLogMessage('下载失败: ' + error.message, 'error');
            this.showAlert('下载失败: ' + error.message, 'danger');
        }
    }
    
    clearVariables() {
        this.currentVariables.forEach(variable => {
            const input = document.getElementById(`var_${variable}`);
            if (input) {
                input.value = '';
            }
        });
        this.addLogMessage('已清空变量值', 'info');
    }
    
    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        // 添加欢迎消息
        const welcomeMessage = this.createChatMessage(
            '日志已清空，重新开始对话', 'info', 'system'
        );
        chatMessages.appendChild(welcomeMessage);
        
        this.scrollToBottom();
    }
    
    addChatMessage(message, level = 'info', sender = 'system') {
        const chatMessages = document.getElementById('chatMessages');
        const messageElement = this.createChatMessage(message, level, sender);
        
        // 移除输入指示器
        this.removeTypingIndicator();
        
        chatMessages.appendChild(messageElement);
        
        if (this.autoScroll) {
            this.scrollToBottom();
        }
        
        // 限制消息数量
        const messages = chatMessages.children;
        if (messages.length > 50) {
            chatMessages.removeChild(messages[0]);
        }
    }
    
    addUserMessage(message) {
        this.addChatMessage(message, 'info', 'user');
    }
    
    createChatMessage(message, level, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${level} ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'chat-avatar';
        
        if (sender === 'user') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        }
        
        const content = document.createElement('div');
        content.className = 'chat-content';
        
        const header = document.createElement('div');
        header.className = 'chat-header';
        
        const senderSpan = document.createElement('span');
        senderSpan.className = 'chat-sender';
        senderSpan.textContent = sender === 'user' ? '用户' : 'AI助手';
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'chat-time';
        timeSpan.textContent = new Date().toLocaleTimeString();
        
        header.appendChild(senderSpan);
        header.appendChild(timeSpan);
        
        const text = document.createElement('div');
        text.className = 'chat-text';
        
        // 处理代码块
        if (message.includes('```')) {
            const parts = message.split('```');
            for (let i = 0; i < parts.length; i++) {
                if (i % 2 === 0) {
                    // 普通文本
                    if (parts[i].trim()) {
                        const textNode = document.createTextNode(parts[i]);
                        text.appendChild(textNode);
                    }
                } else {
                    // 代码块
                    const codeBlock = document.createElement('div');
                    codeBlock.className = 'chat-code';
                    codeBlock.textContent = parts[i];
                    text.appendChild(codeBlock);
                }
            }
        } else {
            text.textContent = message;
        }
        
        content.appendChild(header);
        content.appendChild(text);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        return messageDiv;
    }
    
    showTypingIndicator() {
        if (this.typingIndicatorId) return;
        
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message system';
        typingDiv.id = 'typing-indicator';
        
        typingDiv.innerHTML = `
            <div class="chat-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="chat-content">
                <div class="chat-text">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        this.typingIndicatorId = 'typing-indicator';
        
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }
    
    removeTypingIndicator() {
        if (this.typingIndicatorId) {
            const indicator = document.getElementById(this.typingIndicatorId);
            if (indicator) {
                indicator.remove();
            }
            this.typingIndicatorId = null;
        }
    }
    
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        const btn = document.getElementById('autoScrollBtn');
        
        if (this.autoScroll) {
            btn.classList.add('active');
            btn.title = '自动滚动：开启';
            this.scrollToBottom();
        } else {
            btn.classList.remove('active');
            btn.title = '自动滚动：关闭';
        }
    }
    
    scrollToBottom() {
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    clearLogs() {
        // 保持兼容性的空函数
        this.clearChat();
    }
    
    showResults() {
        document.getElementById('resultsSection').style.display = 'block';
    }
    
    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
    }
    
    updateGenerateButton() {
        const btn = document.getElementById('generateBtn');
        if (this.isGenerating) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>生成中...';
            btn.className = 'btn btn-warning btn-lg';
        } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-play me-2"></i>生成测试用例';
            btn.className = 'btn btn-success btn-lg';
        }
    }
    
    updateStatus(message, level) {
        const container = document.getElementById('statusContainer');
        const statusMessage = document.getElementById('statusMessage');
        
        statusMessage.innerHTML = `<i class="fas fa-info-circle me-2"></i>${message}`;
        
        container.innerHTML = '';
        const alert = document.createElement('div');
        alert.className = `alert alert-${level}`;
        alert.setAttribute('role', 'alert');
        alert.appendChild(statusMessage);
        container.appendChild(alert);
    }
    
    addLogMessage(message, level = 'info', timestamp = null) {
        const logContainer = document.getElementById('logMessages');
        const logMessage = document.createElement('div');
        logMessage.className = `log-message ${level}`;
        
        const time = timestamp || new Date().toLocaleTimeString();
        logMessage.innerHTML = `
            <span class="log-timestamp">[${time}]</span>
            <span class="log-content">${message}</span>
        `;
        
        logContainer.appendChild(logMessage);
        
        // Auto scroll to bottom
        const logContainerParent = document.getElementById('logContainer');
        logContainerParent.scrollTop = logContainerParent.scrollHeight;
        
        // Limit log messages to prevent memory issues
        const messages = logContainer.children;
        if (messages.length > 100) {
            logContainer.removeChild(messages[0]);
        }
    }
    
    showLoading(message = '处理中...') {
        document.getElementById('loadingMessage').textContent = message;
        new bootstrap.Modal(document.getElementById('loadingModal')).show();
    }
    
    hideLoading() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }
    
    showAlert(message, type = 'info') {
        // Create a temporary alert
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertContainer.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertContainer);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.parentNode.removeChild(alertContainer);
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AIJsonGeneratorApp();
});
