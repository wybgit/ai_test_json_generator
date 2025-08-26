// 结果管理器组件
class ResultsManager {
    constructor() {
        this.currentExecutionId = null;
        this.resultFiles = [];
        this.fileTree = {};
        this.currentView = 'list'; // 'list' or 'tree'
        this.expandedFolders = new Set();
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 下载全部结果按钮
        const downloadAllBtn = document.getElementById('downloadAllBtn');
        if (downloadAllBtn) {
            downloadAllBtn.addEventListener('click', () => {
                this.downloadAllResults();
            });
        }

        // 文件查看模态框中的下载按钮
        const downloadFileBtn = document.getElementById('downloadFileBtn');
        if (downloadFileBtn) {
            downloadFileBtn.addEventListener('click', () => {
                this.downloadCurrentFile();
            });
        }

        // 文件查看模态框中的复制按钮
        const copyFileBtn = document.getElementById('copyFileBtn');
        if (copyFileBtn) {
            copyFileBtn.addEventListener('click', () => {
                this.copyFileContent();
            });
        }

        // 视图切换按钮
        const listViewBtn = document.getElementById('listViewBtn');
        const treeViewBtn = document.getElementById('treeViewBtn');
        
        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => {
                this.switchToListView();
            });
        }

        if (treeViewBtn) {
            treeViewBtn.addEventListener('click', () => {
                this.switchToTreeView();
            });
        }

        // 文件搜索
        const searchInput = document.getElementById('fileSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            
            // 预设onnx和json搜索内容
            searchInput.setAttribute('placeholder', '搜索文件... (例如: onnx, json)');
            
            // 添加搜索建议
            this.setupSearchSuggestions(searchInput);
        }
    }

    showResults(executionId, files) {
        this.currentExecutionId = executionId;
        this.resultFiles = files || [];
        
        // 构建文件树
        this.buildFileTree();
        
        // 显示结果区域和统计
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            
            // 显示统计信息
            this.showStatistics();
            
            // 渲染当前视图
            this.renderCurrentView();
            
            // 更新搜索建议
            this.updateSearchSuggestions();
            
            // 平滑滚动到结果区域
            setTimeout(() => {
                scrollToElement(resultsSection, 100);
            }, 100);
        }
    }

    // 构建文件树结构
    buildFileTree() {
        this.fileTree = {};
        
        this.resultFiles.forEach(file => {
            const pathParts = file.path.split('/');
            let currentLevel = this.fileTree;
            
            // 创建目录结构
            for (let i = 0; i < pathParts.length - 1; i++) {
                const part = pathParts[i];
                if (!currentLevel[part]) {
                    currentLevel[part] = {
                        type: 'folder',
                        name: part,
                        children: {},
                        files: []
                    };
                }
                currentLevel = currentLevel[part].children;
            }
            
            // 添加文件
            const fileName = pathParts[pathParts.length - 1];
            if (!currentLevel._files) {
                currentLevel._files = [];
            }
            currentLevel._files.push({
                ...file,
                type: 'file',
                name: fileName
            });
        });
    }

    // 渲染当前视图
    renderCurrentView() {
        if (this.currentView === 'list') {
            this.renderListView();
        } else {
            this.renderTreeView();
        }
    }

    // 渲染列表视图
    renderListView() {
        const container = document.getElementById('resultsListView');
        if (!container) return;

        if (this.resultFiles.length === 0) {
            container.innerHTML = `
                <div class="list-group-item text-center text-muted">
                    <i class="fas fa-folder-open fa-2x mb-2"></i>
                    <p class="mb-0">暂无生成的文件</p>
                </div>
            `;
            return;
        }

        const filesHtml = this.resultFiles.map(file => {
            const icon = this.getFileIcon(file.name);
            const sizeFormatted = formatFileSize(file.size);
            const dateFormatted = formatRelativeTime(file.modified);
            
            return `
                <div class="list-group-item list-group-item-action file-item d-flex justify-content-between align-items-center"
                     data-file-path="${escapeHtml(file.path)}"
                     data-file-name="${escapeHtml(file.name)}">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-${icon} me-3 text-primary"></i>
                        <div>
                            <h6 class="mb-1">${escapeHtml(file.name)}</h6>
                            <small class="text-muted">
                                <span class="file-size">${sizeFormatted}</span>
                                <span class="mx-2">•</span>
                                <span class="file-date">${dateFormatted}</span>
                                <span class="mx-2">•</span>
                                <span class="file-path">${escapeHtml(file.path)}</span>
                            </small>
                        </div>
                    </div>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary view-file-btn"
                                data-file-path="${escapeHtml(file.path)}"
                                data-file-name="${escapeHtml(file.name)}">
                            <i class="fas fa-eye me-1"></i>
                            查看
                        </button>
                        <button type="button" class="btn btn-outline-success download-file-btn"
                                data-file-path="${escapeHtml(file.path)}"
                                data-file-name="${escapeHtml(file.name)}">
                            <i class="fas fa-download me-1"></i>
                            下载
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = filesHtml;

        // 添加事件监听器
        this.setupListViewEventListeners(container);
    }

    // 渲染树形视图
    renderTreeView() {
        const container = document.getElementById('fileTree');
        if (!container) return;

        if (this.resultFiles.length === 0) {
            container.innerHTML = `
                <li class="text-center text-muted py-4">
                    <i class="fas fa-folder-open fa-2x mb-2"></i>
                    <p class="mb-0">暂无生成的文件</p>
                </li>
            `;
            return;
        }

        container.innerHTML = this.buildTreeHTML(this.fileTree, '');
        this.setupTreeViewEventListeners(container);
    }

    // 构建树形HTML
    buildTreeHTML(tree, path) {
        let html = '';
        
        // 遍历文件夹
        Object.keys(tree).forEach(key => {
            if (key !== '_files') {
                const folder = tree[key];
                const folderPath = path ? `${path}/${key}` : key;
                const isExpanded = this.expandedFolders.has(folderPath);
                
                html += `
                    <li class="tree-item">
                        <div class="tree-item-content" data-folder-path="${escapeHtml(folderPath)}">
                            <span class="tree-toggle" data-folder-path="${escapeHtml(folderPath)}">
                                <i class="fas fa-chevron-${isExpanded ? 'down' : 'right'}"></i>
                            </span>
                            <i class="fas fa-folder tree-icon folder"></i>
                            <span class="tree-label">${escapeHtml(key)}</span>
                        </div>
                        <ul class="tree-children ${isExpanded ? 'expanded' : ''}">
                            ${this.buildTreeHTML(folder.children, folderPath)}
                        </ul>
                    </li>
                `;
            }
        });
        
        // 添加文件
        if (tree._files) {
            tree._files.forEach(file => {
                const icon = this.getFileIcon(file.name);
                const iconClass = this.getFileIconClass(file.name);
                const sizeFormatted = formatFileSize(file.size);
                
                html += `
                    <li class="tree-item">
                        <div class="tree-item-content" data-file-path="${escapeHtml(file.path)}" data-file-name="${escapeHtml(file.name)}">
                            <span class="tree-toggle empty"></span>
                            <i class="fas fa-${icon} tree-icon ${iconClass}"></i>
                            <span class="tree-label">${escapeHtml(file.name)}</span>
                            <span class="file-info">${sizeFormatted}</span>
                            <div class="tree-actions">
                                <button class="tree-action-btn btn btn-primary view-file-btn" 
                                        data-file-path="${escapeHtml(file.path)}" 
                                        data-file-name="${escapeHtml(file.name)}"
                                        title="查看文件">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="tree-action-btn btn btn-success download-file-btn" 
                                        data-file-path="${escapeHtml(file.path)}" 
                                        data-file-name="${escapeHtml(file.name)}"
                                        title="下载文件">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                    </li>
                `;
            });
        }
        
        return html;
    }

    // 获取文件图标的CSS类
    getFileIconClass(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        const classMap = {
            'json': 'json',
            'onnx': 'onnx',
            'txt': 'file',
            'log': 'file',
            'csv': 'file'
        };
        return classMap[extension] || 'file';
    }

    // 设置列表视图事件监听器
    setupListViewEventListeners(container) {

        // 查看文件按钮
        container.querySelectorAll('.view-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filePath = btn.dataset.filePath;
                const fileName = btn.dataset.fileName;
                this.viewFile(filePath, fileName);
            });
        });

        // 下载文件按钮
        container.querySelectorAll('.download-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filePath = btn.dataset.filePath;
                const fileName = btn.dataset.fileName;
                this.downloadFile(filePath, fileName);
            });
        });

        // 双击文件项查看文件
        container.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('dblclick', () => {
                const filePath = item.dataset.filePath;
                const fileName = item.dataset.fileName;
                this.viewFile(filePath, fileName);
            });
        });
    }



    async viewFile(filePath, fileName) {
        try {
            console.log('开始查看文件:', { filePath, fileName, executionId: this.currentExecutionId });
            
            if (!this.currentExecutionId) {
                throw new Error('执行ID不存在，请重新执行工具');
            }

            // 检查是否是ONNX文件
            if (fileName.toLowerCase().endsWith('.onnx')) {
                this.viewOnnxFile(filePath, fileName);
                return;
            }
            
            // 检查是否是CSV文件
            if (fileName.toLowerCase().endsWith('.csv')) {
                this.viewCsvFile(filePath, fileName);
                return;
            }
            
            showLoading('加载文件内容...');
            
            // 对文件路径进行编码以处理特殊字符
            const encodedFilePath = encodeURIComponent(filePath);
            console.log('编码后的文件路径:', encodedFilePath);
            
            const response = await apiService.viewOutputFile(this.currentExecutionId, filePath);
            console.log('API响应:', response);
            
            // 检查响应是否有效
            if (!response || response.content === undefined) {
                throw new Error('文件内容为空或无效');
            }
            
            // 显示文件内容模态框
            this.showFileModal(fileName, response.content, response.is_binary);
            
            hideLoading();
            
        } catch (error) {
            hideLoading();
            console.error('查看文件失败:', {
                error: error,
                message: error.message,
                executionId: this.currentExecutionId,
                filePath: filePath,
                fileName: fileName
            });
            
            // 提供更详细的错误信息
            let errorMessage = error.message;
            if (error.message.includes('404')) {
                errorMessage = '文件未找到，可能已被删除或移动';
            } else if (error.message.includes('403')) {
                errorMessage = '没有权限访问此文件';
            } else if (error.message.includes('500')) {
                errorMessage = '服务器内部错误，请稍后重试';
            } else if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
                errorMessage = '网络连接错误，请检查服务器状态';
            }
            
            showToast('查看文件失败: ' + errorMessage, 'error');
        }
    }

    showFileModal(fileName, content, isBinary = false) {
        const modal = document.getElementById('fileViewModal');
        const modalTitle = document.getElementById('modalFileName');
        const fileContentElement = document.getElementById('fileContent');
        
        if (!modal || !modalTitle || !fileContentElement) return;

        // 设置文件名
        modalTitle.textContent = fileName;
        
        // 设置当前文件信息
        this.currentViewingFile = {
            name: fileName,
            content: content,
            isBinary: isBinary
        };

        // 显示内容
        if (isBinary) {
            fileContentElement.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-file-code fa-3x mb-3"></i>
                    <h5>二进制文件</h5>
                    <p class="mb-1">无法显示内容</p>
                    <small>文件名: ${escapeHtml(fileName)}</small><br>
                    <small>大小: ${formatFileSize(content.length || 0)}</small>
                </div>
            `;
        } else {
            // 根据文件类型选择语法高亮和特殊处理
            const extension = fileName.split('.').pop().toLowerCase();
            
            if (extension === 'json') {
                this.showJsonContent(fileContentElement, content, fileName);
            } else if (extension === 'onnx') {
                this.showOnnxContent(fileContentElement, content, fileName);
            } else {
                this.showTextContent(fileContentElement, content, fileName);
            }
        }

        // 确保先隐藏loading
        hideLoading();
        
        // 显示模态框
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    // 显示JSON内容
    showJsonContent(container, content, fileName) {
        try {
            // 尝试解析JSON以验证格式
            const jsonObj = JSON.parse(content);
            const formattedJson = JSON.stringify(jsonObj, null, 2);
            
            // 创建带有JSON查看器的内容
            container.innerHTML = `
                <div class="json-viewer-container">
                    <div class="json-viewer-header d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <span class="badge bg-success me-2">JSON</span>
                            <small class="text-muted">有效的JSON格式</small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" id="jsonRawView">原始</button>
                            <button class="btn btn-outline-primary active" id="jsonFormattedView">格式化</button>
                            <button class="btn btn-outline-info" id="jsonTreeView">树形</button>
                        </div>
                    </div>
                    <div id="jsonContent">
                        <pre class="json-formatted"><code class="language-json">${escapeHtml(formattedJson)}</code></pre>
                    </div>
                </div>
            `;
            
            // 应用语法高亮
            setTimeout(() => {
                if (typeof Prism !== 'undefined') {
                    try {
                        Prism.highlightAll();
                    } catch (e) {
                        console.warn('Prism语法高亮失败:', e);
                    }
                }
            }, 10);
            
            // 设置JSON查看器事件
            this.setupJsonViewerEvents(container, content, formattedJson, jsonObj);
            
        } catch (e) {
            // JSON解析失败，显示为普通文本
            container.innerHTML = `
                <div class="json-viewer-container">
                    <div class="json-viewer-header mb-3">
                        <span class="badge bg-warning me-2">JSON</span>
                        <small class="text-muted text-danger">JSON格式错误: ${e.message}</small>
                    </div>
                    <pre class="json-error"><code class="language-text">${escapeHtml(content)}</code></pre>
                </div>
            `;
        }
    }

    // 设置JSON查看器事件
    setupJsonViewerEvents(container, rawContent, formattedContent, jsonObj) {
        const jsonContent = container.querySelector('#jsonContent');
        const rawBtn = container.querySelector('#jsonRawView');
        const formattedBtn = container.querySelector('#jsonFormattedView');
        const treeBtn = container.querySelector('#jsonTreeView');

        if (rawBtn) {
            rawBtn.addEventListener('click', () => {
                this.setActiveJsonView(rawBtn, [formattedBtn, treeBtn]);
                jsonContent.innerHTML = `<pre class="json-raw"><code class="language-json">${escapeHtml(rawContent)}</code></pre>`;
                setTimeout(() => {
                    if (typeof Prism !== 'undefined') {
                        try {
                            Prism.highlightAll();
                        } catch (e) {
                            console.warn('Prism语法高亮失败:', e);
                        }
                    }
                }, 10);
            });
        }

        if (formattedBtn) {
            formattedBtn.addEventListener('click', () => {
                this.setActiveJsonView(formattedBtn, [rawBtn, treeBtn]);
                jsonContent.innerHTML = `<pre class="json-formatted"><code class="language-json">${escapeHtml(formattedContent)}</code></pre>`;
                setTimeout(() => {
                    if (typeof Prism !== 'undefined') {
                        try {
                            Prism.highlightAll();
                        } catch (e) {
                            console.warn('Prism语法高亮失败:', e);
                        }
                    }
                }, 10);
            });
        }

        if (treeBtn) {
            treeBtn.addEventListener('click', () => {
                this.setActiveJsonView(treeBtn, [rawBtn, formattedBtn]);
                jsonContent.innerHTML = this.buildJsonTree(jsonObj);
            });
        }
    }

    // 设置JSON查看器按钮状态
    setActiveJsonView(activeBtn, otherBtns) {
        activeBtn.classList.add('active');
        otherBtns.forEach(btn => btn.classList.remove('active'));
    }

    // 构建JSON树形视图
    buildJsonTree(obj, level = 0) {
        if (obj === null) return `<span class="json-null">null</span>`;
        if (typeof obj === 'boolean') return `<span class="json-boolean">${obj}</span>`;
        if (typeof obj === 'number') return `<span class="json-number">${obj}</span>`;
        if (typeof obj === 'string') return `<span class="json-string">"${escapeHtml(obj)}"</span>`;
        
        const indent = '  '.repeat(level);
        
        if (Array.isArray(obj)) {
            if (obj.length === 0) return '<span class="json-array">[]</span>';
            
            let html = '<span class="json-bracket">[</span>\n';
            obj.forEach((item, index) => {
                html += `${indent}  ${this.buildJsonTree(item, level + 1)}`;
                if (index < obj.length - 1) html += ',';
                html += '\n';
            });
            html += `${indent}<span class="json-bracket">]</span>`;
            return html;
        }
        
        if (typeof obj === 'object') {
            const keys = Object.keys(obj);
            if (keys.length === 0) return '<span class="json-object">{}</span>';
            
            let html = '<span class="json-bracket">{</span>\n';
            keys.forEach((key, index) => {
                html += `${indent}  <span class="json-key">"${escapeHtml(key)}"</span>: ${this.buildJsonTree(obj[key], level + 1)}`;
                if (index < keys.length - 1) html += ',';
                html += '\n';
            });
            html += `${indent}<span class="json-bracket">}</span>`;
            return html;
        }
        
        return String(obj);
    }

    // 显示ONNX内容
    showOnnxContent(container, content, fileName) {
        container.innerHTML = `
            <div class="onnx-viewer-container">
                <div class="onnx-viewer-header text-center p-4">
                    <i class="fas fa-brain fa-3x text-primary mb-3"></i>
                    <h5>ONNX 模型文件</h5>
                    <p class="text-muted mb-1">${escapeHtml(fileName)}</p>
                    <small class="text-muted">大小: ${formatFileSize(content.length)}</small>
                </div>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    ONNX模型文件是二进制格式，无法直接显示内容。
                    <br>您可以下载文件并使用专业的ONNX查看工具（如Netron）来查看模型结构。
                </div>
                <div class="text-center">
                    <a href="https://netron.app" target="_blank" class="btn btn-outline-primary">
                        <i class="fas fa-external-link-alt me-2"></i>
                        在线模型查看器 (Netron)
                    </a>
                </div>
            </div>
        `;
    }

    // 显示普通文本内容
    showTextContent(container, content, fileName) {
        const language = this.getLanguageFromFileName(fileName);
        const highlighted = highlightCode(content, language);
        container.innerHTML = `<pre><code class="language-${language}">${highlighted}</code></pre>`;
        
        setTimeout(() => {
            if (typeof Prism !== 'undefined') {
                try {
                    Prism.highlightAll();
                } catch (e) {
                    console.warn('Prism语法高亮失败:', e);
                }
            }
        }, 10);
    }

    getLanguageFromFileName(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        const languageMap = {
            'json': 'json',
            'js': 'javascript',
            'py': 'python',
            'xml': 'xml',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'txt': 'text',
            'log': 'text',
            'csv': 'text'
        };
        return languageMap[extension] || 'text';
    }

    downloadFile(filePath, fileName) {
        try {
            const url = apiService.getDownloadUrl(`${this.currentExecutionId}/${filePath}`);
            downloadFile(url, fileName);
            showToast(`开始下载 ${fileName}`, 'success');
        } catch (error) {
            console.error('下载文件失败:', error);
            showToast('下载文件失败: ' + error.message, 'error');
        }
    }

    downloadCurrentFile() {
        if (!this.currentViewingFile) return;
        
        const fileName = this.currentViewingFile.name;
        const content = this.currentViewingFile.content;
        
        // 创建下载链接
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        downloadFile(url, fileName);
        
        URL.revokeObjectURL(url);
        showToast(`开始下载 ${fileName}`, 'success');
    }

    downloadAllResults() {
        if (!this.currentExecutionId) {
            showToast('没有可下载的结果', 'warning');
            return;
        }

        try {
            const url = apiService.getDownloadZipUrl(this.currentExecutionId);
            downloadFile(url, `${this.currentExecutionId}_results.zip`);
            showToast('开始下载所有结果', 'success');
        } catch (error) {
            console.error('下载失败:', error);
            showToast('下载失败: ' + error.message, 'error');
        }
    }

    // 刷新结果列表
    async refresh() {
        if (!this.currentExecutionId) return;

        try {
            const results = await apiService.getExecutionOutputs(this.currentExecutionId);
            this.resultFiles = results.files;
            this.renderFilesList();
            showToast('结果列表已刷新', 'success');
        } catch (error) {
            console.error('刷新结果失败:', error);
            showToast('刷新结果失败: ' + error.message, 'error');
        }
    }

    // 清空结果
    clear() {
        this.currentExecutionId = null;
        this.resultFiles = [];
        this.currentViewingFile = null;
        
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
    }

    // 复制文件内容到剪贴板
    async copyFileContent() {
        if (!this.currentViewingFile || this.currentViewingFile.isBinary) {
            showToast('无法复制二进制文件内容', 'warning');
            return;
        }

        const success = await copyToClipboard(this.currentViewingFile.content);
        if (success) {
            showToast('文件内容已复制到剪贴板', 'success');
        }
    }

    // 搜索文件
    searchFiles(query) {
        if (!query.trim()) {
            this.renderFilesList();
            return;
        }

        const filteredFiles = this.resultFiles.filter(file =>
            file.name.toLowerCase().includes(query.toLowerCase()) ||
            file.path.toLowerCase().includes(query.toLowerCase())
        );

        const container = document.getElementById('resultsList');
        if (!container) return;

        if (filteredFiles.length === 0) {
            container.innerHTML = `
                <div class="list-group-item text-center text-muted">
                    <i class="fas fa-search fa-2x mb-2"></i>
                    <p class="mb-0">未找到匹配的文件</p>
                </div>
            `;
            return;
        }

        // 临时设置过滤后的文件列表
        const originalFiles = this.resultFiles;
        this.resultFiles = filteredFiles;
        this.renderFilesList();
        this.resultFiles = originalFiles;
    }

    // 获取统计信息
    getStatistics() {
        const totalFiles = this.resultFiles.length;
        const totalSize = this.resultFiles.reduce((sum, file) => sum + file.size, 0);
        
        const fileTypes = {};
        this.resultFiles.forEach(file => {
            const extension = file.name.split('.').pop().toLowerCase();
            fileTypes[extension] = (fileTypes[extension] || 0) + 1;
        });

        return {
            totalFiles,
            totalSize: formatFileSize(totalSize),
            fileTypes
        };
    }

    // 视图切换方法
    switchToListView() {
        this.currentView = 'list';
        document.getElementById('listViewBtn').classList.add('active');
        document.getElementById('treeViewBtn').classList.remove('active');
        document.getElementById('resultsListView').style.display = 'block';
        document.getElementById('resultsTreeView').style.display = 'none';
        this.renderListView();
    }

    switchToTreeView() {
        this.currentView = 'tree';
        document.getElementById('treeViewBtn').classList.add('active');
        document.getElementById('listViewBtn').classList.remove('active');
        document.getElementById('resultsListView').style.display = 'none';
        document.getElementById('resultsTreeView').style.display = 'block';
        this.renderTreeView();
    }

    // 设置树形视图事件监听器
    setupTreeViewEventListeners(container) {
        // 文件夹展开/收起
        container.querySelectorAll('.tree-toggle').forEach(toggle => {
            if (!toggle.classList.contains('empty')) {
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const folderPath = toggle.dataset.folderPath;
                    this.toggleFolder(folderPath);
                });
            }
        });

        // 查看文件按钮
        container.querySelectorAll('.view-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filePath = btn.dataset.filePath;
                const fileName = btn.dataset.fileName;
                this.viewFile(filePath, fileName);
            });
        });

        // 下载文件按钮
        container.querySelectorAll('.download-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filePath = btn.dataset.filePath;
                const fileName = btn.dataset.fileName;
                this.downloadFile(filePath, fileName);
            });
        });

        // 双击文件查看
        container.querySelectorAll('.tree-item-content[data-file-path]').forEach(item => {
            item.addEventListener('dblclick', () => {
                const filePath = item.dataset.filePath;
                const fileName = item.dataset.fileName;
                this.viewFile(filePath, fileName);
            });
        });
    }

    // 文件夹展开/收起
    toggleFolder(folderPath) {
        const toggle = document.querySelector(`[data-folder-path="${folderPath}"] .tree-toggle i`);
        const children = toggle.closest('.tree-item').querySelector('.tree-children');
        
        if (this.expandedFolders.has(folderPath)) {
            this.expandedFolders.delete(folderPath);
            toggle.className = 'fas fa-chevron-right';
            children.classList.remove('expanded');
        } else {
            this.expandedFolders.add(folderPath);
            toggle.className = 'fas fa-chevron-down';
            children.classList.add('expanded');
        }
    }

    // 显示统计信息
    showStatistics() {
        const stats = this.getStatistics();
        
        document.getElementById('totalFiles').textContent = stats.totalFiles;
        document.getElementById('totalSize').textContent = stats.totalSize;
        document.getElementById('jsonCount').textContent = stats.fileTypes.json || 0;
        document.getElementById('otherCount').textContent = stats.totalFiles - (stats.fileTypes.json || 0);
        
        const statsElement = document.getElementById('resultsStats');
        if (statsElement) {
            statsElement.style.display = 'block';
        }
    }

    // 处理搜索
    handleSearch(query) {
        if (!query.trim()) {
            this.renderCurrentView();
            return;
        }

        const filteredFiles = this.resultFiles.filter(file =>
            file.name.toLowerCase().includes(query.toLowerCase()) ||
            file.path.toLowerCase().includes(query.toLowerCase())
        );

        // 临时更新显示
        const originalFiles = this.resultFiles;
        this.resultFiles = filteredFiles;
        this.buildFileTree();
        this.renderCurrentView();
        this.resultFiles = originalFiles; // 恢复原始数据
    }

    // 设置列表视图事件监听器的完整实现
    setupListViewEventListeners(container) {
        // 查看文件按钮
        container.querySelectorAll('.view-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filePath = btn.dataset.filePath;
                const fileName = btn.dataset.fileName;
                this.viewFile(filePath, fileName);
            });
        });

        // 下载文件按钮
        container.querySelectorAll('.download-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filePath = btn.dataset.filePath;
                const fileName = btn.dataset.fileName;
                this.downloadFile(filePath, fileName);
            });
        });

        // 双击文件项查看文件
        container.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('dblclick', () => {
                const filePath = item.dataset.filePath;
                const fileName = item.dataset.fileName;
                this.viewFile(filePath, fileName);
            });
        });
    }

    // 查看ONNX文件
    viewOnnxFile(filePath, fileName) {
        try {
            console.log('预览ONNX文件:', { filePath, fileName });
            
            // 构建文件下载URL
            const downloadUrl = `http://localhost:5000/api/download/${this.currentExecutionId}/${filePath}`;
            
            // 设置文件名
            const onnxFileNameElement = document.getElementById('onnxFileName');
            if (onnxFileNameElement) {
                onnxFileNameElement.textContent = fileName;
            }

            // 设置Netron查看器
            this.setupNetronViewer(downloadUrl, fileName);
            
            // 显示ONNX预览模态框
            const modal = new bootstrap.Modal(document.getElementById('onnxPreviewModal'));
            modal.show();
            
        } catch (error) {
            console.error('预览ONNX文件失败:', error);
            showToast('预览ONNX文件失败: ' + error.message, 'error');
        }
    }

    // 设置Netron查看器
    setupNetronViewer(fileUrl, fileName) {
        const iframe = document.getElementById('netronViewer');
        const openInNetronBtn = document.getElementById('openInNetronBtn');
        
        if (iframe) {
            // 使用在线Netron服务预览ONNX模型
            // Netron支持通过URL参数加载远程文件
            const netronUrl = `https://netron.app/?url=${encodeURIComponent(fileUrl)}`;
            iframe.src = netronUrl;
        }

        // 设置在新窗口打开按钮
        if (openInNetronBtn) {
            openInNetronBtn.onclick = () => {
                const netronUrl = `https://netron.app/?url=${encodeURIComponent(fileUrl)}`;
                window.open(netronUrl, '_blank', 'width=1200,height=800');
            };
        }
    }

    // 获取文件类型图标（更新以支持ONNX和CSV）
    getFileIcon(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        const iconMap = {
            'json': 'file-code',
            'txt': 'file-alt',
            'csv': 'table',  // 使用表格图标
            'log': 'file-alt',
            'onnx': 'project-diagram'  // 为ONNX文件添加特殊图标
        };
        return iconMap[extension] || 'file';
    }

    // 设置搜索建议
    setupSearchSuggestions(searchInput) {
        const suggestions = document.getElementById('searchSuggestions');
        if (!suggestions) return;

        // 聚焦时显示建议
        searchInput.addEventListener('focus', () => {
            suggestions.style.display = 'block';
        });

        // 失焦时隐藏建议（延迟以允许点击建议）
        searchInput.addEventListener('blur', () => {
            setTimeout(() => {
                suggestions.style.display = 'none';
            }, 200);
        });

        // 点击搜索标签
        suggestions.querySelectorAll('.search-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const searchTerm = tag.dataset.search;
                searchInput.value = searchTerm;
                this.handleSearch(searchTerm);
                suggestions.style.display = 'none';
                searchInput.focus();
            });
        });

        // ESC键隐藏建议
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                suggestions.style.display = 'none';
                searchInput.blur();
            }
        });

        // 点击文档其他地方隐藏建议
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestions.contains(e.target)) {
                suggestions.style.display = 'none';
            }
        });
    }

    // 更新搜索建议
    updateSearchSuggestions() {
        const suggestions = document.getElementById('searchSuggestions');
        if (!suggestions || this.resultFiles.length === 0) return;

        // 统计文件类型
        const fileTypeCount = {};
        this.resultFiles.forEach(file => {
            const extension = file.name.split('.').pop().toLowerCase();
            fileTypeCount[extension] = (fileTypeCount[extension] || 0) + 1;
        });

        // 动态更新搜索标签
        const container = suggestions.querySelector('.mt-1');
        if (container) {
            let tagsHtml = '';
            
            // 按文件数量排序，显示最常见的文件类型
            const sortedTypes = Object.entries(fileTypeCount)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 6); // 最多显示6个
            
            sortedTypes.forEach(([extension, count]) => {
                const badgeClass = this.getFileTypeBadgeClass(extension);
                tagsHtml += `
                    <span class="badge ${badgeClass} me-1 search-tag" 
                          data-search="${extension}" 
                          style="cursor: pointer;" 
                          title="${count} 个 ${extension} 文件">
                        ${extension} (${count})
                    </span>
                `;
            });
            
            container.innerHTML = tagsHtml;
            
            // 重新绑定事件
            container.querySelectorAll('.search-tag').forEach(tag => {
                tag.addEventListener('click', () => {
                    const searchTerm = tag.dataset.search;
                    const searchInput = document.getElementById('fileSearchInput');
                    if (searchInput) {
                        searchInput.value = searchTerm;
                        this.handleSearch(searchTerm);
                        suggestions.style.display = 'none';
                        searchInput.focus();
                    }
                });
            });
        }
    }

    // 获取文件类型对应的badge样式
    getFileTypeBadgeClass(extension) {
        const classMap = {
            'json': 'bg-success',
            'onnx': 'bg-primary', 
            'txt': 'bg-info',
            'log': 'bg-warning',
            'csv': 'bg-secondary',
            'xml': 'bg-danger'
        };
        return classMap[extension] || 'bg-dark';
    }

    // 查看CSV文件
    async viewCsvFile(filePath, fileName) {
        try {
            console.log('开始查看CSV文件:', { filePath, fileName });
            
            if (!this.currentExecutionId) {
                throw new Error('执行ID不存在，请重新执行工具');
            }
            
            showLoading('加载CSV文件内容...');
            
            const response = await apiService.viewOutputFile(this.currentExecutionId, filePath);
            
            if (!response || response.content === undefined) {
                throw new Error('CSV文件内容为空或无效');
            }
            
            // 解析CSV内容
            this.showCsvModal(fileName, response.content);
            
            hideLoading();
            
        } catch (error) {
            hideLoading();
            console.error('查看CSV文件失败:', error);
            showToast('查看CSV文件失败: ' + error.message, 'error');
        }
    }

    // 显示CSV模态框
    showCsvModal(fileName, csvContent) {
        // 解析CSV内容
        const lines = csvContent.trim().split('\n');
        if (lines.length === 0) {
            showToast('CSV文件为空', 'warning');
            return;
        }

        // 解析CSV数据
        const csvData = this.parseCsvContent(csvContent);
        if (!csvData || csvData.length === 0) {
            showToast('无法解析CSV文件内容', 'error');
            return;
        }

        // 重用现有的CSV查看模态框
        const modal = document.getElementById('csvViewModal');
        const modalTitle = document.getElementById('csvModalFileName');
        const modalContent = document.getElementById('csvModalContent');
        const modalTable = document.getElementById('csvModalTable');
        
        if (!modal || !modalTitle || !modalContent || !modalTable) {
            showToast('CSV查看模态框未找到', 'error');
            return;
        }

        // 设置文件名
        modalTitle.textContent = fileName;

        // 更新统计信息
        const totalRows = csvData.length;
        const totalColumns = totalRows > 0 ? Object.keys(csvData[0]).length : 0;
        
        document.getElementById('csvTotalRows').textContent = totalRows;
        document.getElementById('csvTotalColumns').textContent = totalColumns;
        document.getElementById('csvMatchedVars').textContent = '-';
        document.getElementById('csvMissingVars').textContent = '-';

        // 渲染CSV表格
        this.renderCsvResultTable(csvData, modalTable);

        // 显示模态框
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    // 解析CSV内容
    parseCsvContent(csvContent) {
        try {
            const lines = csvContent.trim().split('\n');
            if (lines.length < 2) return [];

            // 解析头部
            const headers = this.parseCsvLine(lines[0]);
            const data = [];

            // 解析数据行
            for (let i = 1; i < lines.length; i++) {
                const values = this.parseCsvLine(lines[i]);
                if (values.length === headers.length) {
                    const row = {};
                    headers.forEach((header, index) => {
                        row[header] = values[index];
                    });
                    data.push(row);
                }
            }

            return data;
        } catch (error) {
            console.error('解析CSV内容失败:', error);
            return [];
        }
    }

    // 解析CSV行（简单的CSV解析器）
    parseCsvLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                if (inQuotes && line[i + 1] === '"') {
                    current += '"';
                    i++; // 跳过下一个引号
                } else {
                    inQuotes = !inQuotes;
                }
            } else if (char === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        
        result.push(current.trim());
        return result;
    }

    // 渲染CSV结果表格
    renderCsvResultTable(csvData, table) {
        if (!csvData || csvData.length === 0) {
            table.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">没有数据</td></tr>';
            return;
        }

        const columns = Object.keys(csvData[0]);
        
        // 创建表格头部
        const thead = `
            <thead class="table-dark sticky-top">
                <tr>
                    <th scope="col" style="width: 60px;">#</th>
                    ${columns.map(col => `<th scope="col">${escapeHtml(col)}</th>`).join('')}
                </tr>
            </thead>
        `;

        // 创建表格主体
        const tbody = `
            <tbody>
                ${csvData.map((row, index) => `
                    <tr class="csv-row" data-row-index="${index}">
                        <th scope="row" class="text-muted">${index + 1}</th>
                        ${columns.map(col => `<td>${escapeHtml(row[col] || '')}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;

        table.innerHTML = thead + tbody;
    }
}

// 创建全局结果管理器实例
window.resultsManager = new ResultsManager();
