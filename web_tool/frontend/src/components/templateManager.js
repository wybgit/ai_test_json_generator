// 模板管理器组件
class TemplateManager {
    constructor() {
        this.templates = [];
        this.currentTemplate = null;
        this.variables = [];
        this.variableValues = {};
        this.useCSV = false;
        this.csvData = [];
        this.init();
    }

    async init() {
        await this.loadTemplates();
        await this.loadCsvFiles();
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

        // 数据模式切换
        const modeRadios = document.querySelectorAll('input[name="dataMode"]');
        modeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.useCSV = e.target.value === 'csv';
                this.toggleDataMode();
            });
        });

        // CSV文件选择
        const csvSelect = document.getElementById('csvSelect');
        if (csvSelect) {
            csvSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadCsvFile(e.target.value);
                } else {
                    this.clearCsvData();
                }
            });
        }

        // CSV文件上传
        const csvUpload = document.getElementById('csvUpload');
        if (csvUpload) {
            csvUpload.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.uploadCsvFile(e.target.files[0]);
                }
            });

            // 设置拖拽上传
            setupFileDrop(csvUpload.parentElement, (file) => {
                if (validateFileType(file, ['csv'])) {
                    this.uploadCsvFile(file);
                } else {
                    showToast('只支持 .csv 文件', 'error');
                }
            });
        }

        // 模板预览按钮
        const templatePreviewBtn = document.getElementById('templatePreviewBtn');
        if (templatePreviewBtn) {
            templatePreviewBtn.addEventListener('click', () => {
                this.showTemplatePreview();
            });
        }

        // 复制预览内容按钮
        const copyPreviewBtn = document.getElementById('copyPreviewBtn');
        if (copyPreviewBtn) {
            copyPreviewBtn.addEventListener('click', () => {
                this.copyPreviewContent();
            });
        }

        // CSV模态框相关事件已移除

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


    }

    async loadTemplate(templateName) {
        try {
            console.log('开始加载模板:', templateName);
            
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
            
            // 显示模板预览按钮
            this.showTemplatePreviewButton();
            
            console.log('模板加载完成');
            showToast(`模板 "${templateName}" 加载成功`, 'success');
            
        } catch (error) {
            console.error('加载模板失败:', error);
            showToast('加载模板失败: ' + error.message, 'error');
        }
    }

    async uploadTemplate(file) {
        try {
            const response = await apiService.uploadTemplate(file);
            
            // 重新加载模板列表
            await this.loadTemplates();
            
            // 选择新上传的模板
            const templateSelect = document.getElementById('templateSelect');
            if (templateSelect) {
                templateSelect.value = response.filename;
                await this.loadTemplate(response.filename);
            }

            showToast('模板上传成功', 'success');
            
        } catch (error) {
            console.error('上传模板失败:', error);
            showToast('上传模板失败: ' + error.message, 'error');
        }
    }

    renderVariables() {
        // 根据数据模式显示不同的变量配置
        if (this.useCSV) {
            this.renderCsvVariables();
            this.hideManualVariables();
        } else {
            this.renderManualVariables();
            this.hideCsvVariables();
        }
    }

    renderManualVariables() {
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
            
            // 检查是否是需要特殊处理的变量
            if (variable === '算子级联信息') {
                return this.renderDropdownVariable(variable, ['Conv', 'Conv+Relu', 'Abs', 'Add', 'BatchNormalization'], value, isEmpty, errorClass);
            } else if (variable === '算子级联结构') {
                return this.renderDropdownVariable(variable, ['串联', '并联'], value, isEmpty, errorClass);
            }
            
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
        container.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('input', (e) => {
                const variable = e.target.dataset.variable;
                this.variableValues[variable] = e.target.value;
                
                // 实时更新验证状态
                this.updateVariableValidation(e.target, variable);
                

            });
            
            input.addEventListener('change', (e) => {
                const variable = e.target.dataset.variable;
                this.variableValues[variable] = e.target.value;
                
                // 实时更新验证状态
                this.updateVariableValidation(e.target, variable);
                

            });
        });

        // 设置下拉菜单特殊事件监听
        container.querySelectorAll('.dropdown-with-custom').forEach(dropdown => {
            this.setupDropdownWithCustomInput(dropdown);
        });
    }



    renderDropdownVariable(variable, options, value, isEmpty, errorClass) {
        const isCustomValue = value && !options.includes(value);
        const selectValue = isCustomValue ? 'custom' : value;
        
        return `
            <div class="variable-input dropdown-with-custom" data-variable="${variable}">
                <label class="variable-label">${variable}</label>
                <div class="input-group">
                    <select class="form-select ${errorClass}" data-variable="${variable}" data-type="select">
                        <option value="">请选择...</option>
                        ${options.map(option => 
                            `<option value="${escapeHtml(option)}" ${selectValue === option ? 'selected' : ''}>${escapeHtml(option)}</option>`
                        ).join('')}
                        <option value="custom" ${isCustomValue ? 'selected' : ''}>自定义输入</option>
                    </select>
                    <input 
                        type="text" 
                        class="form-control custom-input ${isCustomValue ? '' : 'd-none'} ${isCustomValue && isEmpty ? 'is-invalid' : ''}" 
                        data-variable="${variable}"
                        data-type="custom"
                        value="${isCustomValue ? escapeHtml(value) : ''}"
                        placeholder="请输入自定义的${variable}"
                    >
                </div>
                ${isEmpty ? `<div class="invalid-feedback">请填写 ${variable} 的值</div>` : ''}
            </div>
        `;
    }

    setupDropdownWithCustomInput(dropdown) {
        const variable = dropdown.dataset.variable;
        const select = dropdown.querySelector('select');
        const customInput = dropdown.querySelector('.custom-input');
        
        if (!select || !customInput) return;

        select.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                // 显示自定义输入框
                customInput.classList.remove('d-none');
                customInput.focus();
                // 清空select的值，使用自定义输入
                this.variableValues[variable] = customInput.value;
            } else {
                // 隐藏自定义输入框
                customInput.classList.add('d-none');
                customInput.value = '';
                // 使用选中的预设值
                this.variableValues[variable] = e.target.value;
            }
            
            // 更新验证状态
            this.updateVariableValidation(e.target, variable);

        });

        customInput.addEventListener('input', (e) => {
            this.variableValues[variable] = e.target.value;
            this.updateVariableValidation(e.target, variable);

        });
    }

    updateVariableValidation(inputElement, variable) {
        // 获取实际的变量值
        const actualValue = this.variableValues[variable] || '';
        const isEmpty = !actualValue || actualValue.trim() === '';
        
        // 对于下拉菜单组合，需要特殊处理
        const dropdownContainer = inputElement.closest('.dropdown-with-custom');
        if (dropdownContainer) {
            const select = dropdownContainer.querySelector('select');
            const customInput = dropdownContainer.querySelector('.custom-input');
            
            // 更新样式
            if (isEmpty) {
                select.classList.add('is-invalid');
                select.classList.remove('is-valid');
                if (!customInput.classList.contains('d-none')) {
                    customInput.classList.add('is-invalid');
                    customInput.classList.remove('is-valid');
                }
            } else {
                select.classList.remove('is-invalid');
                select.classList.add('is-valid');
                customInput.classList.remove('is-invalid');
                customInput.classList.add('is-valid');
            }
            
            // 更新错误提示
            let errorDiv = dropdownContainer.querySelector('.invalid-feedback');
            if (isEmpty) {
                if (!errorDiv) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    dropdownContainer.appendChild(errorDiv);
                }
                errorDiv.textContent = `请填写 ${variable} 的值`;
                errorDiv.style.display = 'block';
            } else {
                if (errorDiv) {
                    errorDiv.style.display = 'none';
                }
            }
        } else {
            // 普通输入框的处理
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
    }



    onTemplateContentChange() {
        const templateContent = document.getElementById('templateContent');
        if (!templateContent) return;

        const content = templateContent.value;
        
        // 重新提取变量
        this.extractVariablesFromContent(content);
        
        // 重新渲染变量输入框
        this.renderVariables();
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
        
        // 清空CSV相关显示
        this.hideCsvVariables();

        // 隐藏模板预览按钮
        this.hideTemplatePreviewButton();
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

        if (this.useCSV) {
            // CSV模式验证
            if (this.csvData.length === 0) {
                showToast('请选择或上传CSV文件', 'error');
                return false;
            }
            
            // 检查CSV数据是否包含所需的列
            if (this.variables.length > 0 && this.csvData.length > 0) {
                const csvColumns = Object.keys(this.csvData[0]);
                const missingColumns = this.variables.filter(variable => 
                    !csvColumns.includes(variable)
                );
                
                if (missingColumns.length > 0) {
                    showToast(`CSV文件缺少以下列: ${missingColumns.join(', ')}`, 'error');
                    return false;
                }
            }
        } else {
            // 手动模式验证
            const missingVars = this.variables.filter(variable => 
                !this.variableValues[variable] || this.variableValues[variable].trim() === ''
            );

            if (missingVars.length > 0) {
                // 高亮显示缺失的变量输入框
                this.highlightMissingVariables(missingVars);
                showToast(`请填写缺失的变量值`, 'error');
                return false;
            }
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
            template_name: this.currentTemplate ? this.currentTemplate.name : null,
            use_csv: this.useCSV,
            csv_data: this.getCsvData()
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

        if (config.use_csv !== undefined) {
            this.useCSV = config.use_csv;
            
            // 更新UI
            const modeRadio = document.querySelector(`input[name="dataMode"][value="${this.useCSV ? 'csv' : 'manual'}"]`);
            if (modeRadio) {
                modeRadio.checked = true;
            }
            
            this.toggleDataMode();
        }

        if (config.csv_data && config.csv_data.length > 0) {
            this.csvData = config.csv_data;
            const columns = Object.keys(config.csv_data[0]);
            this.renderCsvPreview(config.csv_data, columns);
        }

        this.onTemplateContentChange();
    }

    // 显示模板预览按钮
    showTemplatePreviewButton() {
        const templatePreviewBtn = document.getElementById('templatePreviewBtn');
        if (templatePreviewBtn) {
            templatePreviewBtn.style.display = 'block';
        }
    }

    // 隐藏模板预览按钮
    hideTemplatePreviewButton() {
        const templatePreviewBtn = document.getElementById('templatePreviewBtn');
        if (templatePreviewBtn) {
            templatePreviewBtn.style.display = 'none';
        }
    }

    // 显示模板预览对话框
    async showTemplatePreview() {
        const content = this.getTemplateContent();
        if (!content.trim()) {
            showToast('请先输入模板内容', 'warning');
            return;
        }

        try {
            // 获取预览内容
            const response = await apiService.previewTemplate(content, this.variableValues);
            
            // 显示预览结果
            const previewElement = document.getElementById('previewedTemplateContent');
            if (previewElement) {
                const codeElement = previewElement.querySelector('code');
                if (codeElement) {
                    const highlighted = highlightCode(response.preview, 'text');
                    codeElement.innerHTML = highlighted;
                }
            }
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('templatePreviewModal'));
            modal.show();
            
        } catch (error) {
            console.error('模板预览失败:', error);
            showToast('模板预览失败: ' + error.message, 'error');
        }
    }



    // 复制预览内容
    async copyPreviewContent() {
        const previewElement = document.getElementById('previewedTemplateContent');
        if (previewElement) {
            const codeElement = previewElement.querySelector('code');
            if (codeElement) {
                // 获取纯文本内容（去除HTML标签）
                const textContent = codeElement.textContent || codeElement.innerText;
                await copyToClipboard(textContent);
            }
        }
    }

    // CSV 相关方法
    toggleDataMode() {
        const csvSection = document.getElementById('csvSection');
        if (!csvSection) return;

        if (this.useCSV) {
            csvSection.style.display = 'block';
        } else {
            csvSection.style.display = 'none';
            this.clearCsvData();
        }

        // 重新渲染变量
        this.renderVariables();
    }

    async loadCsvFiles() {
        try {
            const response = await apiService.getCsvFiles();
            const csvFiles = response.csv_files;
            this.renderCsvOptions(csvFiles);
        } catch (error) {
            console.error('加载CSV文件失败:', error);
            showToast('加载CSV文件失败: ' + error.message, 'error');
        }
    }

    renderCsvOptions(csvFiles) {
        const select = document.getElementById('csvSelect');
        if (!select) return;

        // 清空现有选项
        select.innerHTML = '<option value="">选择一个 CSV 文件...</option>';

        // 添加CSV文件选项
        csvFiles.forEach(csvFile => {
            const option = document.createElement('option');
            option.value = csvFile.name;
            option.textContent = csvFile.display_name;
            select.appendChild(option);
        });
    }

    async loadCsvFile(csvFileName) {
        try {
            const response = await apiService.getCsvContent(csvFileName);
            console.log('原始API响应:', response);
            
            // 验证响应
            if (!response || !response.data) {
                console.error('响应验证失败:', {
                    response: response,
                    hasResponse: !!response,
                    hasData: response ? !!response.data : false,
                    dataType: response ? typeof response.data : 'N/A',
                    dataLength: response && response.data ? response.data.length : 'N/A'
                });
                throw new Error('CSV文件内容为空或无效');
            }
            
            // 验证data是数组且非空
            if (!Array.isArray(response.data) || response.data.length === 0) {
                console.error('CSV数据格式错误:', {
                    isArray: Array.isArray(response.data),
                    length: response.data ? response.data.length : 'N/A',
                    data: response.data
                });
                throw new Error('CSV数据格式不正确或为空');
            }
            
            this.csvData = response.data;
            console.log('CSV数据已设置:', {
                data: this.csvData,
                length: this.csvData.length,
                firstRow: this.csvData[0]
            });
            
            // 显示CSV预览
            this.renderCsvPreview(response.data, response.columns);
            
            // 如果有模板变量，显示CSV变量预览
            if (this.variables.length > 0) {
                this.renderCsvVariables();
            }
            
            showToast(`CSV文件 "${csvFileName}" 加载成功`, 'success');
            
        } catch (error) {
            console.error('加载CSV文件失败:', error);
            showToast('加载CSV文件失败: ' + error.message, 'error');
        }
    }

    async uploadCsvFile(file) {
        try {
            const response = await apiService.uploadCsv(file);
            
            // 重新加载CSV文件列表
            await this.loadCsvFiles();
            
            // 选择新上传的CSV文件
            const csvSelect = document.getElementById('csvSelect');
            if (csvSelect) {
                csvSelect.value = response.filename;
                this.csvData = response.data;
                console.log('上传后设置CSV数据:', {
                    data: this.csvData,
                    length: this.csvData.length,
                    firstRow: this.csvData[0]
                });
                this.renderCsvPreview(response.data, response.columns);
                
                // 如果有模板变量，显示CSV变量预览
                if (this.variables.length > 0) {
                    this.renderCsvVariables();
                }
            }
            
            showToast('CSV文件上传成功', 'success');
            
        } catch (error) {
            console.error('上传CSV文件失败:', error);
            showToast('上传CSV文件失败: ' + error.message, 'error');
        }
    }

    renderCsvPreview(data, columns) {
        const previewContainer = document.getElementById('csvPreview');
        const table = document.getElementById('csvTable');
        
        if (!previewContainer || !table || !data || data.length === 0) {
            if (previewContainer) previewContainer.style.display = 'none';
            return;
        }

        // 创建表格头部
        const thead = `
            <thead>
                <tr>
                    <th scope="col">#</th>
                    ${columns.map(col => `<th scope="col">${escapeHtml(col)}</th>`).join('')}
                </tr>
            </thead>
        `;

        // 创建表格主体 (最多显示5行以节省空间)
        const maxRows = Math.min(data.length, 5);
        const tbody = `
            <tbody>
                ${data.slice(0, maxRows).map((row, index) => `
                    <tr>
                        <th scope="row">${index + 1}</th>
                        ${columns.map(col => `<td>${escapeHtml(row[col] || '')}</td>`).join('')}
                    </tr>
                `).join('')}
                ${data.length > maxRows ? `
                    <tr>
                        <td colspan="${columns.length + 1}" class="text-center text-muted">
                            ... 还有 ${data.length - maxRows} 行数据
                        </td>
                    </tr>
                ` : ''}
            </tbody>
        `;

        table.innerHTML = thead + tbody;
        previewContainer.style.display = 'block';
    }

    renderCsvVariables() {
        const container = document.getElementById('csvVariablesList');
        const variablesSection = document.getElementById('csvVariables');
        
        if (!container || !variablesSection || this.csvData.length === 0) {
            if (variablesSection) variablesSection.style.display = 'none';
            return;
        }

        const csvColumns = Object.keys(this.csvData[0]);
        const matchedVars = this.variables.filter(variable => csvColumns.includes(variable));
        const missingVars = this.variables.filter(variable => !csvColumns.includes(variable));

        let content = '';
        
        if (matchedVars.length > 0) {
            content += `
                <div class="mb-3">
                    <h6 class="text-success"><i class="fas fa-check me-1"></i>匹配的变量 (${matchedVars.length})</h6>
                    <div class="row">
                        ${matchedVars.map(variable => `
                            <div class="col-md-6 mb-2">
                                <span class="badge bg-success">${escapeHtml(variable)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (missingVars.length > 0) {
            content += `
                <div class="mb-3">
                    <h6 class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>缺失的变量 (${missingVars.length})</h6>
                    <div class="row">
                        ${missingVars.map(variable => `
                            <div class="col-md-6 mb-2">
                                <span class="badge bg-warning">${escapeHtml(variable)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        content += `
            <div class="mt-3">
                <small class="text-muted">
                    <i class="fas fa-info-circle me-1"></i>
                    将使用 ${this.csvData.length} 行CSV数据生成结果
                </small>
            </div>
        `;

        container.innerHTML = content;
        variablesSection.style.display = 'block';
    }

    hideManualVariables() {
        const variablesSection = document.getElementById('templateVariables');
        if (variablesSection) {
            variablesSection.style.display = 'none';
        }
    }

    hideCsvVariables() {
        const variablesSection = document.getElementById('csvVariables');
        if (variablesSection) {
            variablesSection.style.display = 'none';
        }
    }

    clearCsvData() {
        this.csvData = [];
        
        const previewContainer = document.getElementById('csvPreview');
        if (previewContainer) {
            previewContainer.style.display = 'none';
        }
        
        const csvSelect = document.getElementById('csvSelect');
        if (csvSelect) {
            csvSelect.value = '';
        }

        this.hideCsvVariables();
    }

    getCsvData() {
        return this.useCSV ? [...this.csvData] : [];
    }

    isUsingCSV() {
        return this.useCSV;
    }

    // 显示查看CSV按钮
    showViewCsvButton() {
        console.log('尝试显示查看CSV按钮');
        const viewCsvBtn = document.getElementById('viewCsvBtn');
        if (viewCsvBtn) {
            viewCsvBtn.style.display = 'block';
            console.log('查看CSV按钮已显示');
        } else {
            console.error('找不到查看CSV按钮元素');
        }
    }

    // 隐藏查看CSV按钮
    hideViewCsvButton() {
        const viewCsvBtn = document.getElementById('viewCsvBtn');
        if (viewCsvBtn) {
            viewCsvBtn.style.display = 'none';
        }
    }

    // 设置CSV模态框事件
    setupCsvModalEvents() {
        // CSV搜索事件
        const csvSearchInput = document.getElementById('csvSearchInput');
        if (csvSearchInput) {
            csvSearchInput.addEventListener('input', (e) => {
                this.filterCsvTable(e.target.value);
            });
        }

        // 清空搜索按钮
        const csvSearchClear = document.getElementById('csvSearchClear');
        if (csvSearchClear) {
            csvSearchClear.addEventListener('click', () => {
                const csvSearchInput = document.getElementById('csvSearchInput');
                if (csvSearchInput) {
                    csvSearchInput.value = '';
                    this.filterCsvTable('');
                }
            });
        }

        // 复制CSV数据按钮
        const csvCopyBtn = document.getElementById('csvCopyBtn');
        if (csvCopyBtn) {
            csvCopyBtn.addEventListener('click', () => {
                this.copyCsvData();
            });
        }

        // 导出CSV按钮
        const csvExportBtn = document.getElementById('csvExportBtn');
        if (csvExportBtn) {
            csvExportBtn.addEventListener('click', () => {
                this.exportCsvData();
            });
        }
    }

    // 显示CSV查看模态框
    showCsvViewModal() {
        console.log('=== CSV查看模态框调试 ===');
        console.log('csvData:', this.csvData);
        console.log('csvData类型:', typeof this.csvData);
        console.log('csvData长度:', this.csvData ? this.csvData.length : 'null/undefined');
        console.log('是否为数组:', Array.isArray(this.csvData));
        
        if (!this.csvData || this.csvData.length === 0) {
            console.error('CSV数据检查失败 - csvData为空或长度为0');
            console.log('当前CSV选择:', document.getElementById('csvSelect')?.value);
            showToast('请先选择或上传CSV文件，当前CSV数据为空', 'warning');
            return;
        }
        
        console.log('CSV数据验证通过，开始显示模态框');

        // 设置文件名
        const csvSelect = document.getElementById('csvSelect');
        const fileName = csvSelect ? csvSelect.value || '未命名CSV文件' : '未命名CSV文件';
        const csvModalFileName = document.getElementById('csvModalFileName');
        if (csvModalFileName) {
            csvModalFileName.textContent = fileName;
        }

        // 更新统计信息
        this.updateCsvModalStats();

        // 渲染CSV表格
        this.renderCsvModalTable();

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('csvViewModal'));
        modal.show();
    }

    // 更新CSV模态框统计信息
    updateCsvModalStats() {
        const totalRows = this.csvData.length;
        const totalColumns = totalRows > 0 ? Object.keys(this.csvData[0]).length : 0;
        
        // 计算匹配和缺失的变量
        let matchedVars = 0;
        let missingVars = 0;
        
        if (this.variables.length > 0 && totalRows > 0) {
            const csvColumns = Object.keys(this.csvData[0]);
            matchedVars = this.variables.filter(variable => csvColumns.includes(variable)).length;
            missingVars = this.variables.length - matchedVars;
        }

        // 更新DOM元素
        document.getElementById('csvTotalRows').textContent = totalRows;
        document.getElementById('csvTotalColumns').textContent = totalColumns;
        document.getElementById('csvMatchedVars').textContent = matchedVars;
        document.getElementById('csvMissingVars').textContent = missingVars;
    }

    // 渲染CSV模态框表格
    renderCsvModalTable() {
        const table = document.getElementById('csvModalTable');
        if (!table || this.csvData.length === 0) return;

        const columns = Object.keys(this.csvData[0]);
        
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
                ${this.csvData.map((row, index) => `
                    <tr class="csv-row" data-row-index="${index}">
                        <th scope="row" class="text-muted">${index + 1}</th>
                        ${columns.map(col => `<td>${escapeHtml(row[col] || '')}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;

        table.innerHTML = thead + tbody;
    }

    // 过滤CSV表格
    filterCsvTable(query) {
        const rows = document.querySelectorAll('#csvModalTable tbody .csv-row');
        const lowerQuery = query.toLowerCase();

        let visibleCount = 0;
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (!query || text.includes(lowerQuery)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // 更新显示的行数统计
        const totalRows = document.getElementById('csvTotalRows');
        if (totalRows) {
            if (query) {
                totalRows.textContent = `${visibleCount}/${this.csvData.length}`;
            } else {
                totalRows.textContent = this.csvData.length;
            }
        }
    }

    // 复制CSV数据
    async copyCsvData() {
        if (this.csvData.length === 0) {
            showToast('没有数据可复制', 'warning');
            return;
        }

        try {
            // 转换为CSV格式文本
            const columns = Object.keys(this.csvData[0]);
            const csvText = [
                columns.join(','),
                ...this.csvData.map(row => 
                    columns.map(col => `"${(row[col] || '').toString().replace(/"/g, '""')}"`).join(',')
                )
            ].join('\n');

            await copyToClipboard(csvText);
            showToast('CSV数据已复制到剪贴板', 'success');
        } catch (error) {
            console.error('复制失败:', error);
            showToast('复制失败: ' + error.message, 'error');
        }
    }

    // 导出CSV数据
    exportCsvData() {
        if (this.csvData.length === 0) {
            showToast('没有数据可导出', 'warning');
            return;
        }

        try {
            // 转换为CSV格式文本
            const columns = Object.keys(this.csvData[0]);
            const csvText = [
                columns.join(','),
                ...this.csvData.map(row => 
                    columns.map(col => `"${(row[col] || '').toString().replace(/"/g, '""')}"`).join(',')
                )
            ].join('\n');

            // 创建下载链接
            const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            
            const csvSelect = document.getElementById('csvSelect');
            const fileName = csvSelect ? csvSelect.value || 'exported_data.csv' : 'exported_data.csv';
            
            downloadFile(url, fileName);
            URL.revokeObjectURL(url);
            
            showToast('CSV文件导出成功', 'success');
        } catch (error) {
            console.error('导出失败:', error);
            showToast('导出失败: ' + error.message, 'error');
        }
    }
}

// 创建全局模板管理器实例
window.templateManager = new TemplateManager();

// 添加全局调试函数
window.debugTemplateManager = () => {
    if (window.templateManager) {
        const tm = window.templateManager;
        console.log('=== 模板管理器调试状态 ===');
        console.log('useCSV:', tm.useCSV);
        console.log('csvData:', tm.csvData);
        console.log('csvData type:', typeof tm.csvData);
        console.log('csvData length:', tm.csvData ? tm.csvData.length : 'null/undefined');
        console.log('variables:', tm.variables);
        
        const csvSelect = document.getElementById('csvSelect');
        const viewCsvBtn = document.getElementById('viewCsvBtn');
        const csvSection = document.getElementById('csvSection');
        
        console.log('csvSelect value:', csvSelect ? csvSelect.value : 'element not found');
        console.log('viewCsvBtn display:', viewCsvBtn ? viewCsvBtn.style.display : 'element not found');
        console.log('csvSection display:', csvSection ? csvSection.style.display : 'element not found');
        console.log('==========================');
    } else {
        console.error('模板管理器未初始化');
    }
};

// 添加CSV测试功能
window.testCsvLoad = async (csvFileName = 'cascade_test_points.csv') => {
    if (!window.templateManager) {
        console.error('模板管理器未初始化');
        return;
    }
    
    console.log('=== 开始CSV加载测试 ===');
    try {
        await window.templateManager.loadCsvFile(csvFileName);
        console.log('CSV加载测试完成');
        window.debugTemplateManager();
    } catch (error) {
        console.error('CSV加载测试失败:', error);
    }
};

// 添加直接API测试
window.testCsvApi = async (csvFileName = 'cascade_test_points.csv') => {
    console.log('=== 直接API测试 ===');
    try {
        const response = await window.apiService.getCsvContent(csvFileName);
        console.log('API测试成功:', response);
        return response;
    } catch (error) {
        console.error('API测试失败:', error);
        throw error;
    }
};
