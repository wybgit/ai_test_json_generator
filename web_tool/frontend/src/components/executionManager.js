// 执行管理器组件
class ExecutionManager {
    constructor() {
        this.currentExecutionId = null;
        this.isExecuting = false;
        this.logLines = [];
        this.maxLogLines = 1000;
        this.executionStartTime = null;
        this.timerInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocketCallbacks();
    }

    setupEventListeners() {
        // 执行按钮
        const executeBtn = document.getElementById('executeBtn');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => {
                this.executeToolAsync();
            });
        }

        // 停止按钮
        const stopBtn = document.getElementById('stopBtn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                this.stopExecution();
            });
        }

        // 清空日志按钮
        const clearLogBtn = document.getElementById('clearLogBtn');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => {
                this.clearLog();
            });
        }

        // 导出日志按钮
        const exportLogBtn = document.getElementById('exportLogBtn');
        if (exportLogBtn) {
            exportLogBtn.addEventListener('click', () => {
                this.exportLog();
            });
        }
    }

    setupWebSocketCallbacks() {
        // 执行开始
        wsService.on('executionStarted', (data) => {
            this.onExecutionStarted(data);
        });

        // 执行日志
        wsService.on('executionLog', (data) => {
            this.onExecutionLog(data);
        });

        // 执行完成
        wsService.on('executionCompleted', (data) => {
            this.onExecutionCompleted(data);
        });

        // 执行错误
        wsService.on('executionError', (data) => {
            this.onExecutionError(data);
        });

        // 执行停止
        wsService.on('executionStopped', (data) => {
            this.onExecutionStopped(data);
        });
    }

    async executeToolAsync() {
        try {
            // 验证工具选择
            const selectedTool = window.toolSelector?.getSelectedTool();
            if (!selectedTool) {
                showToast('请先选择一个工具', 'error');
                return;
            }

            // 验证模板
            if (!window.templateManager?.validateTemplate()) {
                return; // validateTemplate 现在返回布尔值并显示UI错误
            }

            // 构建执行参数（包括CSV数据）
            const params = this.buildExecutionParams();
            
            // 开始执行
            this.startExecution();
            
            // 通过WebSocket异步执行
            wsService.executeToolAsync(selectedTool.name, params);

        } catch (error) {
            console.error('执行失败:', error);
            showToast('执行失败: ' + error.message, 'error');
            this.stopExecution();
        }
    }

    buildExecutionParams() {
        const templateContent = window.templateManager?.getTemplateContent() || '';
        const variableValues = window.templateManager?.getVariableValues() || {};
        const csvData = window.templateManager?.getCsvData() || [];
        const useCSV = window.templateManager?.isUsingCSV() || false;
        const maxRetries = document.getElementById('maxRetries')?.value || 3;

        const params = {
            template_content: templateContent,
            use_csv: useCSV,
            max_retries: parseInt(maxRetries)
        };

        if (useCSV) {
            params.csv_data = csvData;
        } else {
            params.variable_values = variableValues;
        }

        return params;
    }

    startExecution() {
        this.isExecuting = true;
        this.executionStartTime = new Date();
        this.updateExecutionButtons();
        this.showExecutionSection();
        this.showExecutionProgress();
        this.startTimer();
        this.updateExecutionStatus('running', '执行中...');
        this.updateCurrentActivity('正在初始化...');
        this.addLogLine('开始执行工具...', 'info');
    }

    stopExecution() {
        if (this.currentExecutionId && this.isExecuting) {
            wsService.stopExecution(this.currentExecutionId);
        }
        
        this.isExecuting = false;
        this.stopTimer();
        this.updateExecutionButtons();
        this.updateExecutionStatus('stopped', '已停止');
        this.updateCurrentActivity('已停止');
    }

    onExecutionStarted(data) {
        console.log('执行开始:', data);
        this.currentExecutionId = data.execution_id;
        this.updateExecutionId(data.execution_id);
        this.updateCurrentActivity('正在执行...');
        this.addLogLine(`执行ID: ${data.execution_id}`, 'info');
        this.addLogLine(`工具: ${data.tool_name}`, 'info');
        this.addLogLine(`输出目录: ${data.output_dir}`, 'info');
        this.addLogLine('='.repeat(50), 'info');
        
        // 加入执行房间
        wsService.joinExecution(data.execution_id);
    }

    onExecutionLog(data) {
        if (data.execution_id === this.currentExecutionId) {
            this.addLogLine(data.log, 'log');
            this.updateCurrentActivityFromLog(data.log);
        }
    }

    onExecutionCompleted(data) {
        console.log('执行完成:', data);
        this.isExecuting = false;
        this.stopTimer();
        this.updateExecutionButtons();
        
        if (data.success) {
            this.updateExecutionStatus('completed', '执行完成');
            this.updateCurrentActivity('执行完成');
            this.addLogLine('='.repeat(50), 'success');
            this.addLogLine('执行成功完成!', 'success');
            showToast('工具执行成功', 'success');
            
            // 添加到历史记录
            this.addToHistory({
                execution_id: this.currentExecutionId,
                tool_name: data.tool_name || '未知工具',
                timestamp: data.timestamp,
                success: true,
                output_files: data.output_files,
                output_dir: data.output_dir
            });
            
            // 显示结果
            this.showResults(data);
        } else {
            this.updateExecutionStatus('failed', '执行失败');
            this.updateCurrentActivity('执行失败');
            this.addLogLine('='.repeat(50), 'error');
            this.addLogLine(`执行失败: ${data.error}`, 'error');
            showToast('工具执行失败: ' + data.error, 'error');
            
            // 添加到历史记录
            this.addToHistory({
                execution_id: this.currentExecutionId,
                tool_name: data.tool_name || '未知工具',
                timestamp: data.timestamp,
                success: false,
                error: data.error,
                output_dir: data.output_dir
            });
        }
    }

    onExecutionError(data) {
        console.error('执行错误:', data);
        this.isExecuting = false;
        this.updateExecutionButtons();
        this.updateExecutionStatus('failed', '执行错误');
        
        this.addLogLine('='.repeat(50), 'error');
        this.addLogLine(`执行错误: ${data.error}`, 'error');
        showToast('执行错误: ' + data.error, 'error');
    }

    onExecutionStopped(data) {
        console.log('执行停止:', data);
        this.isExecuting = false;
        this.updateExecutionButtons();
        this.updateExecutionStatus('stopped', '已停止');
        
        this.addLogLine('='.repeat(50), 'warning');
        this.addLogLine('执行已被停止', 'warning');
        showToast('执行已停止', 'warning');
    }

    addLogLine(text, type = 'log') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            text,
            type,
            id: Date.now() + Math.random() // 为每行日志添加唯一ID
        };

        this.logLines.push(logEntry);

        // 限制日志行数
        if (this.logLines.length > this.maxLogLines) {
            this.logLines = this.logLines.slice(-this.maxLogLines);
        }

        this.renderLogIncremental(logEntry);
    }

    // 增量渲染日志，避免重新渲染整个日志容器
    renderLogIncremental(logEntry) {
        const logContainer = document.getElementById('logContainer');
        if (!logContainer) return;

        const cssClass = this.getLogLineClass(logEntry.type);
        const logLineDiv = document.createElement('div');
        logLineDiv.className = `log-line ${cssClass}`;
        logLineDiv.setAttribute('data-log-id', logEntry.id);
        logLineDiv.innerHTML = `[${logEntry.timestamp}] ${escapeHtml(logEntry.text)}`;
        
        // 添加打字机效果（可选）
        if (logEntry.type === 'log' && logEntry.text.length > 50) {
            logLineDiv.style.opacity = '0';
            logContainer.appendChild(logLineDiv);
            
            // 淡入效果
            setTimeout(() => {
                logLineDiv.style.transition = 'opacity 0.3s ease-in';
                logLineDiv.style.opacity = '1';
            }, 10);
        } else {
            logContainer.appendChild(logLineDiv);
        }

        // 自动滚动到底部
        scrollToBottom(logContainer);
        
        // 更新日志行数统计
        this.updateLogLineCount();
        
        // 如果日志行数过多，删除旧的日志行
        const logLines = logContainer.querySelectorAll('.log-line');
        if (logLines.length > this.maxLogLines) {
            const excessCount = logLines.length - this.maxLogLines;
            for (let i = 0; i < excessCount; i++) {
                logLines[i].remove();
            }
        }
    }

    renderLog() {
        const logContainer = document.getElementById('logContainer');
        if (!logContainer) return;

        const logHtml = this.logLines.map(entry => {
            const cssClass = this.getLogLineClass(entry.type);
            return `<div class="log-line ${cssClass}">[${entry.timestamp}] ${escapeHtml(entry.text)}</div>`;
        }).join('');

        logContainer.innerHTML = logHtml;
        scrollToBottom(logContainer);
    }

    getLogLineClass(type) {
        const classes = {
            'error': 'error',
            'warning': 'warning',
            'success': 'success',
            'info': 'info',
            'log': ''
        };
        return classes[type] || '';
    }

    clearLog() {
        this.logLines = [];
        this.renderLog();
        showToast('日志已清空', 'info');
    }

    updateExecutionButtons() {
        const executeBtn = document.getElementById('executeBtn');
        const stopBtn = document.getElementById('stopBtn');

        if (executeBtn && stopBtn) {
            if (this.isExecuting) {
                executeBtn.style.display = 'none';
                stopBtn.style.display = 'block';
            } else {
                executeBtn.style.display = 'block';
                stopBtn.style.display = 'none';
            }
        }
    }

    showExecutionSection() {
        // 显示右侧的执行日志卡片
        const executionLogCard = document.getElementById('executionLogCard');
        if (executionLogCard) {
            executionLogCard.style.display = 'block';
            
            // 移除自动滚动，避免页面跳转
            // const toolConfigSection = document.getElementById('toolConfigSection');
            // if (toolConfigSection) {
            //     setTimeout(() => {
            //         scrollToElement(toolConfigSection, 100);
            //     }, 100);
            // }
        }
    }

    updateExecutionStatus(status, text) {
        const statusElement = document.getElementById('executionStatus');
        if (!statusElement) return;

        // 清除所有状态类和动画类
        statusElement.className = 'badge';
        statusElement.classList.remove('executing-dots', 'executing-spinner');
        
        // 添加新状态类
        statusElement.classList.add(`status-${status}`);
        statusElement.textContent = text;
        
        // 为运行状态添加动态效果
        if (status === 'running') {
            statusElement.classList.add('executing-dots');
        }
    }

    async showResults(data) {
        try {
            // 获取执行结果
            const results = await apiService.getExecutionOutputs(this.currentExecutionId);
            
            // 显示结果区域
            window.resultsManager?.showResults(this.currentExecutionId, results.files);
            
        } catch (error) {
            console.error('获取执行结果失败:', error);
            showToast('获取执行结果失败: ' + error.message, 'error');
        }
    }

    // 重置执行状态
    reset() {
        this.currentExecutionId = null;
        this.isExecuting = false;
        this.logLines = [];
        this.updateExecutionButtons();
        this.updateExecutionStatus('ready', '就绪');
        this.renderLog();

        // 隐藏执行和结果区域
        const executionSection = document.getElementById('executionSection');
        const resultsSection = document.getElementById('resultsSection');
        
        if (executionSection) executionSection.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';
    }

    // 导出执行日志
    exportLog() {
        const logText = this.logLines.map(entry => 
            `[${entry.timestamp}] ${entry.text}`
        ).join('\n');

        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        downloadFile(url, `execution_log_${this.currentExecutionId || 'unknown'}.txt`);
        
        URL.revokeObjectURL(url);
        showToast('日志已导出', 'success');
    }

    getCurrentExecutionId() {
        return this.currentExecutionId;
    }

    isCurrentlyExecuting() {
        return this.isExecuting;
    }

    // 显示执行进度区域
    showExecutionProgress() {
        const progressSection = document.getElementById('executionProgress');
        if (progressSection) {
            progressSection.style.display = 'block';
        }
    }

    // 隐藏执行进度区域
    hideExecutionProgress() {
        const progressSection = document.getElementById('executionProgress');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    }

    // 启动计时器
    startTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        this.timerInterval = setInterval(() => {
            this.updateExecutionTime();
        }, 1000);
    }

    // 停止计时器
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // 更新执行时间显示
    updateExecutionTime() {
        if (!this.executionStartTime) return;
        
        const now = new Date();
        const diff = now - this.executionStartTime;
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        
        const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const timeElement = document.getElementById('executionTime');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
    }

    // 更新日志行数
    updateLogLineCount() {
        const countElement = document.getElementById('logLineCount');
        if (countElement) {
            countElement.textContent = this.logLines.length.toString();
        }
    }

    // 更新当前活动状态
    updateCurrentActivity(activity) {
        const activityElement = document.getElementById('currentActivity');
        if (activityElement) {
            activityElement.textContent = activity;
            
            // 根据活动状态添加动态效果
            if (this.isExecuting) {
                activityElement.classList.add('executing-animation');
            } else {
                activityElement.classList.remove('executing-animation');
            }
        }
    }

    // 从日志内容推断当前活动
    updateCurrentActivityFromLog(logText) {
        if (!logText) return;
        
        const text = logText.toLowerCase();
        
        if (text.includes('generating') || text.includes('正在生成')) {
            this.updateCurrentActivity('正在生成...');
        } else if (text.includes('processing') || text.includes('正在处理')) {
            this.updateCurrentActivity('正在处理...');
        } else if (text.includes('saving') || text.includes('保存')) {
            this.updateCurrentActivity('正在保存...');
        } else if (text.includes('converting') || text.includes('转换')) {
            this.updateCurrentActivity('正在转换...');
        } else if (text.includes('validating') || text.includes('验证')) {
            this.updateCurrentActivity('正在验证...');
        } else if (text.includes('finished') || text.includes('completed') || text.includes('完成')) {
            this.updateCurrentActivity('即将完成...');
        } else if (text.includes('error') || text.includes('错误') || text.includes('failed')) {
            this.updateCurrentActivity('发生错误...');
        }
    }

    // 更新执行ID显示
    updateExecutionId(executionId) {
        const idElement = document.getElementById('executionId');
        if (idElement) {
            idElement.textContent = executionId;
            idElement.title = executionId; // 添加完整ID的悬停提示
        }
    }

    // 重置时添加进度条隐藏
    reset() {
        this.currentExecutionId = null;
        this.isExecuting = false;
        this.logLines = [];
        this.executionStartTime = null;
        this.stopTimer();
        this.updateExecutionButtons();
        this.updateExecutionStatus('ready', '就绪');
        this.updateCurrentActivity('等待中...');
        this.updateExecutionId('-');
        this.renderLog();
        this.hideExecutionProgress();

        // 隐藏执行日志和结果区域
        const executionLogCard = document.getElementById('executionLogCard');
        const resultsSection = document.getElementById('resultsSection');
        
        if (executionLogCard) executionLogCard.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';
    }

    // 安全地添加到历史记录
    addToHistory(executionData) {
        // 如果historyManager还未初始化，延迟添加
        if (window.historyManager && window.historyManager.addExecution) {
            window.historyManager.addExecution(executionData);
        } else {
            // 延迟重试
            setTimeout(() => {
                if (window.historyManager && window.historyManager.addExecution) {
                    window.historyManager.addExecution(executionData);
                } else {
                    console.warn('历史管理器未初始化，跳过添加历史记录');
                }
            }, 500);
        }
    }

    // 停止执行
    stopExecution() {
        this.isExecuting = false;
        this.stopTimer();
        this.updateExecutionButtons();
        this.updateExecutionStatus('stopped', '已停止');
        this.updateCurrentActivity('执行已停止');
        this.addLogLine('执行已停止', 'warning');
        
        // 通知WebSocket停止执行
        if (this.currentExecutionId) {
            wsService.stopExecution(this.currentExecutionId);
        }
    }
}

// 创建全局执行管理器实例
window.executionManager = new ExecutionManager();
