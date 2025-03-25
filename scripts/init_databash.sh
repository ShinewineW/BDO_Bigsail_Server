#!/bin/bash

# 初始化数据库脚本
echo "开始初始化数据库..."

# 进入Docker容器并运行初始化脚本
docker exec -it $(docker ps -qf "name=card-auth-system-web-1") python -m scripts.init_db

echo "数据库初始化完成！"