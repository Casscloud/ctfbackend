import redis


class Config(object):
    """配置信息"""
    SECRET_KEY = "XHSOI*Y9dfs9cshd9"

    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask-session配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # SESSION_USE_SIGNER = True  # 对cookie中session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期，单位秒

    UPLOAD_FOLDER = 'D:/projects/ctfbackend/storage'

# 数据库
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:51638227xX@127.0.0.1:3306/flask_ctf"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

# 邮箱
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'clblctf@163.com'
    MAIL_PASSWORD = 'AGJIPCBQZPXRSJHB'
    MAIL_DEFAULT_SENDER = 'clblctf@163.com'


class DevelopmentConfig(Config):
    """开发模式的配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置信息"""
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}
