// CSV管理器组件
class CsvManager {
    constructor() {
        this.csvFiles = [];
        this.currentCsvData = [];
        this.useCSV = false;
        this.init();
    }

    async init() {
        await this.loadCsvFiles();
        this.setupEventListeners();
    }

    async loadCsvFiles() {
        try {
            const response = await apiService.getCsvFiles();
            this.csvFiles = response.csv_files;
            this.renderCsvOptions();
        } catch (error) {
            console.error('加载CSV文件失败:', error);
            showToast('加载CSV文件失败: ' + error.message, 'error');
        }
    }

    renderCsvOptions() {
        const select = document.getElementById('csvSelect');
        if (!select) return;

        // 清空现有选项
        select.innerHTML = '<option value="">选择一个 CSV 文件...</option>';

        // 添加CSV文件选项
        this.csvFiles.forEach(csvFile => {
            const option = document.createElement('option');
            option.value = csvFile.name;
            option.textContent = csvFile.display_name;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
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
    }

    toggleDataMode() {
        const csvSection = document.getElementById('csvSection');
        if (!csvSection) return;

        if (this.useCSV) {
            csvSection.style.display = 'block';
        } else {
            csvSection.style.display = 'none';
            this.clearCsvData();
        }

        // 触发数据模式变化事件
        const event = new CustomEvent('dataModeChanged', {
            detail: { useCSV: this.useCSV }
        });
        document.dispatchEvent(event);
    }

    async loadCsvFile(csvFileName) {
        try {
            showLoading('加载CSV文件中...');
            
            const response = await apiService.getCsvContent(csvFileName);
            this.currentCsvData = response.data;
            
            // 显示CSV预览
            this.renderCsvPreview(response.data, response.columns);
            
            hideLoading();
            showToast(`CSV文件 "${csvFileName}" 加载成功`, 'success');
            
        } catch (error) {
            hideLoading();
            console.error('加载CSV文件失败:', error);
            showToast('加载CSV文件失败: ' + error.message, 'error');
        }
    }

    async uploadCsvFile(file) {
        try {
            showLoading('上传CSV文件中...');
            
            const response = await apiService.uploadCsv(file);
            
            // 重新加载CSV文件列表
            await this.loadCsvFiles();
            
            // 选择新上传的CSV文件
            const csvSelect = document.getElementById('csvSelect');
            if (csvSelect) {
                csvSelect.value = response.filename;
                this.currentCsvData = response.data;
                this.renderCsvPreview(response.data, response.columns);
            }
            
            hideLoading();
            showToast('CSV文件上传成功', 'success');
            
        } catch (error) {
            hideLoading();
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

        // 创建表格主体 (最多显示10行)
        const maxRows = Math.min(data.length, 10);
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

    clearCsvData() {
        this.currentCsvData = [];
        
        const previewContainer = document.getElementById('csvPreview');
        if (previewContainer) {
            previewContainer.style.display = 'none';
        }
        
        const csvSelect = document.getElementById('csvSelect');
        if (csvSelect) {
            csvSelect.value = '';
        }
    }

    getCsvData() {
        return this.useCSV ? [...this.currentCsvData] : [];
    }

    isUsingCSV() {
        return this.useCSV;
    }

    validateData() {
        if (this.useCSV) {
            if (this.currentCsvData.length === 0) {
                throw new Error('请选择或上传CSV文件');
            }
            
            // 检查CSV数据是否包含所需的列
            const templateVars = window.templateManager?.variables || [];
            if (templateVars.length > 0 && this.currentCsvData.length > 0) {
                const csvColumns = Object.keys(this.currentCsvData[0]);
                const missingColumns = templateVars.filter(variable => 
                    !csvColumns.includes(variable)
                );
                
                if (missingColumns.length > 0) {
                    throw new Error(`CSV文件缺少以下列: ${missingColumns.join(', ')}`);
                }
            }
        }
        return true;
    }

    // 从CSV数据创建变量映射
    createVariableMappings() {
        if (!this.useCSV || this.currentCsvData.length === 0) {
            return [];
        }

        return this.currentCsvData.map((row, index) => ({
            index: index + 1,
            variables: { ...row }
        }));
    }

    // 获取CSV列名
    getColumns() {
        if (this.currentCsvData.length === 0) return [];
        return Object.keys(this.currentCsvData[0]);
    }

    // 重新加载CSV文件列表
    async refresh() {
        await this.loadCsvFiles();
    }

    // 导出配置
    exportConfig() {
        return {
            use_csv: this.useCSV,
            csv_data: this.getCsvData(),
            csv_file_name: this.getCurrentCsvFileName()
        };
    }

    getCurrentCsvFileName() {
        const csvSelect = document.getElementById('csvSelect');
        return csvSelect ? csvSelect.value : null;
    }

    // 导入配置
    importConfig(config) {
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
            this.currentCsvData = config.csv_data;
            const columns = Object.keys(config.csv_data[0]);
            this.renderCsvPreview(config.csv_data, columns);
        }

        if (config.csv_file_name) {
            const csvSelect = document.getElementById('csvSelect');
            if (csvSelect) {
                csvSelect.value = config.csv_file_name;
            }
        }
    }

    // 解析本地CSV文件
    async parseLocalCsvFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const text = e.target.result;
                    const data = parseCSV(text);
                    resolve(data);
                } catch (error) {
                    reject(new Error('CSV文件解析失败: ' + error.message));
                }
            };
            
            reader.onerror = () => {
                reject(new Error('文件读取失败'));
            };
            
            reader.readAsText(file, 'utf-8');
        });
    }
}

// 创建全局CSV管理器实例
window.csvManager = new CsvManager();
