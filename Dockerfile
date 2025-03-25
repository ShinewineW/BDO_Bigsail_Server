FROM python:3.9-slim

# 为PIP换源，替换为清华镜像源
RUN python -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --upgrade pip
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app/main.py

# 暴露端口
EXPOSE 5000

# 启动命令 - 移除SSL配置
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app"]