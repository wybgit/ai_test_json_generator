#!/bin/bash

# AI Web工具快速清理脚本
# 使用方法: ./clean.sh [天数]

set -e

# 默认清理7天前的文件
DAYS=${1:-7}

echo "🧹 AI Web工具快速清理"
echo "=================================="
echo "📅 清理 $DAYS 天前的文件"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_TOOL_DIR="$SCRIPT_DIR"

# 定义目录
OUTPUTS_DIR="$WEB_TOOL_DIR/shared/outputs"
UPLOADS_DIR="$WEB_TOOL_DIR/shared/uploads"

# 清理函数
cleanup_directory() {
    local dir="$1"
    local name="$2"
    
    if [[ -d "$dir" ]]; then
        echo "🗂️  清理 $name: $dir"
        
        # 计算清理前的大小
        local before_size=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "0")
        
        # 查找并删除旧文件/目录
        local count=0
        if [[ "$dir" == *"outputs"* ]]; then
            # 对于outputs目录，删除整个执行目录
            while IFS= read -r -d '' item; do
                echo "   📁 删除: $(basename "$item")"
                rm -rf "$item"
                ((count++))
            done < <(find "$dir" -maxdepth 1 -type d -mtime +$DAYS -print0 2>/dev/null)
        else
            # 对于其他目录，删除文件
            while IFS= read -r -d '' item; do
                echo "   📄 删除: $(basename "$item")"
                rm -f "$item"
                ((count++))
            done < <(find "$dir" -type f -mtime +$DAYS -print0 2>/dev/null)
        fi
        
        # 计算清理后的大小
        local after_size=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "0")
        
        echo "   ✅ 删除了 $count 个项目"
        echo ""
    else
        echo "⚠️  目录不存在，跳过: $dir"
        echo ""
    fi
}

# 清理临时文件
cleanup_temp_files() {
    echo "🗑️  清理临时文件"
    
    local count=0
    local patterns=("/tmp/tmp*csv" "/tmp/tmp*txt" "/tmp/tmp*prompt*")
    
    for pattern in "${patterns[@]}"; do
        for file in $pattern 2>/dev/null; do
            if [[ -f "$file" ]]; then
                # 检查文件是否超过1小时未修改
                if [[ $(find "$file" -mmin +60 2>/dev/null) ]]; then
                    echo "   🗑️  删除: $(basename "$file")"
                    rm -f "$file"
                    ((count++))
                fi
            fi
        done
    done
    
    echo "   ✅ 删除了 $count 个临时文件"
    echo ""
}

# 显示磁盘使用情况
show_disk_usage() {
    echo "💾 磁盘使用情况:"
    if [[ -d "$WEB_TOOL_DIR/shared" ]]; then
        du -sh "$WEB_TOOL_DIR/shared" 2>/dev/null || echo "   无法获取大小信息"
    fi
    echo ""
}

# 主要清理流程
main() {
    echo "📂 工作目录: $WEB_TOOL_DIR"
    echo ""
    
    # 显示清理前的磁盘使用情况
    echo "🔍 清理前:"
    show_disk_usage
    
    # 执行清理
    cleanup_directory "$OUTPUTS_DIR" "输出目录"
    cleanup_directory "$UPLOADS_DIR" "上传目录"
    cleanup_temp_files
    
    # 显示清理后的磁盘使用情况
    echo "✅ 清理后:"
    show_disk_usage
    
    echo "🎉 清理完成！"
}

# 检查参数
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "AI Web工具快速清理脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [天数]"
    echo ""
    echo "参数:"
    echo "  天数    删除N天前的文件 (默认: 7天)"
    echo ""
    echo "示例:"
    echo "  $0        # 清理7天前的文件"
    echo "  $0 3      # 清理3天前的文件"
    echo "  $0 0      # 清理所有文件"
    exit 0
fi

# 验证参数
if ! [[ "$DAYS" =~ ^[0-9]+$ ]]; then
    echo "❌ 错误: 参数必须是数字"
    echo "使用 $0 --help 查看帮助"
    exit 1
fi

# 确认操作
if [[ "$DAYS" -eq 0 ]]; then
    echo "⚠️  警告: 将删除所有历史文件!"
else
    echo "⚠️  将删除 $DAYS 天前的历史文件"
fi

read -p "确定继续吗? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消清理操作"
    exit 0
fi

echo ""

# 执行清理
main
