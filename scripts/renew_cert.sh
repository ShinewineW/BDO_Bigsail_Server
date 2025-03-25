#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/bdobigsail.xyz/fullchain.pem /home/shinewine/card-auth-system/https_certificates/fullchain.pem
cp /etc/letsencrypt/live/bdobigsail.xyz/privkey.pem /home/shinewine/card-auth-system/https_certificates/privkey.pem
chmod -R 755 /home/shinewine/card-auth-system/https_certificates
docker-compose -f /home/shinewine/card-auth-system/docker-compose.yml restart nginx

# 定期化执行，请运行如下
# 首先修改这个文件的 可执行权限
# chmod +x ./scripts/renew_cert.sh

# 移动到 /usr/local/bin/中
# sudo cp ./scripts/renew_cert.sh /usr/local/bin/

# 然后添加到 crontab 中
# (crontab -l 2>/dev/null; echo "0 0 1 * * /usr/local/bin/renew_cert.sh >> /home/shinewine/card-auth-system/scripts/cert_renewal.log 2>&1") | crontab -
# 最后审查 
# crontab -l

