// 模板管理器组件
class TemplateManager {
    constructor() {
        this.templates = [];
        this.currentTemplate = null;
        this.variables = [];
        this.variableValues = {};
        this.init();
    }

    async init() {
        await this.loadTemplates();
        this.setupEventListeners();
    }

    async loadTemplates() {
        try {
            const response = await apiService.getTemplates();
            this.templates = response.templates;
            this.renderTemplateOptions();
        } catch (error) {
            console.error('加载模板失败:', error);
            showToast('加载模板失败: ' + error.message, 'error');
        }
    }

    renderTemplateOptions() {
        const select = document.getElementById('templateSelect');
        if (!select) return;

        // 清空现有选项
        select.innerHTML = '<option value="">选择一个模板...</option>';

        // 添加模板选项
        this.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.name;
            option.textContent = template.display_name;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
        // 模板选择
        const templateSelect = document.getElementById('templateSelect');
        if (templateSelect) {
            templateSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadTemplate(e.target.value);
                } else {
                    this.clearTemplate();
                }
            });
        }

        // 模板上传
        const templateUpload = document.getElementById('templateUpload');
        if (templateUpload) {
            templateUpload.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.uploadTemplate(e.target.files[0]);
                }
            });

            // 设置拖拽上传
            setupFileDrop(templateUpload.parentElement, (file) => {
                if (validateFileType(file, ['txt'])) {
                    this.uploadTemplate(file);
                } else {
                    showToast('只支持 .txt 文件', 'error');
                }
            });
        }

        // 模板内容变化
        const templateContent = document.getElementById('templateContent');
        if (templateContent) {
            templateContent.addEventListener('input', debounce(() => {
                this.onTemplateContentChange();
            }, 500));
        }

        // 预览按钮
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => {
                this.updatePreview();
            });
        }
    }

    async loadTemplate(templateName) {
        let loadingShown = false;
        try {
            console.log('开始加载模板:', templateName);
            showLoading('加载模板中...');
            loadingShown = true;
            
            const response = await apiService.getTemplateContent(templateName);
            console.log('API响应成功，内容长度:', response?.content?.length || 0);
            
            // 验证响应
            if (!response || !response.content) {
                throw new Error('模板内容为空或无效');
            }
            
            this.currentTemplate = response;
            
            // 显示模板内容
            const contentTextarea = document.getElementById('templateContent');
            if (contentTextarea) {
                contentTextarea.value = response.content;
            }

            // 提取并显示变量
            this.variables = response.variables || [];
            this.renderVariables();
            
            // 确保隐藏loading
            console.log('模板加载完成，隐藏loading');
            hideLoading();
            loadingShown = false;
            
            showToast(`模板 "${templateName}" 加载成功`, 'success');
            
            // 最后更新预览（异步，避免阻塞）
            setTimeout(() => {
                this.updatePreview();
            }, 100);
            
        } catch (error) {
            console.error('加载模板失败:', error);
            showToast('加载模板失败: ' + error.message, 'error');
        } finally {
            // 最终保障：确保loading被隐藏
            if (loadingShown) {
                console.log('在finally中隐藏loading');
                hideLoading();
            }
        }
    }

    async uploadTemplate(file) {
        let loadingShown = false;
        try {
            showLoading('上传模板中...');
            loadingShown = true;
            
            const response = await apiService.uploadTemplate(file);
            
            // 重新加载模板列表
            await this.loadTemplates();
            
            // 选择新上传的模板
            const templateSelect = document.getElementById('templateSelect');
            if (templateSelect) {
                templateSelect.value = response.filename;
                await this.loadTemplate(response.filename);
            }

            hideLoading();
            loadingShown = false;
            showToast('模板上传成功', 'success');
            
        } catch (error) {
            console.error('上传模板失败:', error);
            showToast('上传模板失败: ' + error.message, 'error');
        } finally {
            // 最终保障：确保loading被隐藏
            if (loadingShown) {
                hideLoading();
            }
        }
    }

    renderVariables() {
        const container = document.getElementById('variablesList');
        const variablesSection = document.getElementById('templateVariables');
        
        if (!container || !variablesSection) return;

        if (this.variables.length === 0) {
            variablesSection.style.display = 'none';
            return;
        }

        variablesSection.style.display = 'block';

        const variableInputs = this.variables.map(variable => {
            const value = this.variableValues[variable] || '';
            const isEmpty = !value || value.trim() === '';
            const errorClass = isEmpty ? 'is-invalid' : '';
            
            return `
                <div class="variable-input">
                    <label class="variable-label">${variable}</label>
                    <input 
                        type="text" 
                        class="form-control ${errorClass}" 
                        data-variable="${variable}"
                        value="${escapeHtml(value)}"
                        placeholder="请输入 ${variable} 的值"
                    >
                    ${isEmpty ? `<div class="invalid-feedback">请填写 ${variable} 的值</div>` : ''}
                </div>
            `;
        }).join('');

        container.innerHTML = variableInputs;

        // 设置变量输入事件监听
        container.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', (e) => {
                const variable = e.target.dataset.variable;
                this.variableValues[variable] = e.target.value;
                
                // 实时更新验证状态
                this.updateVariableValidation(e.target, variable);
                
                // 自动更新预览（防抖）
                this.debouncedUpdatePreview();
            });
        });
    }

    // 防抖的预览更新
    debouncedUpdatePreview = debounce(() => {
        this.updatePreview();
    }, 1000);

    updateVariableValidation(inputElement, variable) {
        const value = inputElement.value.trim();
        const isEmpty = !value;
        
        // 更新输入框样式
        if (isEmpty) {
            inputElement.classList.add('is-invalid');
            inputElement.classList.remove('is-valid');
        } else {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
        }
        
        // 更新错误提示
        const parentDiv = inputElement.parentElement;
        let errorDiv = parentDiv.querySelector('.invalid-feedback');
        
        if (isEmpty) {
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                parentDiv.appendChild(errorDiv);
            }
            errorDiv.textContent = `请填写 ${variable} 的值`;
        } else {
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }

    async updatePreview() {
        console.log('开始更新预览');
        const templateContent = document.getElementById('templateContent');
        const previewElement = document.getElementById('templatePreview');
        
        if (!templateContent || !previewElement) {
            console.log('预览元素未找到');
            return;
        }

        const content = templateContent.value.trim();
        if (!content) {
            previewElement.innerHTML = '<code>请输入模板内容...</code>';
            console.log('模板内容为空，显示默认提示');
            return;
        }

        try {
            console.log('调用预览API');
            const response = await apiService.previewTemplate(content, this.variableValues);
            console.log('预览API响应:', response);
            
            // 显示预览内容
            const highlighted = highlightCode(response.preview, 'text');
            previewElement.innerHTML = `<code>${highlighted}</code>`;
            console.log('预览内容更新完成');

            // 显示验证信息（现在在输入框下方显示，不需要全局提示）
            // if (!response.validation.is_valid) {
            //     const missingVars = response.validation.missing_variables;
            //     if (missingVars.length > 0) {
            //         showToast(`缺少变量值: ${missingVars.join(', ')}`, 'warning');
            //     }
            // }
            
        } catch (error) {
            console.error('预览失败:', error);
            previewElement.innerHTML = `<code class="text-danger">预览错误: ${escapeHtml(error.message)}</code>`;
            // 不要让预览错误影响模板加载
            console.log('预览失败，但不影响模板加载');
        }
    }

    onTemplateContentChange() {
        const templateContent = document.getElementById('templateContent');
        if (!templateContent) return;

        const content = templateContent.value;
        
        // 重新提取变量
        this.extractVariablesFromContent(content);
        
        // 重新渲染变量输入框
        this.renderVariables();
        
        // 更新预览
        this.updatePreview();
    }

    extractVariablesFromContent(content) {
        // 简单的Jinja2变量提取
        const variableRegex = /\{\{\s*([^}]+)\s*\}\}/g;
        const variables = new Set();
        let match;
        
        while ((match = variableRegex.exec(content)) !== null) {
            const variable = match[1].trim();
            // 排除一些常见的Jinja2语法
            if (!variable.includes('|') && !variable.includes('(') && !variable.includes('[')) {
                variables.add(variable);
            }
        }
        
        this.variables = Array.from(variables);
    }

    clearTemplate() {
        this.currentTemplate = null;
        this.variables = [];
        this.variableValues = {};
        
        // 清空界面
        const templateContent = document.getElementById('templateContent');
        if (templateContent) {
            templateContent.value = '';
        }
        
        const variablesSection = document.getElementById('templateVariables');
        if (variablesSection) {
            variablesSection.style.display = 'none';
        }
        
        const previewElement = document.getElementById('templatePreview');
        if (previewElement) {
            previewElement.innerHTML = '<code>预览内容将在这里显示...</code>';
        }
    }

    getTemplateContent() {
        const templateContent = document.getElementById('templateContent');
        return templateContent ? templateContent.value : '';
    }

    getVariableValues() {
        return { ...this.variableValues };
    }

    validateTemplate() {
        const content = this.getTemplateContent();
        if (!content.trim()) {
            showToast('请输入模板内容', 'error');
            return false;
        }

        // 检查是否所有变量都有值，并高亮显示缺失的变量
        const missingVars = this.variables.filter(variable => 
            !this.variableValues[variable] || this.variableValues[variable].trim() === ''
        );

        if (missingVars.length > 0) {
            // 高亮显示缺失的变量输入框
            this.highlightMissingVariables(missingVars);
            showToast(`请填写缺失的变量值`, 'error');
            return false;
        }

        return true;
    }

    highlightMissingVariables(missingVars) {
        const container = document.getElementById('variablesList');
        if (!container) return;

        // 重置所有输入框样式
        container.querySelectorAll('input').forEach(input => {
            const variable = input.dataset.variable;
            this.updateVariableValidation(input, variable);
        });

        // 滚动到第一个缺失的变量
        if (missingVars.length > 0) {
            const firstMissingInput = container.querySelector(`input[data-variable="${missingVars[0]}"]`);
            if (firstMissingInput) {
                firstMissingInput.focus();
                firstMissingInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }

    // 重新加载模板列表
    async refresh() {
        await this.loadTemplates();
    }

    // 导出配置
    exportConfig() {
        return {
            template_content: this.getTemplateContent(),
            variable_values: this.getVariableValues(),
            template_name: this.currentTemplate ? this.currentTemplate.name : null
        };
    }

    // 导入配置
    importConfig(config) {
        if (config.template_content) {
            const templateContent = document.getElementById('templateContent');
            if (templateContent) {
                templateContent.value = config.template_content;
            }
        }

        if (config.variable_values) {
            this.variableValues = { ...config.variable_values };
        }

        this.onTemplateContentChange();
    }
}

// 创建全局模板管理器实例
window.templateManager = new TemplateManager();
