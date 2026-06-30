// ===== Global State =====
let currentPage = 1;
let totalPages = 1;
let pageSize = 50;
let selectedFile = null;
let searchKeyword = '';

// ===== API Configuration =====
const API_BASE_URL = window.location.origin;

// ===== Utility Functions =====
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');

    // Set message
    toastMessage.textContent = message;

    // Set type
    toast.className = `toast ${type}`;
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };
    toastIcon.textContent = icons[type] || icons.info;

    // Show toast
    setTimeout(() => toast.classList.add('show'), 10);

    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ===== Modal Functions =====
function showImportModal() {
    const modal = document.getElementById('importModal');
    modal.classList.add('active');
}

function closeImportModal() {
    const modal = document.getElementById('importModal');
    modal.classList.remove('active');

    // Reset state
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('importBtn').disabled = true;
    document.getElementById('validateBtn').disabled = true;
    document.getElementById('importStatus').className = 'import-status';
    document.getElementById('importStatus').innerHTML = '';
}

// ===== File Upload Functions =====
function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // File selection
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
        showToast('不支持的文件格式，请上传 Excel 或 CSV 文件', 'error');
        return;
    }

    selectedFile = file;
    document.getElementById('importBtn').disabled = false;
    document.getElementById('validateBtn').disabled = false;

    // Update upload area text
    const uploadText = document.querySelector('.upload-text');
    uploadText.textContent = `已选择: ${file.name}`;

    // Reset validation status
    const importStatus = document.getElementById('importStatus');
    importStatus.className = 'import-status';
    importStatus.innerHTML = '';
}

async function validateFile() {
    if (!selectedFile) {
        showToast('请先选择文件', 'error');
        return;
    }

    const validateBtn = document.getElementById('validateBtn');
    const importStatus = document.getElementById('importStatus');

    // Show loading state
    validateBtn.disabled = true;
    validateBtn.innerHTML = '<span class="spinner"></span> 校验中...';

    importStatus.className = 'import-status info show';
    importStatus.innerHTML = '<strong>正在校验数据，请稍候...</strong>';

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch(`${API_BASE_URL}/api/validate`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            let statusHtml = `
                <strong>校验完成！</strong><br>
                总记录: ${result.total} 条<br>
            `;

            if (result.errors > 0) {
                statusHtml += `<span style="color: #dc3545;">错误: ${result.errors} 条</span><br>`;
            } else {
                statusHtml += `<span style="color: #28a745;">错误: 0 条</span><br>`;
            }

            if (result.warnings > 0) {
                statusHtml += `<span style="color: #ffc107;">警告: ${result.warnings} 条</span>`;
            } else {
                statusHtml += `<span style="color: #28a745;">警告: 0 条</span>`;
            }

            importStatus.className = result.canImport ? 'import-status success show' : 'import-status error show';

            if (result.errorDetails && result.errorDetails.length > 0) {
                statusHtml += '<br><details style="margin-top: 10px;"><summary>查看错误详情</summary>';
                result.errorDetails.forEach(e => {
                    statusHtml += `<div style="font-size: 12px; margin-top: 5px;">行${e.row}: ${e.field} = '${e.value}' - ${e.message}</div>`;
                });
                statusHtml += '</details>';
            }

            if (result.warningDetails && result.warningDetails.length > 0) {
                statusHtml += '<details style="margin-top: 10px;"><summary>查看警告详情</summary>';
                result.warningDetails.forEach(w => {
                    statusHtml += `<div style="font-size: 12px; margin-top: 5px;">行${w.row}: ${w.field} = '${w.value}' - ${w.message}</div>`;
                });
                statusHtml += '</details>';
            }

            importStatus.innerHTML = statusHtml;

            showToast(`校验完成！${result.errors} 个错误，${result.warnings} 个警告`, result.canImport ? 'success' : 'error');

        } else {
            importStatus.className = 'import-status error show';
            importStatus.innerHTML = `<strong>校验失败</strong><br>${result.message || '未知错误'}`;
            showToast(result.message || '校验失败', 'error');
        }
    } catch (error) {
        importStatus.className = 'import-status error show';
        importStatus.innerHTML = `<strong>网络错误</strong><br>${error.message}`;
        showToast('网络错误，请检查服务器连接', 'error');
    } finally {
        validateBtn.disabled = false;
        validateBtn.innerHTML = '校验数据';
    }
}

async function importFile() {
    if (!selectedFile) {
        showToast('请先选择文件', 'error');
        return;
    }

    const importBtn = document.getElementById('importBtn');
    const importStatus = document.getElementById('importStatus');

    // Show loading state
    importBtn.disabled = true;
    importBtn.innerHTML = '<span class="spinner"></span> 导入中...';

    importStatus.className = 'import-status info show';
    importStatus.innerHTML = '<strong>正在导入，请稍候...</strong>';

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', selectedFile);

        // Send to API
        const response = await fetch(`${API_BASE_URL}/api/import`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            // Success
            importStatus.className = 'import-status success show';
            importStatus.innerHTML = `
                <strong>导入成功！</strong><br>
                总计: ${result.total} 条<br>
                成功: ${result.success} 条<br>
                失败: ${result.failed} 条
            `;

            showToast(`导入成功！共 ${result.success} 条数据`, 'success');

            // Close modal after 2 seconds
            setTimeout(() => {
                closeImportModal();
            }, 2000);

            // Refresh data if viewing table
            if (!document.getElementById('dataSection').classList.contains('hidden')) {
                refreshData();
            }
        } else {
            // Error
            importStatus.className = 'import-status error show';
            importStatus.innerHTML = `
                <strong>导入失败</strong><br>
                ${result.message || '未知错误'}
            `;

            showToast(result.message || '导入失败', 'error');
        }
    } catch (error) {
        importStatus.className = 'import-status error show';
        importStatus.innerHTML = `
            <strong>网络错误</strong><br>
            ${error.message}
        `;

        showToast('网络错误，请检查服务器连接', 'error');
    } finally {
        importBtn.disabled = false;
        importBtn.innerHTML = '开始导入';
    }
}

// ===== Data View Functions =====
async function viewData() {
    // Show data section
    const dataSection = document.getElementById('dataSection');
    dataSection.classList.remove('hidden');

    // Scroll to data section
    dataSection.scrollIntoView({ behavior: 'smooth' });

    // Load data
    await loadData();
}

function hideDataSection() {
    const dataSection = document.getElementById('dataSection');
    dataSection.classList.add('hidden');

    // Scroll to top
    window.scrollTo({ behavior: 'smooth' });
}

async function loadData() {
    const tableBody = document.getElementById('dataTableBody');
    const totalRecords = document.getElementById('totalRecords');
    const lastUpdate = document.getElementById('lastUpdate');

    // Show loading
    tableBody.innerHTML = '<tr><td colspan="16" class="loading"><span class="spinner"></span> 加载中...</td></tr>';

    try {
        let url = `${API_BASE_URL}/api/data?page=${currentPage}&pageSize=${pageSize}`;
        if (searchKeyword) {
            url += `&keyword=${encodeURIComponent(searchKeyword)}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('加载数据失败');
        }

        const result = await response.json();

        // Update stats
        totalRecords.textContent = result.total.toLocaleString();
        lastUpdate.textContent = new Date(result.lastUpdate).toLocaleString('zh-CN');

        // Update pagination
        totalPages = Math.ceil(result.total / pageSize);
        updatePagination();

        // Render table
        renderTable(result.data);

    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="16" class="loading">加载失败: ${error.message}</td></tr>`;
        showToast('加载数据失败', 'error');
    }
}

function renderTable(data) {
    const tableBody = document.getElementById('dataTableBody');

    if (data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="16" class="loading">暂无数据</td></tr>';
        return;
    }

    tableBody.innerHTML = data.map((row, index) => {
        const rowNumber = (currentPage - 1) * pageSize + index + 1;
        return `
            <tr>
                <td>${rowNumber}</td>
                <td>${escapeHtml(row.item_barcode)}</td>
                <td>${escapeHtml(row.item_name || '')}</td>
                <td>${escapeHtml(row.old_cat_name || '')}</td>
                <td>${escapeHtml(row.new_cat_name || '')}</td>
                <td>${escapeHtml(row.msy_item_name || '')}</td>
                <td>${escapeHtml(row.msy_cat_name || '')}</td>
                <td>${escapeHtml(row.eb_item_name || '')}</td>
                <td>${escapeHtml(row.eb_cat_name || '')}</td>
                <td>${escapeHtml(row.eb_size || '')}</td>
                <td>${escapeHtml(row.mt_item_name || '')}</td>
                <td>${escapeHtml(row.mt_cat_name || '')}</td>
                <td>${escapeHtml(row.mt_size || '')}</td>
                <td>${escapeHtml(row.gs1_item_name || '')}</td>
                <td>
                    <span class="editable-field" onclick="openEditModal('${escapeHtml(row.item_barcode)}', '${escapeHtml(row.new_name || '')}')">
                        ${escapeHtml(row.new_name || '')}
                        <svg class="edit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </span>
                </td>
                <td>${escapeHtml(row.valid_flag !== null ? row.valid_flag : '')}</td>
            </tr>
        `;
    }).join('');
}

function updatePagination() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const paginationInfo = document.getElementById('paginationInfo');

    // Update buttons
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    // Update info
    paginationInfo.textContent = `第 ${currentPage} / ${totalPages || 1} 页`;
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadData();
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadData();
    }
}

async function refreshData() {
    currentPage = 1;
    searchKeyword = '';
    document.getElementById('searchInput').value = '';
    await loadData();
    showToast('数据已刷新', 'success');
}

// ===== Search Functions =====
function handleSearch(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

async function performSearch() {
    const keyword = document.getElementById('searchInput').value.trim();
    searchKeyword = keyword;
    currentPage = 1;

    // 显示数据表格区域
    const dataSection = document.getElementById('dataSection');
    dataSection.classList.remove('hidden');

    await loadData();

    if (keyword) {
        showToast(`已搜索: ${keyword}`, 'info');
    }
}

// ===== Export Functions =====
function showExportModal() {
    document.getElementById('exportModal').classList.add('active');
}

function closeExportModal() {
    document.getElementById('exportModal').classList.remove('active');
}

async function exportData(format = 'excel') {
    closeExportModal();

    try {
        showToast('正在准备导出...', 'info');

        const response = await fetch(`${API_BASE_URL}/api/export?format=${format}`);

        if (!response.ok) {
            throw new Error('导出失败');
        }

        // Get filename from response headers
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = format === 'csv' ? 'data_export.csv' : 'data_export.xlsx';

        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        // Download blob
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('导出成功！', 'success');

    } catch (error) {
        showToast('导出失败: ' + error.message, 'error');
    }
}

// ===== Utility Functions =====
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== Edit Functions =====
function openEditModal(itemBarcode, newName) {
    document.getElementById('editBarcode').value = itemBarcode;
    document.getElementById('editNewName').value = newName;
    document.getElementById('editModal').classList.add('active');
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
    document.getElementById('editNewName').value = '';
}

async function saveEdit() {
    const itemBarcode = document.getElementById('editBarcode').value;
    const newName = document.getElementById('editNewName').value.trim();

    if (!newName) {
        showToast('请输入新的商品名称', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/update`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_barcode: itemBarcode,
                new_name: newName
            })
        });

        const result = await response.json();

        if (response.ok) {
            showToast('更新成功', 'success');
            closeEditModal();
            await loadData();
        } else {
            showToast(result.detail || '更新失败', 'error');
        }
    } catch (error) {
        showToast('更新失败: ' + error.message, 'error');
    }
}

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload();
});

// ===== Filter Export Functions =====
let currentTable = null;
let tableColumns = [];
let conditionCount = 0;

async function showFilterExportModal() {
    const modal = document.getElementById('filterExportModal');
    modal.classList.add('active');

    // 重置状态
    currentTable = null;
    tableColumns = [];
    conditionCount = 0;
    document.getElementById('fieldGroup').style.display = 'none';
    document.getElementById('conditionGroup').style.display = 'none';
    document.getElementById('limitGroup').style.display = 'none';
    document.getElementById('sqlPreviewGroup').style.display = 'none';
    document.getElementById('conditionsContainer').innerHTML = '';
    document.getElementById('sqlPreviewText').textContent = '';
    document.getElementById('estimatedRows').textContent = '预估行数: -';
    document.getElementById('previewBtn').disabled = true;
    document.getElementById('exportExcelBtn').disabled = true;
    document.getElementById('exportCsvBtn').disabled = true;

    // 加载表列表
    await loadTables();
}

function closeFilterExportModal() {
    document.getElementById('filterExportModal').classList.remove('active');
    document.getElementById('filterTableSelect').value = '';
}

async function loadTables() {
    try {
        console.log('[DEBUG] 正在请求 /api/tables...');
        const response = await fetch(`${API_BASE_URL}/api/tables`);
        console.log('[DEBUG] 响应状态:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        console.log('[DEBUG] API 响应:', result);

        if (result.success) {
            const select = document.getElementById('filterTableSelect');
            select.innerHTML = '<option value="">请选择表...</option>';

            if (result.tables && result.tables.length > 0) {
                result.tables.forEach(table => {
                    const option = document.createElement('option');
                    option.value = table;
                    option.textContent = table;
                    select.appendChild(option);
                });
                console.log(`[DEBUG] 成功加载 ${result.tables.length} 个表`);
            } else {
                console.warn('[DEBUG] 表列表为空');
                select.innerHTML += '<option disabled>没有可用的表</option>';
            }
        } else {
            showToast(result.detail || '加载表列表失败', 'error');
        }
    } catch (error) {
        console.error('[ERROR] 加载表列表失败:', error);
        showToast('加载表列表失败: ' + error.message, 'error');
    }
}

async function onTableChange() {
    const select = document.getElementById('filterTableSelect');
    currentTable = select.value;

    if (!currentTable) {
        document.getElementById('fieldGroup').style.display = 'none';
        document.getElementById('conditionGroup').style.display = 'none';
        document.getElementById('limitGroup').style.display = 'none';
        return;
    }

    // 加载字段信息
    await loadColumns(currentTable);

    // 显示字段选择区
    document.getElementById('fieldGroup').style.display = 'block';
    document.getElementById('conditionGroup').style.display = 'block';
    document.getElementById('limitGroup').style.display = 'block';

    // 清空并添加第一个条件行
    document.getElementById('conditionsContainer').innerHTML = '';
    conditionCount = 0;
    addConditionRow();
}

async function loadColumns(table) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tables/${table}/columns`);
        const result = await response.json();

        if (result.success) {
            tableColumns = result.columns;
            renderFieldCheckboxes(tableColumns);
        }
    } catch (error) {
        showToast('加载字段信息失败', 'error');
    }
}

function renderFieldCheckboxes(columns) {
    const container = document.getElementById('fieldCheckboxes');
    container.innerHTML = '';

    columns.forEach(col => {
        const div = document.createElement('div');
        div.className = 'field-checkbox';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `field_${col.name}`;
        checkbox.value = col.name;
        checkbox.checked = false;  // 默认不选中，防止误操作

        // 监听变化，更新按钮状态
        checkbox.addEventListener('change', updateExportButtons);

        const label = document.createElement('label');
        label.htmlFor = `field_${col.name}`;
        label.textContent = col.name;

        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });

    // 重置按钮状态
    updateExportButtons();
}

function updateExportButtons() {
    const hasSelectedFields = document.querySelectorAll('.field-checkbox input[type="checkbox"]:checked').length > 0;
    const hasTable = document.getElementById('filterTableSelect').value !== '';

    document.getElementById('previewBtn').disabled = !(hasTable && hasSelectedFields);
    document.getElementById('exportExcelBtn').disabled = !(hasTable && hasSelectedFields);
    document.getElementById('exportCsvBtn').disabled = !(hasTable && hasSelectedFields);
}

function selectAllFields() {
    const checkboxes = document.querySelectorAll('.field-checkbox input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = true);
    updateExportButtons();
}

function deselectAllFields() {
    const checkboxes = document.querySelectorAll('.field-checkbox input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
    updateExportButtons();
}

function addConditionRow() {
    const container = document.getElementById('conditionsContainer');
    const rowId = `condition_${conditionCount}`;

    const row = document.createElement('div');
    row.className = 'condition-row';
    row.id = rowId;

    // 字段选择
    const fieldSelect = document.createElement('select');
    fieldSelect.className = 'condition-field';
    tableColumns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.name;
        option.textContent = col.name;
        fieldSelect.appendChild(option);
    });

    // 操作符选择
    const opSelect = document.createElement('select');
    opSelect.className = 'condition-op';
    const operators = [
        { value: 'eq', label: '等于' },
        { value: 'ne', label: '不等于' },
        { value: 'gt', label: '大于' },
        { value: 'gte', label: '大于等于' },
        { value: 'lt', label: '小于' },
        { value: 'lte', label: '小于等于' },
        { value: 'like', label: '包含' },
        { value: 'not_like', label: '不包含' },
        { value: 'in', label: '在列表中' },
        { value: 'not_in', label: '不在列表中' },
        { value: 'is_null', label: '为空' },
        { value: 'is_not_null', label: '不为空' }
    ];
    operators.forEach(op => {
        const option = document.createElement('option');
        option.value = op.value;
        option.textContent = op.label;
        opSelect.appendChild(option);
    });

    // 值输入
    const valueInput = document.createElement('input');
    valueInput.type = 'text';
    valueInput.className = 'condition-value';
    valueInput.placeholder = '值（可选）';

    // 删除按钮
    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-remove';
    removeBtn.innerHTML = '×';
    removeBtn.onclick = () => removeConditionRow(rowId);

    row.appendChild(fieldSelect);
    row.appendChild(opSelect);
    row.appendChild(valueInput);
    row.appendChild(removeBtn);

    container.appendChild(row);
    conditionCount++;
}

function removeConditionRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
    }
}

async function previewQuery() {
    if (!currentTable) {
        showToast('请先选择表', 'error');
        return;
    }

    // 获取选中的字段
    const selectedFields = [];
    document.querySelectorAll('.field-checkbox input[type="checkbox"]:checked').forEach(cb => {
        selectedFields.push(cb.value);
    });

    if (selectedFields.length === 0) {
        showToast('请至少选择一个字段', 'error');
        return;
    }

    // 获取条件
    const conditions = [];
    document.querySelectorAll('.condition-row').forEach(row => {
        const field = row.querySelector('.condition-field').value;
        const op = row.querySelector('.condition-op').value;
        const value = row.querySelector('.condition-value').value;

        const condition = { field, op };

        if (op === 'in' || op === 'not_in') {
            condition.value = value ? value.split(',').map(v => v.trim()) : [];
        } else if (op !== 'is_null' && op !== 'is_not_null') {
            condition.value = value || null;
        }

        if (op === 'is_null' || op === 'is_not_null' || value) {
            conditions.push(condition);
        }
    });

    // 获取限制
    const limit = parseInt(document.getElementById('exportLimit').value) || 10000;

    const previewBtn = document.getElementById('previewBtn');
    previewBtn.disabled = true;
    previewBtn.innerHTML = '<span class="spinner"></span> 预览中...';

    try {
        const response = await fetch(`${API_BASE_URL}/api/query/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                table: currentTable,
                fields: selectedFields,
                conditions: conditions.length > 0 ? conditions : null,
                limit: limit
            })
        });

        const result = await response.json();

        if (result.success) {
            // 显示 SQL 预览
            document.getElementById('sqlPreviewGroup').style.display = 'block';
            document.getElementById('sqlPreviewText').textContent = result.sql;
            document.getElementById('estimatedRows').textContent = `预估行数: ${result.estimatedRows.toLocaleString()}`;

            // 启用导出按钮
            document.getElementById('exportExcelBtn').disabled = result.estimatedRows === 0;
            document.getElementById('exportCsvBtn').disabled = result.estimatedRows === 0;

            showToast('预览成功', 'success');
        } else {
            showToast(result.detail || '预览失败', 'error');
        }
    } catch (error) {
        showToast('预览失败: ' + error.message, 'error');
    } finally {
        previewBtn.disabled = false;
        previewBtn.innerHTML = '预览 SQL';
    }
}

async function executeExport(format) {
    if (!currentTable) {
        showToast('请先选择表', 'error');
        return;
    }

    // 获取选中的字段
    const selectedFields = [];
    document.querySelectorAll('.field-checkbox input[type="checkbox"]:checked').forEach(cb => {
        selectedFields.push(cb.value);
    });

    // 获取条件
    const conditions = [];
    document.querySelectorAll('.condition-row').forEach(row => {
        const field = row.querySelector('.condition-field').value;
        const op = row.querySelector('.condition-op').value;
        const value = row.querySelector('.condition-value').value;

        const condition = { field, op };

        if (op === 'in' || op === 'not_in') {
            condition.value = value ? value.split(',').map(v => v.trim()) : [];
        } else if (op !== 'is_null' && op !== 'is_not_null') {
            condition.value = value || null;
        }

        if (op === 'is_null' || op === 'is_not_null' || value) {
            conditions.push(condition);
        }
    });

    // 获取预估行数（从 SQL 预览中获取）
    const estimatedRowsText = document.getElementById('estimatedRows').textContent;
    let estimatedRows = 0;
    const match = estimatedRowsText.match(/预估行数:\s*([\d,]+)/);
    if (match) {
        estimatedRows = parseInt(match[1].replace(/,/g, '')) || 0;
    }

    // 单次限制
    const BATCH_SIZE = 10000;

    showToast(`正在导出，预计 ${estimatedRows.toLocaleString()} 条数据...`, 'info');

    try {
        let allData = [];
        let offset = 0;
        let totalFetched = 0;

        // 分批获取数据
        while (true) {
            const response = await fetch(`${API_BASE_URL}/api/query/export?format=json`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    table: currentTable,
                    fields: selectedFields,
                    conditions: conditions.length > 0 ? conditions : null,
                    limit: BATCH_SIZE,
                    offset: offset
                })
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.detail || '获取数据失败');
            }

            const result = await response.json();

            if (result.data && result.data.length > 0) {
                allData = allData.concat(result.data);
                totalFetched += result.data.length;
                offset += BATCH_SIZE;

                // 更新进度
                const progress = estimatedRows > 0 ? Math.round((totalFetched / estimatedRows) * 100) : null;
                showToast(`已获取 ${totalFetched.toLocaleString()} 条数据${progress ? ` (${progress}%)` : ''}...`, 'info');

                // 如果获取的数据少于批次大小，说明已经获取完所有数据
                if (result.data.length < BATCH_SIZE) {
                    break;
                }
            } else {
                // 没有更多数据
                break;
            }

            // 安全限制：最多 50 万条
            if (totalFetched >= 500000) {
                showToast('已达到最大导出限制（50万条），停止获取', 'warning');
                break;
            }
        }

        if (allData.length === 0) {
            showToast('没有符合条件的数据', 'warning');
            return;
        }

        // 导出文件
        await exportDataToFile(allData, format, selectedFields);
        showToast(`导出成功！共 ${allData.length.toLocaleString()} 条数据`, 'success');

    } catch (error) {
        showToast('导出失败: ' + error.message, 'error');
    }
}

async function exportDataToFile(data, format, fields) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `query_export_${timestamp}.${format}`;

    if (format === 'csv') {
        // 导出为 CSV
        const csvContent = convertToCSV(data, fields);
        const blob = new Blob(['﻿' + csvContent], { type: 'text/csv;charset=utf-8;' });
        downloadBlob(blob, filename);
    } else {
        // 导出为 Excel（使用简单的表格格式）
        const excelContent = convertToExcelXML(data, fields);
        const blob = new Blob([excelContent], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        downloadBlob(blob, filename);
    }
}

function convertToCSV(data, fields) {
    if (data.length === 0) return '';

    // 表头
    const headers = fields.join(',');
    // 数据行
    const rows = data.map(row => {
        return fields.map(field => {
            const value = row[field];
            if (value === null || value === undefined) return '';
            const strValue = String(value);
            // 如果包含逗号、引号或换行，需要用引号包裹并转义
            if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
                return `"${strValue.replace(/"/g, '""')}"`;
            }
            return strValue;
        }).join(',');
    }).join('\n');

    return headers + '\n' + rows;
}

function convertToExcelXML(data, fields) {
    // 简单的 SpreadsheetML 格式（Excel 2003 XML）
    const rows = data.map(row => {
        return '<Row>' + fields.map(field => {
            const value = row[field];
            if (value === null || value === undefined) {
                return '<Cell><Data ss:Type="String"></Data></Cell>';
            }
            return `<Cell><Data ss:Type="String">${escapeXml(String(value))}</Data></Cell>`;
        }).join('') + '</Row>';
    }).join('');

    const header = '<Row>' + fields.map(f => `<Cell><Data ss:Type="String">${escapeXml(f)}</Data></Cell>`).join('') + '</Row>';

    return `<?xml version="1.0"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Worksheet ss:Name="Sheet1">
  <Table>
   ${header}
   ${rows}
  </Table>
 </Worksheet>
</Workbook>`;
}

function escapeXml(str) {
    return str.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;')
               .replace(/'/g, '&apos;');
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// ===== Batch Update Functions =====
let updateTableColumns = [];
let updateConditionCount = 0;
let selectedUpdateFields = new Set();

function switchTab(tab) {
    // 切换选项卡
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // 切换按钮显示
    const exportButtons = document.getElementById('exportButtons');
    const updateButtons = document.getElementById('updateButtons');

    if (tab === 'export') {
        document.getElementById('tabExport').classList.add('active');
        document.getElementById('exportTabContent').classList.add('active');
        exportButtons.style.display = '';
        updateButtons.style.display = 'none';
    } else {
        document.getElementById('tabUpdate').classList.add('active');
        document.getElementById('updateTabContent').classList.add('active');
        exportButtons.style.display = 'none';
        updateButtons.style.display = '';
        // 加载表列表
        loadUpdateTables();
    }
}

async function loadUpdateTables() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tables`);
        const result = await response.json();

        if (result.success) {
            const select = document.getElementById('updateTableSelect');
            select.innerHTML = '<option value="">请选择表...</option>';

            result.tables.forEach(table => {
                const option = document.createElement('option');
                option.value = table;
                option.textContent = table;
                select.appendChild(option);
            });
        }
    } catch (error) {
        showToast('加载表列表失败', 'error');
    }
}

async function onUpdateTableChange() {
    const select = document.getElementById('updateTableSelect');
    const table = select.value;

    // 重置状态
    selectedUpdateFields.clear();
    document.getElementById('updateFieldSearch').value = '';

    if (!table) {
        document.getElementById('updateFieldSelectGroup').style.display = 'none';
        document.getElementById('updateFieldValueGroup').style.display = 'none';
        document.getElementById('updateConditionGroup').style.display = 'none';
        document.getElementById('updateLimitGroup').style.display = 'none';
        return;
    }

    // 加载字段信息
    try {
        const response = await fetch(`${API_BASE_URL}/api/tables/${table}/columns`);
        const result = await response.json();

        if (result.success) {
            updateTableColumns = result.columns;
            renderUpdateFieldCheckboxes(updateTableColumns);
            renderUpdateConditionFields(updateTableColumns);

            document.getElementById('updateFieldSelectGroup').style.display = 'block';
            document.getElementById('updateConditionGroup').style.display = 'block';
            document.getElementById('updateLimitGroup').style.display = 'block';
            document.getElementById('updateFieldValueGroup').style.display = 'none';

            // 添加第一个条件
            document.getElementById('updateConditionsContainer').innerHTML = '';
            updateConditionCount = 0;
            addUpdateConditionRow();
        }
    } catch (error) {
        showToast('加载字段信息失败', 'error');
    }
}

function renderUpdateFieldCheckboxes(columns) {
    const container = document.getElementById('updateFieldCheckboxes');
    container.innerHTML = '';

    columns.forEach(col => {
        const div = document.createElement('div');
        div.className = 'field-checkbox update-field-checkbox';
        div.dataset.fieldName = col.name.toLowerCase();

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `update_field_${col.name}`;
        checkbox.value = col.name;
        checkbox.checked = false;

        // 监听变化
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                selectedUpdateFields.add(col.name);
            } else {
                selectedUpdateFields.delete(col.name);
            }
            renderUpdateFieldValueInputs();
        });

        const label = document.createElement('label');
        label.htmlFor = `update_field_${col.name}`;
        label.textContent = `${col.name} (${col.type})`;

        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
}

function filterUpdateFields() {
    const searchText = document.getElementById('updateFieldSearch').value.toLowerCase();
    document.querySelectorAll('.update-field-checkbox').forEach(div => {
        const fieldName = div.dataset.fieldName;
        div.style.display = fieldName.includes(searchText) ? '' : 'none';
    });
}

function selectAllUpdateFields() {
    document.querySelectorAll('.update-field-checkbox input[type="checkbox"]').forEach(cb => {
        cb.checked = true;
        selectedUpdateFields.add(cb.value);
    });
    renderUpdateFieldValueInputs();
}

function deselectAllUpdateFields() {
    document.querySelectorAll('.update-field-checkbox input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    selectedUpdateFields.clear();
    renderUpdateFieldValueInputs();
}

function renderUpdateFieldValueInputs() {
    const container = document.getElementById('updateFieldValueInputs');
    container.innerHTML = '';

    if (selectedUpdateFields.size === 0) {
        document.getElementById('updateFieldValueGroup').style.display = 'none';
        return;
    }

    document.getElementById('updateFieldValueGroup').style.display = 'block';

    // 按字段信息查找详细信息
    selectedUpdateFields.forEach(fieldName => {
        const col = updateTableColumns.find(c => c.name === fieldName);
        if (!col) return;

        const div = document.createElement('div');
        div.className = 'form-group';
        div.style.marginBottom = 'var(--spacing-sm)';

        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = `${col.name} (${col.type})`;

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-input update-field-value-input';
        input.dataset.field = col.name;
        input.placeholder = `输入新的 ${col.name} 值`;

        const hint = document.createElement('span');
        hint.className = 'form-hint';
        hint.textContent = col.comment || `输入要更新的值`;

        div.appendChild(label);
        div.appendChild(input);
        div.appendChild(hint);
        container.appendChild(div);
    });
}

function renderUpdateConditionFields(columns) {
    // 条件行中的字段选择会在 addUpdateConditionRow 中动态生成
}

function addUpdateConditionRow() {
    const container = document.getElementById('updateConditionsContainer');
    const rowId = `update_condition_${updateConditionCount}`;

    const row = document.createElement('div');
    row.className = 'condition-row';
    row.id = rowId;

    // 字段选择
    const fieldSelect = document.createElement('select');
    fieldSelect.className = 'condition-field update-condition-field';
    updateTableColumns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.name;
        option.textContent = col.name;
        fieldSelect.appendChild(option);
    });

    // 操作符选择
    const opSelect = document.createElement('select');
    opSelect.className = 'condition-op update-condition-op';
    const operators = [
        { value: 'eq', label: '等于' },
        { value: 'ne', label: '不等于' },
        { value: 'gt', label: '大于' },
        { value: 'gte', label: '大于等于' },
        { value: 'lt', label: '小于' },
        { value: 'lte', label: '小于等于' },
        { value: 'like', label: '包含' },
        { value: 'not_like', label: '不包含' },
        { value: 'in', label: '在列表中' },
        { value: 'not_in', label: '不在列表中' },
        { value: 'is_null', label: '为空' },
        { value: 'is_not_null', label: '不为空' }
    ];
    operators.forEach(op => {
        const option = document.createElement('option');
        option.value = op.value;
        option.textContent = op.label;
        opSelect.appendChild(option);
    });

    // 值输入
    const valueInput = document.createElement('input');
    valueInput.type = 'text';
    valueInput.className = 'condition-value update-condition-value';
    valueInput.placeholder = '值';

    // 删除按钮
    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-remove';
    removeBtn.innerHTML = '×';
    removeBtn.onclick = () => {
        row.remove();
    };

    row.appendChild(fieldSelect);
    row.appendChild(opSelect);
    row.appendChild(valueInput);
    row.appendChild(removeBtn);

    container.appendChild(row);
    updateConditionCount++;
}

async function previewUpdate() {
    const table = document.getElementById('updateTableSelect').value;
    if (!table) {
        showToast('请先选择表', 'error');
        return;
    }

    // 获取要更新的字段和值（从选中的字段的输入框获取）
    const fieldValues = {};
    document.querySelectorAll('.update-field-value-input').forEach(input => {
        const value = input.value.trim();
        if (value) {
            fieldValues[input.dataset.field] = value;
        }
    });

    if (Object.keys(fieldValues).length === 0) {
        showToast('请至少填写一个要更新的字段值', 'error');
        return;
    }

    // 获取条件
    const conditions = [];
    document.querySelectorAll('#updateConditionsContainer .condition-row').forEach(row => {
        const field = row.querySelector('.update-condition-field').value;
        const op = row.querySelector('.update-condition-op').value;
        const value = row.querySelector('.update-condition-value').value;

        const condition = { field, op };

        if (op === 'in' || op === 'not_in') {
            condition.value = value ? value.split(',').map(v => v.trim()) : [];
        } else if (op !== 'is_null' && op !== 'is_not_null') {
            condition.value = value || null;
        }

        if (op === 'is_null' || op === 'is_not_null' || value) {
            conditions.push(condition);
        }
    });

    if (conditions.length === 0) {
        showToast('请至少添加一个筛选条件（防止误操作）', 'error');
        return;
    }

    // 获取限制
    const limitValue = document.getElementById('updateLimit').value;
    const limit = limitValue ? parseInt(limitValue) : null;

    showToast('正在预览...', 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/api/query/update/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                table: table,
                field_values: fieldValues,
                conditions: conditions,
                limit: limit
            })
        });

        const result = await response.json();

        if (result.success) {
            // 显示 SQL 预览
            document.getElementById('updateSqlPreviewGroup').style.display = 'block';
            document.getElementById('updateSqlPreviewText').textContent = result.updateSql;
            document.getElementById('updateEstimatedRows').textContent = `预估影响行数: ${result.estimatedRows.toLocaleString()}`;

            showToast('预览成功', 'success');
        } else {
            showToast(result.detail || '预览失败', 'error');
        }
    } catch (error) {
        showToast('预览失败: ' + error.message, 'error');
    }
}

async function executeUpdate() {
    const table = document.getElementById('updateTableSelect').value;
    if (!table) {
        showToast('请先选择表', 'error');
        return;
    }

    // 获取要更新的字段和值（从选中的字段的输入框获取）
    const fieldValues = {};
    document.querySelectorAll('.update-field-value-input').forEach(input => {
        const value = input.value.trim();
        if (value) {
            fieldValues[input.dataset.field] = value;
        }
    });

    if (Object.keys(fieldValues).length === 0) {
        showToast('请至少填写一个要更新的字段值', 'error');
        return;
    }

    // 获取条件
    const conditions = [];
    document.querySelectorAll('#updateConditionsContainer .condition-row').forEach(row => {
        const field = row.querySelector('.update-condition-field').value;
        const op = row.querySelector('.update-condition-op').value;
        const value = row.querySelector('.update-condition-value').value;

        const condition = { field, op };

        if (op === 'in' || op === 'not_in') {
            condition.value = value ? value.split(',').map(v => v.trim()) : [];
        } else if (op !== 'is_null' && op !== 'is_not_null') {
            condition.value = value || null;
        }

        if (op === 'is_null' || op === 'is_not_null' || value) {
            conditions.push(condition);
        }
    });

    if (conditions.length === 0) {
        showToast('请至少添加一个筛选条件（防止误操作）', 'error');
        return;
    }

    // 二次确认
    const confirmMsg = `确认要更新 ${table} 表吗？\n此操作不可撤销！`;
    if (!confirm(confirmMsg)) {
        return;
    }

    // 获取限制
    const limitValue = document.getElementById('updateLimit').value;
    const limit = limitValue ? parseInt(limitValue) : null;

    showToast('正在执行更新...', 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/api/query/update/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                table: table,
                field_values: fieldValues,
                conditions: conditions,
                limit: limit
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`更新成功！影响了 ${result.affectedRows.toLocaleString()} 条数据`, 'success');

            // 清空输入
            document.querySelectorAll('.update-field-value-input').forEach(input => input.value = '');
            document.querySelectorAll('.update-field-checkbox input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
            selectedUpdateFields.clear();
            renderUpdateFieldValueInputs();
            document.getElementById('updateSqlPreviewGroup').style.display = 'none';
        } else {
            showToast(result.detail || '更新失败', 'error');
        }
    } catch (error) {
        showToast('更新失败: ' + error.message, 'error');
    }
}
