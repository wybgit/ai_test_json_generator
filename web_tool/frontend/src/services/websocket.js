// WebSocket服务模块
class WebSocketService {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentExecutionId = null;
        this.callbacks = {
            connect: [],
            disconnect: [],
            executionStarted: [],
            executionLog: [],
            executionCompleted: [],
            executionError: [],
            executionStopped: []
        };
    }

    // 连接WebSocket
    connect(url = 'http://localhost:5000') {
        try {
            this.socket = io(url);
            this.setupEventListeners();
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            this.updateConnectionStatus(false);
        }
    }

    // 设置事件监听器
    setupEventListeners() {
        this.socket.on('connect', () => {
            console.log('WebSocket连接成功');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.triggerCallbacks('connect');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket连接断开');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.triggerCallbacks('disconnect');
        });

        this.socket.on('execution_started', (data) => {
            console.log('执行开始:', data);
            this.currentExecutionId = data.execution_id;
            this.triggerCallbacks('executionStarted', data);
        });

        this.socket.on('execution_log', (data) => {
            console.log('执行日志:', data);
            this.triggerCallbacks('executionLog', data);
        });

        this.socket.on('execution_completed', (data) => {
            console.log('执行完成:', data);
            this.triggerCallbacks('executionCompleted', data);
        });

        this.socket.on('execution_error', (data) => {
            console.error('执行错误:', data);
            this.triggerCallbacks('executionError', data);
        });

        this.socket.on('execution_stopped', (data) => {
            console.log('执行停止:', data);
            this.triggerCallbacks('executionStopped', data);
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket连接错误:', error);
            this.updateConnectionStatus(false);
        });
    }

    // 更新连接状态显示
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            if (connected) {
                statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> 已连接';
            } else {
                statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i> 已断开';
            }
        }
    }

    // 添加事件回调
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }

    // 移除事件回调
    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }

    // 触发回调
    triggerCallbacks(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`回调执行错误 (${event}):`, error);
                }
            });
        }
    }

    // 异步执行工具
    executeToolAsync(toolName, params) {
        if (!this.isConnected) {
            throw new Error('WebSocket未连接');
        }

        this.socket.emit('execute_tool_async', {
            tool_name: toolName,
            params: params
        });
    }

    // 停止执行
    stopExecution(executionId) {
        if (!this.isConnected) {
            throw new Error('WebSocket未连接');
        }

        this.socket.emit('stop_execution', {
            execution_id: executionId
        });
    }

    // 加入执行房间
    joinExecution(executionId) {
        if (!this.isConnected) {
            throw new Error('WebSocket未连接');
        }

        this.socket.emit('join_execution', {
            execution_id: executionId
        });
    }

    // 离开执行房间
    leaveExecution(executionId) {
        if (!this.isConnected) {
            throw new Error('WebSocket未连接');
        }

        this.socket.emit('leave_execution', {
            execution_id: executionId
        });
    }

    // 获取执行状态
    getExecutionStatus(executionId) {
        if (!this.isConnected) {
            throw new Error('WebSocket未连接');
        }

        this.socket.emit('get_execution_status', {
            execution_id: executionId
        });
    }

    // 列出活动执行
    listActiveExecutions() {
        if (!this.isConnected) {
            throw new Error('WebSocket未连接');
        }

        this.socket.emit('list_active_executions');
    }

    // 断开连接
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
            this.currentExecutionId = null;
        }
    }

    // 重新连接
    reconnect() {
        this.disconnect();
        setTimeout(() => {
            this.connect();
        }, 1000);
    }
}

// 创建全局WebSocket实例
window.wsService = new WebSocketService();
