# AI Web工具清理脚本说明

本目录包含两个清理脚本，用于管理和清理Web工具产生的历史文件。

## 脚本介绍

### 1. cleanup_history.py - 完整功能清理脚本

功能全面的Python清理脚本，支持详细的配置和预览功能。

**功能特点:**
- ✅ 预览模式 (`--dry-run`) - 只显示将要删除的文件，不实际删除
- ✅ 可配置天数阈值 (`--days N`) - 删除N天前的文件
- ✅ 详细信息显示 (`--verbose`) - 显示每个被删除文件的详细信息
- ✅ 强制模式 (`--force`) - 跳过确认提示
- ✅ 智能文件大小计算和显示
- ✅ 完整的清理摘要报告

**使用方法:**
```bash
# 预览将要删除的文件（推荐先运行）
python cleanup_history.py --dry-run --verbose

# 删除7天前的文件（默认）
python cleanup_history.py

# 删除3天前的文件，显示详细信息
python cleanup_history.py --days 3 --verbose

# 强制删除，不询问确认
python cleanup_history.py --force

# 查看帮助
python cleanup_history.py --help
```

### 2. clean.sh - 快速清理脚本

简单易用的Bash脚本，适合日常快速清理。

**功能特点:**
- ✅ 简单直接，一键清理
- ✅ 显示清理前后的磁盘使用情况
- ✅ 安全确认机制
- ✅ 支持自定义天数参数

**使用方法:**
```bash
# 清理7天前的文件（默认）
./clean.sh

# 清理3天前的文件
./clean.sh 3

# 清理所有文件（谨慎使用）
./clean.sh 0

# 查看帮助
./clean.sh --help
```

## 清理内容

两个脚本都会清理以下内容：

### 1. 输出目录 (`shared/outputs/`)
- 删除过期的执行结果目录
- 每个目录包含工具的输出文件（JSON、ONNX、日志等）
- 通常是占用空间最多的部分

### 2. 上传目录 (`shared/uploads/`)
- 删除过期的用户上传文件
- 包括CSV文件、模板文件等

### 3. 临时文件 (`/tmp/`)
- 删除系统临时目录中的相关文件
- 包括临时CSV文件、Prompt文件等
- 只删除超过1小时未修改的文件

### 4. 日志文件 (`logs/`)
- 删除过期的日志文件
- 保留最近的日志用于调试

## 安全性说明

### 🔒 安全特性
- **确认机制**: 所有删除操作都需要用户确认
- **预览模式**: 可以先预览要删除的文件
- **日期检查**: 只删除超过指定天数的文件
- **路径验证**: 只在指定目录内操作

### ⚠️ 注意事项
- 删除的文件**无法恢复**，请谨慎操作
- 建议先使用预览模式查看要删除的文件
- 重要的执行结果请及时备份
- 不要删除正在使用的文件

## 推荐使用流程

### 日常维护（推荐）
```bash
# 1. 先预览要删除的文件
python cleanup_history.py --dry-run --verbose

# 2. 确认无误后执行清理
python cleanup_history.py --verbose
```

### 快速清理
```bash
# 使用快速脚本
./clean.sh
```

### 深度清理（空间不足时）
```bash
# 删除3天前的文件
python cleanup_history.py --days 3 --verbose
```

## 自动化建议

可以将清理脚本加入到系统的定时任务中：

```bash
# 编辑crontab
crontab -e

# 添加每周日凌晨2点自动清理7天前的文件
0 2 * * 0 cd /path/to/web_tool && python cleanup_history.py --force --days 7
```

## 故障排除

### 权限错误
```bash
# 确保脚本有执行权限
chmod +x cleanup_history.py clean.sh
```

### 路径错误
- 确保在web_tool目录下运行脚本
- 或使用`--web-tool-dir`参数指定正确路径

### 磁盘空间
- 如果磁盘空间严重不足，可以使用`--days 1`或更小的值
- 先清理临时文件：`python cleanup_history.py --days 0`（只清理临时文件）

---

**最后更新**: 2025年8月26日
**版本**: 1.0
