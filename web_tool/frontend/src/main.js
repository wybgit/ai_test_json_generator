// 主应用入口
class AIToolsApp {
    constructor() {
        this.isInitialized = false;
        this.init();
    }

    async init() {
        try {
            console.log('初始化 AI Tools Web 应用...');
            
            // 显示加载状态
            this.showInitialLoading();
            
            // 检查后端连接
            await this.checkBackendConnection();
            
            // 初始化WebSocket连接
            this.initWebSocket();
            
            // 等待组件初始化
            await this.waitForComponents();
            
            // 设置全局事件监听器
            this.setupGlobalEventListeners();
            
            // 应用初始化完成
            this.hideInitialLoading();
            this.isInitialized = true;
            
            console.log('应用初始化完成');
            showToast('应用初始化完成', 'success');
            
        } catch (error) {
            console.error('应用初始化失败:', error);
            this.showInitializationError(error);
        }
    }

    showInitialLoading() {
        // 可以在这里显示全屏加载动画
        console.log('显示初始加载状态...');
    }

    hideInitialLoading() {
        // 隐藏初始加载动画
        console.log('隐藏初始加载状态');
    }

    async checkBackendConnection() {
        try {
            console.log('检查后端连接...');
            const response = await apiService.healthCheck();
            console.log('后端连接正常:', response);
        } catch (error) {
            throw new Error('无法连接到后端服务，请确保后端服务正在运行');
        }
    }

    initWebSocket() {
        console.log('初始化WebSocket连接...');
        wsService.connect();
        
        // WebSocket连接事件
        wsService.on('connect', () => {
            console.log('WebSocket连接成功');
        });

        wsService.on('disconnect', () => {
            console.log('WebSocket连接断开');
            showToast('与服务器的连接已断开', 'warning');
        });
    }

    async waitForComponents() {
        // 等待核心组件初始化完成（不包括historyManager，它会延迟加载）
        const coreComponents = [
            'toolSelector',
            'templateManager', 
            'executionManager',
            'resultsManager'
        ];

        for (const componentName of coreComponents) {
            while (!window[componentName]) {
                await this.sleep(100);
            }
        }
        
        console.log('核心组件初始化完成');
        
        // historyManager会在后台延迟初始化，不阻塞应用启动
        setTimeout(() => {
            if (window.historyManager) {
                console.log('历史管理器已在后台加载完成');
            }
        }, 2000);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    setupGlobalEventListeners() {
        // 页面卸载时清理资源
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // 工具选择事件
        document.addEventListener('toolSelected', (e) => {
            console.log('工具已选择:', e.detail);
        });

        // 数据模式变化事件
        document.addEventListener('dataModeChanged', (e) => {
            console.log('数据模式已变化:', e.detail);
        });

        // 全局错误处理
        window.addEventListener('error', (e) => {
            console.error('全局错误:', e.error);
            showToast('发生错误: ' + e.error.message, 'error');
        });

        // 未处理的Promise错误
        window.addEventListener('unhandledrejection', (e) => {
            console.error('未处理的Promise错误:', e.reason);
            showToast('发生错误: ' + e.reason, 'error');
        });
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter: 执行工具
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (window.executionManager && !window.executionManager.isCurrentlyExecuting()) {
                window.executionManager.executeToolAsync();
            }
        }

        // Ctrl/Cmd + L: 清空日志
        if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
            e.preventDefault();
            if (window.executionManager) {
                window.executionManager.clearLog();
            }
        }

        // Escape: 停止执行
        if (e.key === 'Escape') {
            if (window.executionManager && window.executionManager.isCurrentlyExecuting()) {
                window.executionManager.stopExecution();
            }
        }
    }

    showInitializationError(error) {
        // 显示初始化错误页面
        document.body.innerHTML = `
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card border-danger">
                            <div class="card-header bg-danger text-white">
                                <h5 class="card-title mb-0">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    应用初始化失败
                                </h5>
                            </div>
                            <div class="card-body">
                                <p class="card-text">${escapeHtml(error.message)}</p>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-primary" onclick="location.reload()">
                                        <i class="fas fa-sync-alt me-2"></i>
                                        重新加载
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    cleanup() {
        console.log('清理应用资源...');
        
        // 断开WebSocket连接
        if (wsService) {
            wsService.disconnect();
        }

        // 停止正在执行的任务
        if (window.executionManager && window.executionManager.isCurrentlyExecuting()) {
            window.executionManager.stopExecution();
        }
    }

    // 导出应用配置
    exportConfig() {
        const config = {
            version: '1.0',
            timestamp: new Date().toISOString(),
            tool: window.toolSelector?.getSelectedTool(),
            template: window.templateManager?.exportConfig(),
            execution: {
                execution_id: window.executionManager?.getCurrentExecutionId()
            }
        };

        return config;
    }

    // 导入应用配置
    importConfig(config) {
        try {
            if (config.tool) {
                window.toolSelector?.selectTool(config.tool.name);
            }

            if (config.template) {
                window.templateManager?.importConfig(config.template);
            }

            showToast('配置导入成功', 'success');
        } catch (error) {
            console.error('导入配置失败:', error);
            showToast('导入配置失败: ' + error.message, 'error');
        }
    }

    // 重置应用
    reset() {
        if (window.executionManager?.isCurrentlyExecuting()) {
            showToast('请先停止当前执行的任务', 'warning');
            return;
        }

        // 重置所有组件
        window.toolSelector?.refresh();
        window.templateManager?.refresh();
        window.executionManager?.reset();
        window.resultsManager?.clear();

        showToast('应用已重置', 'success');
    }

    // 获取应用状态
    getStatus() {
        return {
            initialized: this.isInitialized,
            websocket_connected: wsService?.isConnected || false,
            selected_tool: window.toolSelector?.getSelectedTool()?.name,
            executing: window.executionManager?.isCurrentlyExecuting() || false,
            current_execution: window.executionManager?.getCurrentExecutionId()
        };
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM加载完成，初始化应用...');
    window.app = new AIToolsApp();
});

// 开发环境下的调试工具
if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    window.debug = {
        app: () => window.app,
        status: () => window.app?.getStatus(),
        export: () => window.app?.exportConfig(),
        import: (config) => window.app?.importConfig(config),
        reset: () => window.app?.reset(),
        components: {
            toolSelector: () => window.toolSelector,
            templateManager: () => window.templateManager,
            executionManager: () => window.executionManager,
            resultsManager: () => window.resultsManager,
            historyManager: () => window.historyManager
        },
        services: {
            api: () => window.apiService,
            ws: () => window.wsService
        }
    };
    
    console.log('调试工具已加载，使用 window.debug 访问');
}
