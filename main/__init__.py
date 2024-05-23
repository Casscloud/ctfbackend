# coding:utf-8

from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
# from flask_wtf import CSRFProtect
from flask import Flask
from flask_restful import reqparse
from config import config_map, Config
import redis
import logging
from logging.handlers import RotatingFileHandler
from itsdangerous import URLSafeTimedSerializer
from main.utils.commons import ReConverter

# 数据库
db = SQLAlchemy()

# 创建redis连接对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# 创建序列化器
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)

# 创建参数解析器
parser = reqparse.RequestParser()
parser.add_argument('action', type=str, required=False, help='Action parameter is required.')
# parser.add_argument('file', type=str, required=False, help='File parameter is required.')
# parser.add_argument('type', type=str, required=False, help='Type parameter is required.')

# 配置日志信息
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/logs", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日记录器
logging.getLogger().addHandler(file_log_handler)
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级


# 工厂模式
def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name: str  配置模式的模式的名字 （"develop",  "product"）
    :return:
    """
    app = Flask(__name__)

    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    # 根据配置模式的名字获取配置参数的类
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 使用app初始化db
    db.init_app(app)

    # 利用flask-session，将session数据保存到redis中
    Session(app)

    # 为flask补充csrf防护
    # CSRFProtect(app)

    # 为flask添加自定义的转换器
    app.url_map.converters["re"] = ReConverter

    return app
