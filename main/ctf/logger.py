# coding:utf-8

from flask_restful import Resource
from flask import current_app


class LogResource(Resource):
    @staticmethod
    def get():
        current_app.logger.error("error info")  # 记录错误信息
        current_app.logger.warning("warn info")  # 警告
        current_app.logger.info("info info")  # 信息
        current_app.logger.debug("debug info")  # 调试
        return "index page"
