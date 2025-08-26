// 配置管理模块
class Config {
    constructor() {
        this.config = {
            // 默认配置
            backend: {
                host: '100.102.198.27',
                port: 5000,
                protocol: 'http'
            },
            frontend: {
                host: '100.102.198.27', 
                port: 8080,
                protocol: 'http'
            }
        };
        
        // 从环境变量或URL参数加载配置
        this.loadConfig();
    }

    loadConfig() {
        try {
            // 1. 尝试从URL参数获取配置
            const urlParams = new URLSearchParams(window.location.search);
            const backendHost = urlParams.get('backend_host');
            const backendPort = urlParams.get('backend_port');
            
            if (backendHost) {
                this.config.backend.host = backendHost;
            }
            if (backendPort) {
                this.config.backend.port = parseInt(backendPort);
            }

            // 2. 尝试从localStorage获取保存的配置
            const savedConfig = localStorage.getItem('ai_tools_config');
            if (savedConfig) {
                const parsed = JSON.parse(savedConfig);
                this.config = { ...this.config, ...parsed };
            }

            // 3. 智能检测：如果当前不是localhost，尝试使用当前主机作为后端
            if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                // 如果前端不在localhost上运行，假设后端也在同一台机器上
                this.config.backend.host = window.location.hostname;
                console.log('自动检测后端地址:', this.config.backend.host);
            }

            // 4. 尝试从环境配置文件获取
            this.loadEnvironmentConfig();

        } catch (error) {
            console.warn('配置加载失败，使用默认配置:', error);
        }
    }

    async loadEnvironmentConfig() {
        try {
            // 尝试加载环境配置文件
            const response = await fetch('/config.json');
            if (response.ok) {
                const envConfig = await response.json();
                if (envConfig.backend) {
                    this.config.backend = { ...this.config.backend, ...envConfig.backend };
                }
                console.log('加载环境配置成功:', envConfig);
            }
        } catch (error) {
            // 配置文件不存在是正常的，不需要报错
            console.debug('未找到环境配置文件，使用默认配置');
        }
    }

    // 获取后端API基础URL
    getApiBaseUrl() {
        const { protocol, host, port } = this.config.backend;
        return `${protocol}://${host}:${port}/api`;
    }

    // 获取WebSocket URL
    getWebSocketUrl() {
        const { protocol, host, port } = this.config.backend;
        const wsProtocol = protocol === 'https' ? 'wss' : 'ws';
        return `${protocol}://${host}:${port}`;
    }

    // 获取文件下载基础URL
    getDownloadBaseUrl() {
        const { protocol, host, port } = this.config.backend;
        return `${protocol}://${host}:${port}/api`;
    }

    // 获取完整配置
    getConfig() {
        return { ...this.config };
    }

    // 更新配置
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.saveConfig();
        console.log('配置已更新:', this.config);
    }

    // 保存配置到localStorage
    saveConfig() {
        try {
            localStorage.setItem('ai_tools_config', JSON.stringify(this.config));
        } catch (error) {
            console.warn('配置保存失败:', error);
        }
    }

    // 重置为默认配置
    resetConfig() {
        this.config = {
            backend: {
                host: '100.102.198.27',
                port: 5000,
                protocol: 'http'
            },
            frontend: {
                host: '100.102.198.27',
                port: 8080,
                protocol: 'http'
            }
        };
        localStorage.removeItem('ai_tools_config');
        console.log('配置已重置为默认值');
    }

    // 测试后端连接
    async testBackendConnection() {
        try {
            const response = await fetch(`${this.getApiBaseUrl()}/health`, {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('后端连接测试成功:', data);
                return { success: true, data };
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('后端连接测试失败:', error);
            return { success: false, error: error.message };
        }
    }

    // 自动发现后端服务
    async discoverBackend() {
        const commonPorts = [5000, 8000, 8080, 3000];
        const currentHost = window.location.hostname;
        
        console.log('开始自动发现后端服务...');
        
        for (const port of commonPorts) {
            try {
                const testConfig = {
                    backend: {
                        host: currentHost,
                        port: port,
                        protocol: window.location.protocol.replace(':', '')
                    }
                };
                
                // 临时设置配置进行测试
                const originalConfig = { ...this.config };
                this.config.backend = testConfig.backend;
                
                const result = await this.testBackendConnection();
                if (result.success) {
                    console.log(`发现后端服务: ${currentHost}:${port}`);
                    this.saveConfig();
                    return true;
                }
                
                // 恢复原配置
                this.config = originalConfig;
            } catch (error) {
                console.debug(`测试 ${currentHost}:${port} 失败:`, error.message);
            }
        }
        
        console.log('未能自动发现后端服务');
        return false;
    }
}

// 创建全局配置实例
window.appConfig = new Config();

// 导出配置类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Config;
}
