#!/bin/bash

# 创建日志目录
mkdir -p logs

# 停止所有已存在的进程
pm2 delete all

# 启动所有服务
pm2 start ecosystem.config.js

# 保存 PM2 配置
pm2 save

# 显示运行状态
pm2 status

# 开始监控日志
pm2 logs 