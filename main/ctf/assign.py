# coding:utf-8
import json
import subprocess
from flask import jsonify, current_app
from flask_restful import Resource

from main.model import Problem
from main.utils.commons import login_required
from main.utils.constants import DOMAIN
from main.utils.response_code import RET


class AssignResource(Resource):
    @login_required
    def get(self, wid):
        problem = Problem.query.get(wid)
        link = f'{problem.filename}'
        return jsonify(errno=RET.OK, errmsg="题目环境部署成功", link=link)

# class AssignResource(Resource):
#     # 动态部署，分配端口
#     @login_required
#     def get(self, wid):
#         problem = Problem.query.get(wid)
#         if problem.file_path:
#             script_path = problem.file_path
#             try:
#                 try:
#                     # 使用 subprocess.Popen 启动脚本
#                     process = subprocess.Popen(["bash", script_path], stdout=subprocess.PIPE,
#                                                stderr=subprocess.PIPE, text=True)
#                 except Exception as e:
#                     current_app.logger.error(e)
#                     return jsonify(errno=RET.PARAMERR, errmsg="运行脚本失败")
#                 # 读取脚本的输出
#                 process.wait()
#                 output = process.stdout.readline()
#                 # 检查输出是否为空
#                 if not output:
#                     return jsonify(errno=RET.PARAMERR, errmsg=f"脚本未输出:{script_path}")
#
#                 # 尝试解析 JSON 输出
#                 try:
#                     output_json = json.loads(output)
#                     allocated_port = output_json.get("next_port")
#                 except json.JSONDecodeError as e:
#                     current_app.logger.error(e)
#                     return jsonify(errno=RET.PARAMERR, errmsg="无法解析脚本输出为 JSON")
#
#                 if allocated_port is not None:
#                     return jsonify(errno=RET.OK, errmsg="题目环境部署成功",
#                                    link=f'{DOMAIN}{allocated_port}')  # 生成的可以访问题目的路由
#                 else:
#                     return jsonify(errno=RET.PARAMERR, errmsg="无输出端口")
#
#             except Exception as e:
#                 current_app.logger.error(e)
#                 return jsonify(errno=RET.PARAMERR, errmsg="题目环境部署失败")
#         else:
#             return jsonify(errno=RET.DBERR, errmsg="查询题目脚本错误")

