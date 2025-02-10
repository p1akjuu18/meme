#!/bin/bash

# =================
# 服务器配置信息
# =================
# 服务器用户名
REMOTE_USER="administrator"

# 服务器IP地址
REMOTE_HOST="47.76.248.209"

# 服务器密码
REMOTE_PASS="xLh9xmiMuic"

# 服务器上的日志目录
REMOTE_PATH="/c/Users/Administrator/AppData/Local/Programs/Python/crypto_monitor_full/logs"

# 本地保存日志的目录
LOCAL_PATH="$HOME/crypto_monitor_logs"

# =================
# 脚本开始
# =================
# 获取当前时间作为文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "===== 开始同步日志 ====="
echo "时间: $(date)"
echo "从服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo "同步目录: ${REMOTE_PATH}"
echo "保存到本地: ${LOCAL_PATH}"

# 创建本地日志目录
mkdir -p "${LOCAL_PATH}"

# 使用scp下载日志文件（比rsync更适合Windows服务器）
echo -e "\n1. 开始从服务器下载日志文件..."
scp -r "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/*" "${LOCAL_PATH}/"

if [ $? -eq 0 ]; then
    echo "日志文件下载成功"
    
    # 创建带时间戳的目录
    mkdir -p "${LOCAL_PATH}/${TIMESTAMP}"
    
    # 移动所有日志文件到时间戳目录
    mv "${LOCAL_PATH}"/*.log "${LOCAL_PATH}/${TIMESTAMP}/"
    
    # 压缩下载的日志
    echo -e "\n2. 压缩日志文件..."
    cd "${LOCAL_PATH}"
    tar -czf "logs_${TIMESTAMP}.tar.gz" "${TIMESTAMP}"
    
    # 清理临时文件
    rm -rf "${LOCAL_PATH}/${TIMESTAMP}"
    
    echo -e "\n===== 日志同步完成 ====="
    echo "日志文件已保存为: ${LOCAL_PATH}/logs_${TIMESTAMP}.tar.gz"
    echo "你可以使用以下命令查看日志："
    echo "1. 解压日志: tar -xzf ${LOCAL_PATH}/logs_${TIMESTAMP}.tar.gz"
    echo "2. 查看日志: cd ${LOCAL_PATH}/${TIMESTAMP} && ls -l"
else
    echo "错误：日志文件下载失败"
    exit 1
fi 