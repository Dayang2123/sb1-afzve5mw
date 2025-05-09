/**
 * AI内容创作平台主JavaScript文件
 */

// 在DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    initTooltips();
    
    // 初始化确认对话框
    initConfirmDialogs();
    
    // 初始化表单验证
    initFormValidation();
    
    // 初始化任务轮询
    initTaskPolling();
    
    // 初始化敏感词过滤
    initSensitiveWordFilter();
});

/**
 * 初始化Bootstrap工具提示
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 初始化确认对话框
 */
function initConfirmDialogs() {
    // 为所有带有data-confirm属性的元素添加确认对话框
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(event) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                event.preventDefault();
            }
        });
    });
}

/**
 * 初始化表单验证
 */
function initFormValidation() {
    // 获取所有需要验证的表单
    var forms = document.querySelectorAll('.needs-validation');
    
    // 遍历表单并阻止提交
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * 初始化任务轮询
 */
function initTaskPolling() {
    // 查找任务状态元素
    var taskStatusElements = document.querySelectorAll('[data-task-id]');
    
    if (taskStatusElements.length > 0) {
        // 定期检查任务状态
        setInterval(function() {
            taskStatusElements.forEach(function(element) {
                var taskId = element.getAttribute('data-task-id');
                updateTaskStatus(taskId, element);
            });
        }, 5000); // 每5秒检查一次
    }
}

/**
 * 更新任务状态
 * @param {string} taskId - 任务ID
 * @param {Element} element - 显示任务状态的DOM元素
 */
function updateTaskStatus(taskId, element) {
    fetch('/api/tasks/' + taskId)
        .then(response => response.json())
        .then(data => {
            // 更新状态文本
            element.textContent = getStatusText(data.status);
            
            // 更新状态类
            element.className = element.className.replace(/task-status-\w+/, '');
            element.classList.add('task-status-' + data.status);
            
            // 如果任务完成，刷新页面
            if (data.status === 'completed' && element.getAttribute('data-reload-on-complete') === 'true') {
                window.location.reload();
            }
        })
        .catch(error => console.error('获取任务状态失败:', error));
}

/**
 * 获取状态文本
 * @param {string} status - 任务状态
 * @returns {string} 状态的中文描述
 */
function getStatusText(status) {
    switch (status) {
        case 'pending':
            return '等待中';
        case 'running':
            return '运行中';
        case 'completed':
            return '已完成';
        case 'failed':
            return '失败';
        default:
            return status;
    }
}

/**
 * 初始化敏感词过滤
 */
function initSensitiveWordFilter() {
    // 查找需要过滤敏感词的输入框
    var filterInputs = document.querySelectorAll('[data-filter-sensitive]');
    
    filterInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            filterSensitiveWords(this);
        });
    });
}

/**
 * 过滤敏感词
 * @param {Element} input - 输入框元素
 */
function filterSensitiveWords(input) {
    var text = input.value;
    
    if (text.trim() === '') {
        return;
    }
    
    fetch('/api/filter_text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.filtered_text !== text) {
            input.value = data.filtered_text;
            
            // 显示提示
            if (data.found_words && data.found_words.length > 0) {
                var words = data.found_words.map(w => w.word).join(', ');
                alert('检测到敏感词: ' + words + '\n已自动过滤');
            }
        }
    })
    .catch(error => console.error('过滤敏感词失败:', error));
}

/**
 * 获取CSRF令牌
 * @returns {string} CSRF令牌
 */
function getCsrfToken() {
    return document.querySelector('input[name="csrf_token"]').value;
}

/**
 * 显示加载动画
 */
function showLoading() {
    var spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
    document.body.appendChild(spinner);
}

/**
 * 隐藏加载动画
 */
function hideLoading() {
    var spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

/**
 * 格式化日期时间
 * @param {string} dateString - 日期字符串
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(dateString) {
    var date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 */
function copyToClipboard(text) {
    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        alert('已复制到剪贴板');
    } catch (err) {
        console.error('复制失败:', err);
        alert('复制失败');
    }
    
    document.body.removeChild(textarea);
}