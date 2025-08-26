// 工具选择器组件
class ToolSelector {
    constructor() {
        this.selectedTool = null;
        this.tools = [];
        this.init();
    }

    async init() {
        await this.loadTools();
        this.render();
        this.setupEventListeners();
    }

    async loadTools() {
        try {
            const response = await apiService.getTools();
            this.tools = response.tools;
        } catch (error) {
            console.error('加载工具失败:', error);
            showToast('加载工具失败: ' + error.message, 'error');
            this.tools = [];
        }
    }

    render() {
        const container = document.getElementById('toolSelector');
        if (!container) return;

        if (this.tools.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning text-center" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        暂无可用工具
                    </div>
                </div>
            `;
            return;
        }

        const toolCards = this.tools.map(tool => `
            <div class="col-lg-4 col-md-6">
                <div class="card tool-card h-100" data-tool="${tool.name}">
                    <div class="card-body text-center">
                        <div class="tool-icon">
                            <i class="fas fa-${this.getToolIcon(tool.name)}"></i>
                        </div>
                        <h5 class="card-title">${tool.display_name}</h5>
                        <p class="card-text text-muted">${tool.description}</p>
                        <div class="row text-start">
                            <div class="col-6">
                                <small class="text-muted">
                                    <i class="fas fa-file-code me-1"></i>
                                    模板支持: ${tool.templates_supported ? '是' : '否'}
                                </small>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">
                                    <i class="fas fa-table me-1"></i>
                                    CSV支持: ${tool.csv_supported ? '是' : '否'}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = toolCards;
    }

    getToolIcon(toolName) {
        const icons = {
            'ai_json_generator': 'brain',
            'data_processor': 'database',
            'model_converter': 'exchange-alt',
            'default': 'cog'
        };
        return icons[toolName] || icons.default;
    }

    setupEventListeners() {
        const container = document.getElementById('toolSelector');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const toolCard = e.target.closest('.tool-card');
            if (toolCard) {
                this.selectTool(toolCard.dataset.tool);
            }
        });

        // 折叠/展开按钮事件
        const toggleBtn = document.getElementById('toggleToolSelector');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleToolSelector();
            });
        }
    }

    selectTool(toolName) {
        // 清除之前的选择
        document.querySelectorAll('.tool-card').forEach(card => {
            card.classList.remove('selected');
        });

        // 选择新工具
        const selectedCard = document.querySelector(`[data-tool="${toolName}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
            this.selectedTool = this.tools.find(tool => tool.name === toolName);
            
            // 显示工具详细信息并折叠选择器
            this.showToolDetails();
            this.collapseToolSelector();
            
            // 显示工具配置区域
            this.showToolConfig();
            
            // 触发工具选择事件
            this.onToolSelected(this.selectedTool);
        }
    }

    showToolConfig() {
        const configSection = document.getElementById('toolConfigSection');
        if (configSection) {
            configSection.style.display = 'block';
            
            // 移除自动滚动，避免页面跳转
            // setTimeout(() => {
            //     scrollToElement(configSection, 100);
            // }, 100);
        }
    }

    hideToolConfig() {
        const configSection = document.getElementById('toolConfigSection');
        if (configSection) {
            configSection.style.display = 'none';
        }
    }

    onToolSelected(tool) {
        // 触发自定义事件
        const event = new CustomEvent('toolSelected', {
            detail: tool
        });
        document.dispatchEvent(event);

        // 显示成功消息
        showToast(`已选择工具: ${tool.display_name}`, 'success');
    }

    getSelectedTool() {
        return this.selectedTool;
    }

    // 重新加载工具列表
    async refresh() {
        await this.loadTools();
        this.render();
        this.selectedTool = null;
        this.hideToolConfig();
    }

    // 显示工具详细信息
    showToolDetails() {
        if (!this.selectedTool) return;

        const selectedToolInfo = document.getElementById('selectedToolInfo');
        const selectedToolIcon = document.getElementById('selectedToolIcon');
        const selectedToolName = document.getElementById('selectedToolName');
        const selectedToolDescription = document.getElementById('selectedToolDescription');
        const selectedToolFormats = document.getElementById('selectedToolFormats');
        const selectedToolType = document.getElementById('selectedToolType');

        if (selectedToolInfo) {
            // 更新工具详细信息
            if (selectedToolIcon) {
                selectedToolIcon.innerHTML = `<i class="fas fa-${this.getToolIcon(this.selectedTool.name)} fa-3x text-primary"></i>`;
            }
            if (selectedToolName) {
                selectedToolName.textContent = this.selectedTool.display_name;
            }
            if (selectedToolDescription) {
                selectedToolDescription.textContent = this.selectedTool.description;
            }
            if (selectedToolFormats) {
                const formats = this.selectedTool.supported_formats || ['未知'];
                selectedToolFormats.innerHTML = formats.map(format => `<span class="badge bg-secondary me-1">${format}</span>`).join('');
            }
            if (selectedToolType) {
                selectedToolType.innerHTML = `<span class="badge bg-info">${this.selectedTool.execution_type || '标准'}</span>`;
            }

            selectedToolInfo.style.display = 'block';
        }
    }

    // 折叠工具选择器
    collapseToolSelector() {
        const toolSelectorBody = document.getElementById('toolSelectorBody');
        const toggleBtn = document.getElementById('toggleToolSelector');
        const toggleIcon = toggleBtn?.querySelector('i');
        const toggleText = toggleBtn?.querySelector('.toggle-text');

        if (toolSelectorBody) {
            toolSelectorBody.style.display = 'none';
        }
        if (toggleBtn) {
            toggleBtn.style.display = 'inline-block';
        }
        if (toggleIcon) {
            toggleIcon.className = 'fas fa-chevron-down me-1';
        }
        if (toggleText) {
            toggleText.textContent = '展开';
        }
    }

    // 展开工具选择器
    expandToolSelector() {
        const toolSelectorBody = document.getElementById('toolSelectorBody');
        const selectedToolInfo = document.getElementById('selectedToolInfo');
        const toggleIcon = document.querySelector('#toggleToolSelector i');
        const toggleText = document.querySelector('#toggleToolSelector .toggle-text');

        if (toolSelectorBody) {
            toolSelectorBody.style.display = 'block';
        }
        if (selectedToolInfo) {
            selectedToolInfo.style.display = 'none';
        }
        if (toggleIcon) {
            toggleIcon.className = 'fas fa-chevron-up me-1';
        }
        if (toggleText) {
            toggleText.textContent = '收起';
        }
    }

    // 切换工具选择器显示状态
    toggleToolSelector() {
        const toolSelectorBody = document.getElementById('toolSelectorBody');
        const isCollapsed = toolSelectorBody && toolSelectorBody.style.display === 'none';

        if (isCollapsed) {
            this.expandToolSelector();
        } else {
            this.collapseToolSelector();
        }
    }
}

// 创建全局工具选择器实例
window.toolSelector = new ToolSelector();
