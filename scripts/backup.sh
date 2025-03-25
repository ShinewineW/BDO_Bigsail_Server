#!/bin/bash
BACKUP_DIR="/home/shinewine/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR/logical
mkdir -p $BACKUP_DIR/physical

# 逻辑备份（每天）
PGPASSWORD=Aa145150120 docker exec -t card-auth-system-postgres-1 pg_dump -U cardadmin -d carddb > $BACKUP_DIR/logical/carddb_$TIMESTAMP.sql

# 物理备份（每周日）
# if [ $(date +%u) -eq 7 ]; then
#   echo "执行物理备份..."
#   docker-compose -f /path/to/docker-compose.yml stop postgres
#   tar -czf $BACKUP_DIR/physical/postgres_data_$TIMESTAMP.tar.gz -C /path/to /data/postgres
#   docker-compose -f /path/to/docker-compose.yml start postgres
# fi

# 保留最近30天的逻辑备份
find $BACKUP_DIR/logical -type f -name "carddb_*.sql" -mtime +30 -delete

# 保留最近3个月的物理备份
# find $BACKUP_DIR/physical -type f -name "postgres_data_*.tar.gz" -mtime +90 -delete


## 如果需要持续化执行，请依次执行如下命令:
# 1. 移动脚本到 /usr/local/bin/
# 2. 直接执行 
# (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup_db.sh >> /home/shinewine/backups/postgres/cron.log 2>&1") | crontab -
# 3. 最后审查 
# crontab -l

