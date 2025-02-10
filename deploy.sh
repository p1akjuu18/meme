#!/bin/bash

# 设置环境变量
export PYTHONIOENCODING=utf-8
export LANG=zh_CN.UTF-8

# 停止并删除所有现有程序
pm2 stop all
pm2 delete all

# 启动所有程序（会按照依赖顺序自动启动）
echo "启动所有程序..."
pm2 start ecosystem.config.js

# 监控运行状态
echo "监控程序运行状态..."
pm2 monit 