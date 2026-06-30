-- 认证系统相关表
-- 在现有数据库 bigdata_main_data2 中执行

-- 用户表
CREATE TABLE IF NOT EXISTS data_sync_sys_user (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(100) COMMENT '真实姓名',
    email VARCHAR(100) COMMENT '邮箱',
    role_code VARCHAR(50) DEFAULT 'viewer' COMMENT '角色编码: admin/operator/viewer',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_role (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据存储同步系统用户表';

-- 操作日志表
CREATE TABLE IF NOT EXISTS data_sync_sys_operation_log (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id INT COMMENT '用户ID',
    username VARCHAR(50) COMMENT '用户名',
    operation_type VARCHAR(20) NOT NULL COMMENT '操作类型: login/logout/import/export/view/edit',
    stage_id INT COMMENT '阶段ID: 1-5',
    table_name VARCHAR(50) COMMENT '操作的表名',
    affected_rows INT DEFAULT 0 COMMENT '影响行数',
    status VARCHAR(20) DEFAULT 'success' COMMENT '状态: success/failed',
    error_message TEXT COMMENT '错误信息',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_stage_created (stage_id, created_at),
    INDEX idx_operation_type (operation_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据存储同步系统操作日志表';

-- 插入初始管理员账号
-- 用户名: admin
-- 密码: admin123
-- 密码使用 bcrypt 哈希
INSERT INTO data_sync_sys_user (username, password_hash, real_name, role_code, is_active) VALUES
('admin', '$2b$12$pio8oT8WmAzCHgPNq230D.jkc5Vl465x27WPfRfCRwfaIRd2yQbD2', '系统管理员', 'admin', TRUE)
ON DUPLICATE KEY UPDATE real_name = '系统管理员';

-- 说明：
-- 初始密码为 admin123
-- 登录后建议立即修改密码
