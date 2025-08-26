// API服务模块
class APIService {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const timeout = options.timeout || 30000; // 默认30秒超时
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            console.log('发起API请求:', { url, config, timeout });
            
            // 创建超时Promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('请求超时')), timeout);
            });
            
            // 发起请求
            const fetchPromise = fetch(url, config);
            
            // 竞速执行，任何一个先完成就返回结果
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            console.log('API响应状态:', response.status, response.statusText);
            
            // 处理不同的响应状态
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (jsonError) {
                    // 如果无法解析JSON，使用状态文本
                    console.warn('无法解析错误响应JSON:', jsonError);
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            console.log('API响应数据:', data);
            
            // 验证响应数据
            if (data === null || data === undefined) {
                throw new Error('响应数据为空');
            }
            
            return data;
            
        } catch (error) {
            console.error('API请求错误:', {
                url,
                error: error.message,
                stack: error.stack
            });
            
            // 改进错误消息
            if (error.message === '请求超时') {
                throw new Error('请求超时，请稍后重试');
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('网络连接失败，请检查服务器是否运行');
            } else if (error.message.includes('NetworkError')) {
                throw new Error('网络错误，请检查网络连接');
            }
            
            throw error;
        }
    }

    // GET请求
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST请求
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // 文件上传
    async uploadFile(endpoint, file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '文件上传失败');
        }
        
        return data;
    }

    // 健康检查
    async healthCheck() {
        return this.get('/health');
    }

    // 获取工具列表
    async getTools() {
        return this.get('/tools');
    }

    // 获取模板列表
    async getTemplates() {
        return this.get('/templates');
    }

    // 获取模板内容
    async getTemplateContent(templateName) {
        return this.get(`/templates/${templateName}`);
    }

    // 获取CSV文件列表
    async getCsvFiles() {
        return this.get('/csv-files');
    }

    // 获取CSV文件内容
    async getCsvContent(csvName) {
        console.log('请求CSV内容:', csvName);
        const result = await this.get(`/csv-files/${csvName}`);
        console.log('CSV内容响应:', result);
        return result;
    }

    // 上传模板
    async uploadTemplate(file) {
        return this.uploadFile('/upload/template', file);
    }

    // 上传CSV
    async uploadCsv(file) {
        return this.uploadFile('/upload/csv', file);
    }

    // 模板预览
    async previewTemplate(templateContent, variables) {
        return this.post('/template/preview', {
            template_content: templateContent,
            variables: variables
        });
    }

    // 执行工具
    async executeTool(toolName, params) {
        return this.post(`/tools/${toolName}/execute`, params);
    }

    // 获取执行结果
    async getExecutionOutputs(executionId) {
        return this.get(`/outputs/${executionId}`);
    }

    // 查看输出文件
    async viewOutputFile(executionId, filePath) {
        return this.get(`/outputs/${executionId}/${filePath}`);
    }

    // 下载文件URL
    getDownloadUrl(filePath) {
        return `${this.baseURL}/download/${filePath}`;
    }

    // 下载执行结果ZIP
    getDownloadZipUrl(executionId) {
        return `${this.baseURL}/download-zip/${executionId}`;
    }

    // 清理旧文件
    async cleanup() {
        return this.post('/cleanup', {});
    }
}

// 创建全局API实例
window.apiService = new APIService();
