// 历史记录管理器组件
class HistoryManager {
    constructor() {
        this.historyData = [];
        this.currentView = 'list'; // 'list' or 'tree'
        this.expandedExecutions = new Set();
        this.isLoaded = false;
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        // 延迟加载历史记录，不阻塞页面初始化
        this.loadHistoryDataLazy();
    }

    setupEventListeners() {
        // 历史记录按钮
        const historyBtn = document.getElementById('historyBtn');
        if (historyBtn) {
            historyBtn.addEventListener('click', () => {
                this.showHistoryModal();
            });
        }

        // 刷新历史记录按钮
        const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
        if (refreshHistoryBtn) {
            refreshHistoryBtn.addEventListener('click', () => {
                this.refreshHistory();
            });
        }

        // 清空历史记录按钮
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                this.clearHistory();
            });
        }

        // 历史记录视图切换
        const historyListViewBtn = document.getElementById('historyListViewBtn');
        const historyTreeViewBtn = document.getElementById('historyTreeViewBtn');
        
        if (historyListViewBtn) {
            historyListViewBtn.addEventListener('click', () => {
                this.switchToListView();
            });
        }

        if (historyTreeViewBtn) {
            historyTreeViewBtn.addEventListener('click', () => {
                this.switchToTreeView();
            });
        }

        // 历史记录搜索
        const historySearchInput = document.getElementById('historySearchInput');
        if (historySearchInput) {
            historySearchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
    }

    // 延迟加载历史数据（不阻塞页面）
    loadHistoryDataLazy() {
        // 立即从本地存储加载，不显示loading
        this.loadFromLocalStorage();
        this.isLoaded = true;
        
        // 后台异步尝试从服务器同步数据
        setTimeout(() => {
            this.syncFromServer();
        }, 1000); // 1秒后开始同步
    }

    // 后台同步服务器数据
    async syncFromServer() {
        if (this.isLoading) return;
        
        try {
            this.isLoading = true;
            // 静默请求，不显示loading
            const response = await apiService.get('/history/executions');
            if (response && response.executions) {
                this.historyData = response.executions;
                this.saveToLocalStorage();
            }
        } catch (error) {
            console.warn('后台同步历史记录失败:', error);
            // 静默失败，不影响用户体验
        } finally {
            this.isLoading = false;
        }
    }

    // 加载历史数据（显示loading，用于手动刷新）
    async loadHistoryData() {
        if (this.isLoading) return;
        
        try {
            this.isLoading = true;
            showLoading('加载历史记录...');
            
            // 获取所有输出目录
            const response = await apiService.get('/history/executions');
            this.historyData = response.executions || [];
            this.isLoaded = true;
            
            hideLoading();
            
        } catch (error) {
            hideLoading();
            console.error('加载历史记录失败:', error);
            
            // 如果API不存在，从本地存储加载
            this.loadFromLocalStorage();
            this.isLoaded = true;
        } finally {
            this.isLoading = false;
        }
    }

    // 从本地存储加载
    loadFromLocalStorage() {
        try {
            const stored = localStorage.getItem('ai_tools_history');
            if (stored) {
                const data = JSON.parse(stored);
                // 验证数据格式
                if (Array.isArray(data)) {
                    this.historyData = data;
                    console.log(`从本地存储加载了 ${data.length} 条历史记录`);
                } else {
                    console.warn('本地存储的历史记录格式无效');
                    this.historyData = [];
                }
            } else {
                this.historyData = [];
            }
        } catch (e) {
            console.warn('加载本地历史记录失败:', e);
            this.historyData = [];
            // 清除损坏的存储
            try {
                localStorage.removeItem('ai_tools_history');
            } catch (cleanupError) {
                console.warn('清除损坏的本地存储失败:', cleanupError);
            }
        }
    }

    // 保存到本地存储
    saveToLocalStorage() {
        try {
            const dataString = JSON.stringify(this.historyData);
            localStorage.setItem('ai_tools_history', dataString);
            console.log(`保存了 ${this.historyData.length} 条历史记录到本地存储`);
        } catch (e) {
            console.warn('保存历史记录失败:', e);
            
            // 如果是存储空间不足，尝试清理旧记录
            if (e.name === 'QuotaExceededError') {
                console.log('存储空间不足，清理旧记录...');
                this.cleanupOldRecords();
                try {
                    localStorage.setItem('ai_tools_history', JSON.stringify(this.historyData));
                    console.log('清理后重新保存成功');
                } catch (retryError) {
                    console.error('清理后仍然保存失败:', retryError);
                }
            }
        }
    }

    // 清理旧记录（保留最近50条）
    cleanupOldRecords() {
        if (this.historyData.length > 50) {
            const oldLength = this.historyData.length;
            this.historyData = this.historyData.slice(0, 50);
            console.log(`清理了 ${oldLength - this.historyData.length} 条旧记录`);
        }
    }

    // 添加执行记录
    addExecution(executionData) {
        const execution = {
            id: executionData.execution_id,
            tool_name: executionData.tool_name,
            start_time: executionData.timestamp || new Date().toISOString(),
            status: executionData.success ? 'completed' : 'failed',
            output_dir: executionData.output_dir,
            files: executionData.output_files || [],
            ...executionData
        };

        // 避免重复添加
        const existingIndex = this.historyData.findIndex(item => item.id === execution.id);
        if (existingIndex >= 0) {
            this.historyData[existingIndex] = execution;
        } else {
            this.historyData.unshift(execution); // 添加到开头
        }

        // 限制历史记录数量
        if (this.historyData.length > 50) {
            this.historyData = this.historyData.slice(0, 50);
        }

        this.saveToLocalStorage();
    }

    // 显示历史记录模态框
    async showHistoryModal() {
        const modal = document.getElementById('historyModal');
        if (!modal) {
            this.createHistoryModal();
        }

        // 如果还未加载过，显示loading并加载
        if (!this.isLoaded && !this.isLoading) {
            showLoading('加载历史记录...');
            await this.loadHistoryData();
            hideLoading();
        }

        this.renderHistory();
        
        const bootstrapModal = new bootstrap.Modal(document.getElementById('historyModal'));
        bootstrapModal.show();
    }

    // 创建历史记录模态框
    createHistoryModal() {
        const modalHTML = `
            <div class="modal fade" id="historyModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-history me-2"></i>
                                执行历史记录
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- 工具栏 -->
                            <div class="history-toolbar mb-3">
                                <div class="row align-items-center">
                                    <div class="col-md-6">
                                        <div class="input-group">
                                            <span class="input-group-text">
                                                <i class="fas fa-search"></i>
                                            </span>
                                            <input type="text" id="historySearchInput" class="form-control" placeholder="搜索执行记录...">
                                        </div>
                                    </div>
                                    <div class="col-md-6 text-end">
                                        <div class="btn-group btn-group-sm me-2">
                                            <button id="historyListViewBtn" class="btn btn-outline-secondary active">
                                                <i class="fas fa-list me-1"></i>列表
                                            </button>
                                            <button id="historyTreeViewBtn" class="btn btn-outline-secondary">
                                                <i class="fas fa-sitemap me-1"></i>树形
                                            </button>
                                        </div>
                                        <button id="refreshHistoryBtn" class="btn btn-outline-primary btn-sm me-2">
                                            <i class="fas fa-sync-alt me-1"></i>刷新
                                        </button>
                                        <button id="clearHistoryBtn" class="btn btn-outline-danger btn-sm">
                                            <i class="fas fa-trash me-1"></i>清空
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <!-- 统计信息 -->
                            <div id="historyStats" class="mb-3" style="display: none;">
                                <div class="row text-center">
                                    <div class="col-md-3">
                                        <small class="text-muted">总执行次数</small>
                                        <div id="totalExecutions" class="fw-bold">0</div>
                                    </div>
                                    <div class="col-md-3">
                                        <small class="text-muted">成功次数</small>
                                        <div id="successExecutions" class="fw-bold text-success">0</div>
                                    </div>
                                    <div class="col-md-3">
                                        <small class="text-muted">失败次数</small>
                                        <div id="failedExecutions" class="fw-bold text-danger">0</div>
                                    </div>
                                    <div class="col-md-3">
                                        <small class="text-muted">总文件数</small>
                                        <div id="totalHistoryFiles" class="fw-bold">0</div>
                                    </div>
                                </div>
                                <hr>
                            </div>

                            <!-- 历史记录内容 -->
                            <div id="historyContent">
                                <div id="historyListView">
                                    <!-- 列表视图内容 -->
                                </div>
                                <div id="historyTreeView" style="display: none;">
                                    <!-- 树形视图内容 -->
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // 重新绑定事件监听器
        this.setupEventListeners();
    }

    // 渲染历史记录
    renderHistory() {
        this.showStatistics();
        
        if (this.currentView === 'list') {
            this.renderListView();
        } else {
            this.renderTreeView();
        }
    }

    // 渲染列表视图
    renderListView() {
        const container = document.getElementById('historyListView');
        if (!container) return;

        if (this.historyData.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-history fa-3x mb-3"></i>
                    <h5>暂无执行记录</h5>
                    <p>执行工具后，记录将显示在这里</p>
                </div>
            `;
            return;
        }

        // 限制一次渲染的数量，避免性能问题
        const maxRender = 20;
        const dataToRender = this.historyData.slice(0, maxRender);
        const hasMore = this.historyData.length > maxRender;

        const historyHTML = dataToRender.map(execution => {
            const statusIcon = execution.status === 'completed' ? 'check-circle text-success' : 'times-circle text-danger';
            const statusText = execution.status === 'completed' ? '成功' : '失败';
            const timeFormatted = formatDateTime(execution.start_time);
            const fileCount = execution.files ? execution.files.length : 0;

            return `
                <div class="card mb-3 execution-item" data-execution-id="${execution.id}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-0">
                                <i class="fas fa-${statusIcon} me-2"></i>
                                ${execution.tool_name} - ${execution.id}
                            </h6>
                            <small class="text-muted">${timeFormatted}</small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary view-execution-btn" 
                                    data-execution-id="${execution.id}"
                                    title="查看结果">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-info download-execution-btn" 
                                    data-execution-id="${execution.id}"
                                    title="下载结果">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-outline-danger delete-execution-btn" 
                                    data-execution-id="${execution.id}"
                                    title="删除记录">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <small class="text-muted">状态:</small>
                                <span class="badge bg-${execution.status === 'completed' ? 'success' : 'danger'}">${statusText}</span>
                            </div>
                            <div class="col-md-4">
                                <small class="text-muted">文件数量:</small>
                                <span class="fw-bold">${fileCount}</span>
                            </div>
                            <div class="col-md-4">
                                <small class="text-muted">输出目录:</small>
                                <code class="small">${execution.output_dir || '-'}</code>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // 添加"加载更多"按钮
        if (hasMore) {
            historyHTML += `
                <div class="text-center py-3">
                    <button class="btn btn-outline-primary" id="loadMoreHistory">
                        <i class="fas fa-chevron-down me-1"></i>
                        加载更多 (还有 ${this.historyData.length - maxRender} 条记录)
                    </button>
                </div>
            `;
        }

        container.innerHTML = historyHTML;
        this.setupHistoryEventListeners(container);

        // 设置"加载更多"按钮事件
        if (hasMore) {
            const loadMoreBtn = document.getElementById('loadMoreHistory');
            if (loadMoreBtn) {
                loadMoreBtn.addEventListener('click', () => {
                    this.renderAllHistory();
                });
            }
        }
    }

    // 渲染全部历史记录
    renderAllHistory() {
        const container = document.getElementById('historyListView');
        if (!container) return;

        const historyHTML = this.historyData.map(execution => {
            const statusIcon = execution.status === 'completed' ? 'check-circle text-success' : 'times-circle text-danger';
            const statusText = execution.status === 'completed' ? '成功' : '失败';
            const timeFormatted = formatDateTime(execution.start_time);
            const fileCount = execution.files ? execution.files.length : 0;

            return `
                <div class="card mb-3 execution-item" data-execution-id="${execution.id}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-0">
                                <i class="fas fa-${statusIcon} me-2"></i>
                                ${execution.tool_name} - ${execution.id}
                            </h6>
                            <small class="text-muted">${timeFormatted}</small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary view-execution-btn" 
                                    data-execution-id="${execution.id}"
                                    title="查看结果">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-info download-execution-btn" 
                                    data-execution-id="${execution.id}"
                                    title="下载结果">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-outline-danger delete-execution-btn" 
                                    data-execution-id="${execution.id}"
                                    title="删除记录">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <small class="text-muted">状态:</small>
                                <span class="badge bg-${execution.status === 'completed' ? 'success' : 'danger'}">${statusText}</span>
                            </div>
                            <div class="col-md-4">
                                <small class="text-muted">文件数量:</small>
                                <span class="fw-bold">${fileCount}</span>
                            </div>
                            <div class="col-md-4">
                                <small class="text-muted">输出目录:</small>
                                <code class="small">${execution.output_dir || '-'}</code>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = historyHTML;
        this.setupHistoryEventListeners(container);
    }

    // 设置历史记录事件监听器
    setupHistoryEventListeners(container) {
        // 查看执行结果
        container.querySelectorAll('.view-execution-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const executionId = btn.dataset.executionId;
                this.viewExecution(executionId);
            });
        });

        // 下载执行结果
        container.querySelectorAll('.download-execution-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const executionId = btn.dataset.executionId;
                this.downloadExecution(executionId);
            });
        });

        // 删除执行记录
        container.querySelectorAll('.delete-execution-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const executionId = btn.dataset.executionId;
                this.deleteExecution(executionId);
            });
        });
    }

    // 查看执行结果
    async viewExecution(executionId) {
        try {
            const execution = this.historyData.find(item => item.id === executionId);
            if (!execution) {
                showToast('执行记录不存在', 'error');
                return;
            }

            // 关闭历史记录模态框
            const historyModal = bootstrap.Modal.getInstance(document.getElementById('historyModal'));
            if (historyModal) {
                historyModal.hide();
            }

            // 显示结果
            if (window.resultsManager && window.resultsManager.showResults) {
                // 确保files是数组格式
                const files = Array.isArray(execution.files) ? execution.files : [];
                window.resultsManager.showResults(executionId, files);
            } else {
                console.error('结果管理器未初始化');
                showToast('结果管理器未初始化', 'error');
            }
            
        } catch (error) {
            console.error('查看执行结果失败:', error);
            showToast('查看执行结果失败: ' + error.message, 'error');
        }
    }

    // 下载执行结果
    downloadExecution(executionId) {
        try {
            const url = apiService.getDownloadZipUrl(executionId);
            downloadFile(url, `${executionId}_results.zip`);
            showToast('开始下载执行结果', 'success');
        } catch (error) {
            console.error('下载失败:', error);
            showToast('下载失败: ' + error.message, 'error');
        }
    }

    // 删除执行记录
    async deleteExecution(executionId) {
        const confirmed = await confirmDialog('确定要删除这个执行记录吗？', '确认删除');
        if (!confirmed) return;

        try {
            // 从数组中移除
            this.historyData = this.historyData.filter(item => item.id !== executionId);
            this.saveToLocalStorage();
            
            // 重新渲染
            this.renderHistory();
            
            showToast('执行记录已删除', 'success');
            
        } catch (error) {
            console.error('删除执行记录失败:', error);
            showToast('删除失败: ' + error.message, 'error');
        }
    }

    // 显示统计信息
    showStatistics() {
        const total = this.historyData.length;
        const success = this.historyData.filter(item => item.status === 'completed').length;
        const failed = total - success;
        const totalFiles = this.historyData.reduce((sum, item) => sum + (item.files ? item.files.length : 0), 0);

        document.getElementById('totalExecutions').textContent = total;
        document.getElementById('successExecutions').textContent = success;
        document.getElementById('failedExecutions').textContent = failed;
        document.getElementById('totalHistoryFiles').textContent = totalFiles;

        const statsElement = document.getElementById('historyStats');
        if (statsElement) {
            statsElement.style.display = 'block';
        }
    }

    // 视图切换
    switchToListView() {
        this.currentView = 'list';
        document.getElementById('historyListViewBtn').classList.add('active');
        document.getElementById('historyTreeViewBtn').classList.remove('active');
        document.getElementById('historyListView').style.display = 'block';
        document.getElementById('historyTreeView').style.display = 'none';
        this.renderListView();
    }

    switchToTreeView() {
        this.currentView = 'tree';
        document.getElementById('historyTreeViewBtn').classList.add('active');
        document.getElementById('historyListViewBtn').classList.remove('active');
        document.getElementById('historyListView').style.display = 'none';
        document.getElementById('historyTreeView').style.display = 'block';
        this.renderTreeView();
    }

    // 渲染树形视图
    renderTreeView() {
        const container = document.getElementById('historyTreeView');
        if (!container) return;

        // 按工具分组
        const groupedData = {};
        this.historyData.forEach(execution => {
            if (!groupedData[execution.tool_name]) {
                groupedData[execution.tool_name] = [];
            }
            groupedData[execution.tool_name].push(execution);
        });

        if (Object.keys(groupedData).length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-history fa-3x mb-3"></i>
                    <h5>暂无执行记录</h5>
                </div>
            `;
            return;
        }

        let treeHTML = '<ul class="history-tree">';
        
        Object.keys(groupedData).forEach(toolName => {
            const executions = groupedData[toolName];
            const isExpanded = this.expandedExecutions.has(toolName);
            
            treeHTML += `
                <li class="tree-item">
                    <div class="tree-item-content tool-group" data-tool-name="${toolName}">
                        <span class="tree-toggle" data-tool-name="${toolName}">
                            <i class="fas fa-chevron-${isExpanded ? 'down' : 'right'}"></i>
                        </span>
                        <i class="fas fa-tools tree-icon"></i>
                        <span class="tree-label">${toolName} (${executions.length})</span>
                    </div>
                    <ul class="tree-children ${isExpanded ? 'expanded' : ''}">
            `;
            
            executions.forEach(execution => {
                const statusIcon = execution.status === 'completed' ? 'check-circle text-success' : 'times-circle text-danger';
                const timeFormatted = formatRelativeTime(execution.start_time);
                
                treeHTML += `
                    <li class="tree-item">
                        <div class="tree-item-content execution-item" data-execution-id="${execution.id}">
                            <span class="tree-toggle empty"></span>
                            <i class="fas fa-${statusIcon} tree-icon"></i>
                            <span class="tree-label">${execution.id}</span>
                            <span class="file-info">${timeFormatted}</span>
                            <div class="tree-actions">
                                <button class="tree-action-btn btn btn-primary view-execution-btn" 
                                        data-execution-id="${execution.id}" title="查看结果">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="tree-action-btn btn btn-success download-execution-btn" 
                                        data-execution-id="${execution.id}" title="下载结果">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="tree-action-btn btn btn-danger delete-execution-btn" 
                                        data-execution-id="${execution.id}" title="删除记录">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </li>
                `;
            });
            
            treeHTML += `
                    </ul>
                </li>
            `;
        });
        
        treeHTML += '</ul>';
        container.innerHTML = treeHTML;
        
        this.setupTreeEventListeners(container);
    }

    // 设置树形视图事件监听器
    setupTreeEventListeners(container) {
        // 工具组展开/收起
        container.querySelectorAll('.tree-toggle').forEach(toggle => {
            if (!toggle.classList.contains('empty')) {
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const toolName = toggle.dataset.toolName;
                    this.toggleToolGroup(toolName);
                });
            }
        });

        // 设置执行项事件监听器
        this.setupHistoryEventListeners(container);
    }

    // 工具组展开/收起
    toggleToolGroup(toolName) {
        const toggle = document.querySelector(`[data-tool-name="${toolName}"] .tree-toggle i`);
        const children = toggle.closest('.tree-item').querySelector('.tree-children');
        
        if (this.expandedExecutions.has(toolName)) {
            this.expandedExecutions.delete(toolName);
            toggle.className = 'fas fa-chevron-right';
            children.classList.remove('expanded');
        } else {
            this.expandedExecutions.add(toolName);
            toggle.className = 'fas fa-chevron-down';
            children.classList.add('expanded');
        }
    }

    // 搜索处理
    handleSearch(query) {
        if (!query.trim()) {
            this.renderHistory();
            return;
        }

        const filteredData = this.historyData.filter(execution =>
            execution.id.toLowerCase().includes(query.toLowerCase()) ||
            execution.tool_name.toLowerCase().includes(query.toLowerCase()) ||
            (execution.output_dir && execution.output_dir.toLowerCase().includes(query.toLowerCase()))
        );

        // 临时更新显示
        const originalData = [...this.historyData]; // 创建副本
        this.historyData = filteredData;
        this.renderHistory();
        this.historyData = originalData; // 恢复原始数据
    }

    // 刷新历史记录
    async refreshHistory() {
        await this.loadHistoryData();
        this.renderHistory();
        showToast('历史记录已刷新', 'success');
    }

    // 清空历史记录
    async clearHistory() {
        const confirmed = await confirmDialog('确定要清空所有历史记录吗？此操作不可恢复。', '确认清空');
        if (!confirmed) return;

        this.historyData = [];
        this.saveToLocalStorage();
        this.renderHistory();
        showToast('历史记录已清空', 'success');
    }
}

// 延迟创建全局历史管理器实例，避免阻塞页面加载
function initHistoryManager() {
    if (!window.historyManager) {
        window.historyManager = new HistoryManager();
        console.log('历史管理器初始化完成');
    }
}

// 在页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(initHistoryManager, 100); // 延迟100ms，确保其他组件先加载
    });
} else {
    setTimeout(initHistoryManager, 100);
}
