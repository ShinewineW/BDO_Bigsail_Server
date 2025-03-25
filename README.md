# Flask + PostgreSQL + Docker 部署的卡密系统

### 系统概述
本卡密系统开发基于已经开发完成的一个python程序，该程序现在需要加入卡密系统，以保证客户服务状态以及授权资格。本卡密系统满足如下几点：
1. 所有需要持久化运行的服务和环境都运行在服务器端的docker环境中，以保证快速迁移以及异常还原; 
2. 数据库服务本身运行在docker环境中，数据库文件存储在本地，同时通过 crontab 进行每日备份，备份文件最多保留30天;
3. 数据库分为2个表，分别是卡密表，客户运行环境表
   卡密表：卡密ID，卡密有效期，卡密是否已激活，卡密开始使用时间，卡密过期时间。
   客户运行环境表： 客户硬件信息，客户IP地址，客户发起请求时间，客户使用客户端的功能
   两张表只能以一对一的形式连接，即一个卡密只能对应一个客户，一个客户只能使用一个卡密；
4. 蓝图规则如下：
   客户端在启动的时候，会发出一个带有卡密，IP信息，硬件信息，和当前运行功能的请求报文给服务器，
   服务器在收到请求报文之后，首先检查卡密是否在数据库中，如果在且未激活，则激活卡密，并更新卡密过期时间，如果激活，则判断是否过期。并同时将这个卡密绑定的客户运行环境表更新。 如果卡密不存在，则直接返回错误信息给客户端。 如果卡密已经了一个客户，则检查记录的客户和当前请求客户的  硬件信息和IP地址是否匹配，如果两个都不匹配，则返回错误信息，并将客户发送过来的信息记录在日志中，以备后续分析。
5. 同时如果当前功能为 打开程序， 则返回一个 握手秘钥，给秘钥用于解密客户端的核心数据。
6. 由于暂时无法使用TLS传输，所以为了避免明文http传输，传输前使用了共享秘钥进行对称加密。共享秘钥在服务器端和客户端都存在，并且需要定期更新。

### 技术框架
1. 后端服务与响应框架
    使用Flask/FastAPI框架，Flask/FastAPI框架是Python生态中非常流行的轻量级Web框架，适合构建小型API服务。
2. 数据库框架
    使用 PostgreSQL 数据库，PostgreSQL 以支持小规模并发，以及低负载和高利用率
3. Docker 容器，通过 Docker Compose 进行管理，分别拉起不同的服务，同时保证通信。

### 系统架构、
```
┌─────────────────┐      ┌─────────────────────────────┐
│                 │      │ Docker容器                  │
│  客户端程序     │◄────►│ ┌───────────────────────┐   │
│                 │      │ │ Flask/FastAPI服务     │   │
└─────────────────┘      │ │                       │   │
                         │ │ - 卡密验证            │   │
                         │ │ - 秘钥分发            │   │
                         │ │ - 文件传输（暂缓开发）│   │
                         │ │ - 核心功能执行        │   │
                         │ └───────────┬───────────┘   │
                         └─────────────┼───────────────┘
                                       │
                         ┌─────────────▼───────────────┐
                         │ 宿主机                      │
                         │ ┌───────────────────────┐   │
                         │ │PostgreSQL数据库          │   │
                         │ │                       │   │
                         │ │ - 卡密信息            │   │
                         │ │ - 客户硬件信息        │   │
                         │ │ - IP记录              │   │
                         │ │ - 使用记录            │   │
                         │ └───────────────────────┘   │
                         └───────────────────────────────┘
```

### 数据库结构表
1. 卡密表：
    卡密ID: 32位字符串
    卡密有效期： 日期数据
    卡密是否激活： bool 型
    激活日期： 日期数据
    卡密过期时间： 日期数据
2. 客户信息表：
    客户ID: 32位字符串
    关联卡密ID: 32位字符串
    硬件信息: 字符串
    客户IP地址： 字符串
    客户请求时间： 日期数据
    客户使用功能： 字符串

### 搭建步骤
#### 第一部分： Ubuntu系统初始化
##### 1. 系统更新
```
# 更新软件包列表
sudo apt update

# 升级所有已安装的软件包
sudo apt upgrade -y

# 安装一些基本工具
sudo apt install -y curl wget vim git htop net-tools unzip
```

##### 2. 安装 Docker 和 Docker Compose
```
# 安装必要的依赖
sudo apt install -y apt-transport-https ca-certificates gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 设置 Docker 稳定版仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新软件包索引
sudo apt update

# 安装 Docker Engine
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 将当前用户添加到 docker 组（免 sudo 运行 docker）
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo apt install -y docker-compose-plugin

# 验证安装
docker --version
docker compose version
```

##### 3. 配置防火墙
```
# 安装 UFW（如果尚未安装）
sudo apt install -y ufw

# 设置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许 SSH 连接
sudo ufw allow ssh

# 允许 HTTP 和 HTTPS（如果需要）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许您的应用程序端口（假设是 5000）
sudo ufw allow 5000/tcp

# 启用防火墙
sudo ufw enable

# 检查状态
sudo ufw status
```

##### 4. 安装和配置 PostgreSQL (禁止操作， 因为数据库服务运行在docker中)
```
# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 启动 PostgreSQL 服务并设置为开机自启
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到 postgres 用户
sudo -i -u postgres

# 创建数据库用户和数据库
psql -c "CREATE USER cardadmin WITH PASSWORD 'Aa145150120';"
psql -c "CREATE DATABASE carddb OWNER cardadmin;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE carddb TO cardadmin;"

# 退出 postgres 用户
exit

# 配置 PostgreSQL 允许远程连接（如需要）
# 注意在当前同一宿主机上运行的情况下，并不需要这条命令。
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf

# 重启 PostgreSQL 服务
sudo systemctl restart postgresql
```

##### 5. 配置服务器系统时间
```
# 设置系统时区为上海时间（或您需要的时区）
sudo timedatectl set-timezone Asia/Shanghai

# 安装 NTP 服务保持时间同步
sudo apt install -y ntp

# 启动 NTP 服务并设置为开机自启
sudo systemctl start ntp
sudo systemctl enable ntp
```

##### 6. 为服务器数据库DOCKER容器设置备份策略
```
查看 sripts 中的 backup.sh 文件，将该脚本纳入到 crontab 执行中即可。
```

##### 7. 最后，为服务器进行 https加密，以保护通信过程
```
# 更新软件包
sudo apt update

# 安装 Certbot
sudo apt install -y certbot

# 获取证书 (为两个域名同时申请)
sudo certbot certonly --standalone --preferred-challenges http \
  -d bdobigsail.xyz -d www.bdobigsail.xyz

# 执行完成后，证书会保存在  /etc/letsencrypt/live/bdobigsail.xyz/ 目录下：
<!-- fullchain.pem - 完整证书链 --> /etc/letsencrypt/live/bdobigsail.xyz/fullchain.pem
<!-- privkey.pem - 私钥 --> /etc/letsencrypt/live/bdobigsail.xyz/privkey.pem
```

```
# 将证书保存到项目目录下：
sudo cp /etc/letsencrypt/live/bdobigsail.xyz/fullchain.pem ./https_certificates/
sudo cp /etc/letsencrypt/live/bdobigsail.xyz/privkey.pem ./https_certificates/
sudo chmod -R 775 ./https_certificates/
```
#### 第二部分： 使用docker运行项目
##### 1. 运行项目
```
# 进入项目根目录
cd ./card_auth_system

# 拉起项目
sudo docker compose up --build -d
```

### 可选功能
#### 1. HTTPS传输和TLS加密

由于某些原因，暂时无法使用TLS加密，如下大致阐述一下如何对当前项目执行 nginx 进行反向代理。

```
# 参考 docker-compose-nginx.backup 文件，这是一个带nginx服务的 docker-compose.yml 文件，
# 该文件再拉起一个 nginx 服务，并使用 ./nginx/conf/default.conf 文件作为 nginx 的配置文件,
# 同时将上述申请到的证书挂载到 nginx 服务中，并监听http的80端口，https的443端口。
```

#### 2. 如何定期为域名申请证书
```
# 参考 ./scripts/certbot.sh 文件，这是一个用于申请证书的脚本，
# 该脚本会调用 certbot 命令，并使用 ./https_certificates/fullchain.pem 和 ./https_certificates/privkey.pem 文件作为证书文件，
# 该脚本如果要定期运行，请先使用sudo将脚本 cp到 /usr/local/bin/ 目录下，然后使用 crontab -e 编辑 crontab 文件，将脚本纳入到 crontab 执行中即可。
```


#### 第三部分： 一些脚本文件的说明
##### 1. ./scripts/backup.sh 文件
```
# 该脚本用于为服务器数据库执行备份操作，
# 该脚本会调用 pg_dump 命令，并使用 文件中指定的 目录作为备份文件的存储目录，
# 该脚本没过30天会执行一次数据库本体文件备份，并保留90天。
```

##### 2. ./scripts/renew_cert.sh 文件
```
# 该脚本用于为服务器域名定期执行证书申请操作，
# 该脚本会调用 certbot 命令，并使用 ./https_certificates/fullchain.pem 和 ./https_certificates/privkey.pem 文件作为证书文件，
```

##### 3. ./scripts/generate_cards.sh 文件
```
# 该脚本用于添加指定个数和天数的卡密。
# 并且会将记录保存在  /home/shinewine/card_records 目录下。
```

##### 4. ./scripts/search_databash.txt 文件
```
# 保存了一些简单的查表命令，以在异常时候提供必要的检查。
```





