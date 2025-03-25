#!/bin/bash
BACKUP_DIR="/home/shinewine/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR/logical
mkdir -p $BACKUP_DIR/physical

# 记录开始时间和备份信息
echo "开始数据库备份 - $(date)" >> $BACKUP_DIR/backup.log

# 逻辑备份（每天）- 添加 -v 参数获取详细输出
echo "执行逻辑备份..." >> $BACKUP_DIR/backup.log
PGPASSWORD=Aa145150120 docker exec -t card-auth-system-postgres-1 pg_dump -U cardadmin -d carddb -v > $BACKUP_DIR/logical/carddb_$TIMESTAMP.sql 2>> $BACKUP_DIR/backup.log
echo "逻辑备份完成，文件：carddb_$TIMESTAMP.sql" >> $BACKUP_DIR/backup.log

# 物理备份（每周日）
if [ $(date +%u) -eq 7 ]; then
  echo "执行物理备份..." >> $BACKUP_DIR/backup.log
  # 使用正确的容器名称和docker-compose文件路径
  docker-compose -f /home/shinewine/card-auth-system/docker-compose.yml stop postgres
  # 使用正确的数据目录路径
  tar -czf $BACKUP_DIR/physical/postgres_data_$TIMESTAMP.tar.gz -C /home/shinewine/card-auth-system/data postgres
  docker-compose -f /home/shinewine/card-auth-system/docker-compose.yml start postgres
  echo "物理备份完成，文件：postgres_data_$TIMESTAMP.tar.gz" >> $BACKUP_DIR/backup.log
fi

# 保留最近30天的逻辑备份
echo "清理过期逻辑备份..." >> $BACKUP_DIR/backup.log
find $BACKUP_DIR/logical -type f -name "carddb_*.sql" -mtime +30 -delete

# 保留最近3个月的物理备份
echo "清理过期物理备份..." >> $BACKUP_DIR/backup.log
find $BACKUP_DIR/physical -type f -name "postgres_data_*.tar.gz" -mtime +90 -delete

echo "备份过程完成 - $(date)" >> $BACKUP_DIR/backup.log
echo "----------------------------------------" >> $BACKUP_DIR/backup.log


## 如果需要持续化执行，请依次执行如下命令:
# 1. 移动脚本到 /usr/local/bin/
# sudo cp ./scripts/backup.sh /usr/local/bin/backup.sh
# sudo chmod +x /usr/local/bin/backup.sh
# 2. 添加到 root 的 crontab 以确保有足够权限
# sudo sh -c '(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup.sh >> /home/shinewine/backups/postgres/cron.log 2>&1") | crontab -'
# 3. 最后审查 
# sudo crontab -l

