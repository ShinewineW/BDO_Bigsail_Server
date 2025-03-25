from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import redirect, request

# 初始化数据库
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # 创建应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_pyfile('config/settings.py')
    
    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 配置日志
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/card_auth.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Card Auth System startup')
    
    # 注册蓝图
    from app.api.routes import api
    app.register_blueprint(api, url_prefix='/api')
    
    return app
