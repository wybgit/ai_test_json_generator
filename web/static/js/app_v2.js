// AI JSON Generator Web Interface v2 - 使用新的API
// 直接调用ai-json-generator核心功能

class AIJsonGeneratorV2 {
    constructor() {
        this.currentTask = null;
        this.taskStatusInterval = null;
        this.templates = [];
        this.csvFiles = [];
        this.currentVariables = [];
        this.isBatchMode = false;
        this.currentCsvData = [];
        this.isGenerating = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadTemplates();
        this.loadCsvFiles();
        this.updateStatus('准备就绪，等待生成任务...', 'info');
        this.loadConfig();
    }
    
    bindEvents() {
        // Template operations
        document.getElementById('loadTemplateBtn').addEventListener('click', () => {
            this.loadSelectedTemplate();
        });
        
        document.getElementById('parseTemplateBtn').addEventListener('click', () => {
            this.parseTemplate();
        });
        
        // Mode toggle
        document.getElementById('toggleBatchMode').addEventListener('click', () => {
            this.toggleBatchMode();
        });
        
        // CSV operations
        document.getElementById('loadCsvBtn').addEventListener('click', () => {
            this.loadSelectedCsv();
        });
        
        document.getElementById('toggleCsvPreview').addEventListener('click', () => {
            this.toggleCsvPreview();
        });
        
        // Main generation
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateTestCases();
        });
        
        // Clear functions
        document.getElementById('clearVariablesBtn').addEventListener('click', () => {
            this.clearVariables();
        });
        
        document.getElementById('clearLogsBtn').addEventListener('click', () => {
            this.clearLogs();
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
            this.downloadResults();
        });
        
        // Task monitoring
        document.getElementById('stopTaskBtn')?.addEventListener('click', () => {
            this.stopCurrentTask();
        });
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/v2/config');
            const data = await response.json();
            
            if (data.success) {
                this.config = data.config;
                this.addLogMessage(`配置加载成功: ${data.config.model}`, 'success');
            } else {
                this.addLogMessage('配置加载失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.addLogMessage('配置加载失败: ' + error.message, 'error');
        }
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
            
            this.addLogMessage(`已加载 ${templates.length} 个模板文件`, 'info');
        } catch (error) {
            this.addLogMessage('加载模板失败: ' + error.message, 'error');
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
        
        this.addLogMessage(`✅ 已加载模板: ${template.name}`, 'success');
        
        // 自动解析变量
        this.addLogMessage('🔍 正在自动解析模板变量...', 'info');
        await this.parseTemplate();
    }
    
    async parseTemplate() {
        const templateContent = document.getElementById('templateContent').value.trim();
        
        if (!templateContent) {
            this.addLogMessage('⚠️ 请输入模板内容', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/parse_template', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ template_content: templateContent })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentVariables = result.variables;
                this.renderVariableInputs();
                if (result.variables.length > 0) {
                    this.addLogMessage(`✅ 解析到 ${result.variables.length} 个变量: ${result.variables.join(', ')}`, 'success');
                } else {
                    this.addLogMessage('ℹ️ 模板中未发现变量，可以直接生成', 'info');
                }
            } else {
                this.addLogMessage('❌ 模板解析失败: ' + result.error, 'error');
            }
        } catch (error) {
            this.addLogMessage('❌ 模板解析失败: ' + error.message, 'error');
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
        
        // Body (限制预览行数)
        const tbody = document.createElement('tbody');
        csvFile.rows.slice(0, 10).forEach(row => {
            const tr = document.createElement('tr');
            csvFile.headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header] || '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        
        if (csvFile.rows.length > 10) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = csvFile.headers.length;
            td.className = 'text-center text-muted';
            td.textContent = `... 还有 ${csvFile.rows.length - 10} 行`;
            tr.appendChild(td);
            tbody.appendChild(tr);
        }
        
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
            this.showAlert('已有任务在进行中，请等待完成', 'warning');
            return;
        }
        
        const templateContent = document.getElementById('templateContent').value.trim();
        if (!templateContent) {
            this.showAlert('请输入模板内容', 'warning');
            return;
        }
        
        this.isGenerating = true;
        this.updateGenerateButton();
        this.updateStatus('正在生成测试用例...', 'warning');
        
        try {
            let apiUrl, requestData;
            
            if (this.isBatchMode) {
                // 批量模式
                if (this.currentCsvData.length === 0) {
                    this.showAlert('批量模式下请先加载 CSV 数据', 'warning');
                    this.isGenerating = false;
                    this.updateGenerateButton();
                    return;
                }
                
                apiUrl = '/api/v2/generate/batch';
                requestData = {
                    csv_data: this.currentCsvData,
                    prompt_template: templateContent,
                    output_dir: 'web_outputs',
                    convert_to_onnx: document.getElementById('convertToOnnx').checked,
                    max_retries: parseInt(document.getElementById('maxRetries').value),
                    debug: document.getElementById('debugMode').checked,
                    quiet: false
                };
                
                this.addLogMessage(`开始批量生成 ${this.currentCsvData.length} 个测试用例`, 'info');
                
            } else {
                // 单个测试用例模式
                const variables = {};
                this.currentVariables.forEach(variable => {
                    const input = document.getElementById(`var_${variable}`);
                    if (input) {
                        variables[variable] = input.value;
                    }
                });
                
                // 如果有变量，渲染模板
                let finalTemplate = templateContent;
                if (this.currentVariables.length > 0) {
                    try {
                        // 简单的变量替换（更复杂的模板渲染在后端进行）
                        for (const [key, value] of Object.entries(variables)) {
                            const regex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
                            finalTemplate = finalTemplate.replace(regex, value);
                        }
                    } catch (e) {
                        this.addLogMessage('模板变量替换失败，将发送原始模板到后端处理', 'warning');
                    }
                }
                
                apiUrl = '/api/v2/generate/single';
                requestData = {
                    operator: '', // 使用direct_prompt模式
                    direct_prompt: finalTemplate,
                    output_dir: 'web_outputs',
                    convert_to_onnx: document.getElementById('convertToOnnx').checked,
                    max_retries: parseInt(document.getElementById('maxRetries').value),
                    debug: document.getElementById('debugMode').checked,
                    quiet: false
                };
                
                const varSummary = this.currentVariables.map(v => {
                    const input = document.getElementById(`var_${v}`);
                    return `${v}: ${input ? input.value || '(空)' : '(空)'}`;
                }).join(', ');
                
                this.addLogMessage(`开始生成测试用例 (${varSummary || '无变量'})`, 'info');
            }
            
            // 发送生成请求
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentTask = result.task_id;
                this.addLogMessage(`✅ 生成任务已启动 (任务ID: ${result.task_id})`, 'success');
                this.addLogMessage('📊 开始监控任务状态...', 'info');
                
                // 开始监控任务状态
                this.startTaskMonitoring();
                
            } else {
                this.addLogMessage('❌ 生成任务启动失败: ' + result.error, 'error');
                this.updateStatus('生成失败: ' + result.error, 'danger');
                this.isGenerating = false;
                this.updateGenerateButton();
            }
            
        } catch (error) {
            this.addLogMessage('❌ 生成失败: ' + error.message, 'error');
            this.updateStatus('生成失败: ' + error.message, 'danger');
            this.isGenerating = false;
            this.updateGenerateButton();
        }
    }
    
    startTaskMonitoring() {
        if (!this.currentTask) return;
        
        // 清除之前的监控
        if (this.taskStatusInterval) {
            clearInterval(this.taskStatusInterval);
        }
        
        // 每2秒检查一次任务状态
        this.taskStatusInterval = setInterval(async () => {
            await this.checkTaskStatus();
        }, 2000);
        
        // 立即检查一次
        this.checkTaskStatus();
    }
    
    async checkTaskStatus() {
        if (!this.currentTask) return;
        
        try {
            const response = await fetch(`/api/v2/tasks/${this.currentTask}/status`);
            const data = await response.json();
            
            if (data.success) {
                const task = data.task;
                
                // 显示新的日志
                if (task.logs && task.logs.length > 0) {
                    task.logs.forEach(log => {
                        if (!this.displayedLogs) this.displayedLogs = new Set();
                        const logKey = `${log.timestamp}-${log.message}`;
                        if (!this.displayedLogs.has(logKey)) {
                            this.addLogMessage(`[${log.timestamp}] ${log.message}`, log.level);
                            this.displayedLogs.add(logKey);
                        }
                    });
                }
                
                // 检查任务状态
                if (task.status === 'completed') {
                    this.addLogMessage('🎉 生成任务完成！', 'success');
                    this.updateStatus('生成完成！', 'success');
                    this.onTaskCompleted(task.result);
                    
                } else if (task.status === 'failed' || task.status === 'error') {
                    this.addLogMessage('❌ 生成任务失败: ' + (task.error || '未知错误'), 'error');
                    this.updateStatus('生成失败: ' + (task.error || '未知错误'), 'danger');
                    this.onTaskCompleted(null);
                }
                
            } else {
                this.addLogMessage('❌ 无法获取任务状态: ' + data.error, 'error');
                this.onTaskCompleted(null);
            }
            
        } catch (error) {
            this.addLogMessage('❌ 任务状态检查失败: ' + error.message, 'error');
        }
    }
    
    onTaskCompleted(result) {
        // 停止监控
        if (this.taskStatusInterval) {
            clearInterval(this.taskStatusInterval);
            this.taskStatusInterval = null;
        }
        
        this.isGenerating = false;
        this.updateGenerateButton();
        
        if (result && result.success) {
            this.showResults();
            this.loadResults();
        }
    }
    
    stopCurrentTask() {
        if (this.taskStatusInterval) {
            clearInterval(this.taskStatusInterval);
            this.taskStatusInterval = null;
        }
        
        this.currentTask = null;
        this.isGenerating = false;
        this.updateGenerateButton();
        this.updateStatus('任务已停止', 'warning');
        this.addLogMessage('⏹️ 用户手动停止任务监控', 'warning');
    }
    
    async loadResults() {
        if (!this.currentTask) {
            this.addLogMessage('没有活动的任务', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/v2/tasks/${this.currentTask}/files`);
            const data = await response.json();
            
            if (data.success) {
                this.renderResults(data.files);
                this.addLogMessage(`加载到 ${data.files.length} 个结果文件`, 'info');
            } else {
                this.addLogMessage('加载结果失败: ' + data.error, 'error');
            }
            
        } catch (error) {
            this.addLogMessage('加载结果失败: ' + error.message, 'error');
        }
    }
    
    renderResults(files) {
        const container = document.getElementById('resultsList');
        container.innerHTML = '';
        
        if (files.length === 0) {
            container.innerHTML = '<div class="list-group-item text-center text-muted">暂无结果</div>';
            return;
        }
        
        files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const fileIcon = this.getFileIcon(file.name);
            const fileSize = this.formatFileSize(file.size);
            
            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="${fileIcon} me-2"></i>
                    <div>
                        <div class="fw-bold">${file.name}</div>
                        <small class="text-muted">${file.path}</small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <span class="badge bg-secondary file-size-badge me-2">${fileSize}</span>
                    ${file.preview ? `<button class="btn btn-sm btn-outline-info file-preview-btn me-2" onclick="app.showFilePreview('${file.name}', \`${file.preview.replace(/`/g, '\\`')}\`)">
                        <i class="fas fa-eye"></i>
                    </button>` : ''}
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    async downloadResults() {
        if (!this.currentTask) {
            this.showAlert('没有可下载的结果', 'warning');
            return;
        }
        
        try {
            this.addLogMessage('开始下载结果文件...', 'info');
            
            const response = await fetch(`/api/v2/tasks/${this.currentTask}/download`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ai_json_results_${this.currentTask}.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.addLogMessage('下载完成', 'success');
                this.showAlert('下载完成', 'success');
            } else {
                throw new Error('下载失败');
            }
        } catch (error) {
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
    
    clearLogs() {
        const logContainer = document.getElementById('logMessages');
        if (logContainer) {
            logContainer.innerHTML = '';
        }
        this.displayedLogs = new Set();
        this.addLogMessage('日志已清空，重新开始', 'info');
    }
    
    showResults() {
        document.getElementById('resultsSection').style.display = 'block';
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
    
    addLogMessage(message, level = 'info') {
        const logContainer = document.getElementById('logMessages');
        if (!logContainer) return;
        
        const logMessage = document.createElement('div');
        logMessage.className = `log-message ${level}`;
        
        const time = new Date().toLocaleTimeString();
        logMessage.innerHTML = `
            <span class="log-timestamp">[${time}]</span>
            <span class="log-content">${message}</span>
        `;
        
        logContainer.appendChild(logMessage);
        
        // Auto scroll to bottom
        const logContainerParent = document.getElementById('logContainer');
        if (logContainerParent) {
            logContainerParent.scrollTop = logContainerParent.scrollHeight;
        }
        
        // Limit log messages
        const messages = logContainer.children;
        if (messages.length > 100) {
            logContainer.removeChild(messages[0]);
        }
    }
    
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'json': return 'fas fa-file-code text-primary';
            case 'onnx': return 'fas fa-cube text-success';
            case 'csv': return 'fas fa-table text-info';
            case 'txt': return 'fas fa-file-alt text-secondary';
            default: return 'fas fa-file text-muted';
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
        // 这个函数可能需要从HTML模板调用，所以保持简单实现
        alert(`文件预览: ${filename}\n\n${content}`);
    }
    
    showAlert(message, type = 'info') {
        // 创建临时提示
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertContainer.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertContainer);
        
        // 5秒后自动移除
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.parentNode.removeChild(alertContainer);
            }
        }, 5000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AIJsonGeneratorV2();
});
