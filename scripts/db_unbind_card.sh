#!/bin/bash
# 文件: db_unbind_card.sh
# 描述: 直接通过SQL命令解绑卡密的IP和硬件信息
# 用法: ./db_unbind_card.sh <card_key>

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: ./db_unbind_card.sh <card_key>"
    exit 1
fi

CARD_KEY=$1
DB_CONTAINER="card-auth-system-postgres-1"
DB_NAME="carddb"
DB_USER="cardadmin"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# 检查数据库容器是否运行
if ! docker ps | grep -q $DB_CONTAINER; then
    echo "错误: 数据库容器未运行"
    exit 1
fi

# 创建SQL命令
SQL_COMMAND="
-- 开始事务
BEGIN;

-- 记录操作到日志表（如果存在）
DO \$\$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'operation_logs') THEN
        INSERT INTO operation_logs (operation, details, created_at)
        VALUES ('卡密解绑', '卡密: $CARD_KEY', '$TIMESTAMP');
    END IF;
END \$\$;

-- 查找卡密ID并删除相关记录
DO \$\$
DECLARE
    v_card_id INTEGER;
BEGIN
    -- 获取卡密ID
    SELECT id INTO v_card_id FROM cards WHERE card_key = '$CARD_KEY';
    
    IF v_card_id IS NULL THEN
        RAISE NOTICE '卡密 % 不存在', '$CARD_KEY';
    ELSE
        -- 删除usages表中的相关记录
        DELETE FROM usages 
        WHERE user_id IN (SELECT id FROM users WHERE card_id = v_card_id);
        
        -- 删除users表中的记录
        DELETE FROM users 
        WHERE card_id = v_card_id;
        
        RAISE NOTICE '卡密 % 解绑成功', '$CARD_KEY';
    END IF;
END \$\$;

-- 提交事务
COMMIT;

-- 输出操作结果
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM cards WHERE card_key = '$CARD_KEY') 
        THEN '卡密 $CARD_KEY 解绑成功' 
        ELSE '卡密 $CARD_KEY 不存在' 
    END AS result;
"

# 执行SQL命令
echo "正在解绑卡密: $CARD_KEY"
RESULT=$(docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "$SQL_COMMAND")

# 记录操作到日志文件
mkdir -p logs
echo "[$TIMESTAMP] 解绑卡密: $CARD_KEY - 结果: $RESULT" >> logs/unbind_card.log

# 显示结果
echo "$RESULT" | grep -v "^$" | tail -n 1 | sed 's/^ *//;s/ *$//'

# 检查是否包含"成功"字样
if echo "$RESULT" | grep -q "成功"; then
    exit 0
else
    exit 1
fi