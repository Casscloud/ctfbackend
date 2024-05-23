# coding:utf-8

from flask import g, current_app, jsonify, request
from flask_restful import Resource
from main import db, parser
from main.model import User, Writeup
from main.utils.commons import login_required
from main.utils.response_code import RET


class WmenuResource(Resource):
    # 返回全部writeup目录
    @login_required
    def get(self):
        writeups = Writeup.query.all()
        writeup_list = []
        for writeup in writeups:
            writeup_data = {
                'id': writeup.id,
                'tag': writeup.tag,
                'name': writeup.name,
                'auther': writeup.user_name,
                'update_time': writeup.update_time
            }
            writeup_list.append(writeup_data)
        return jsonify(errno=RET.OK, errmsg="OK", data=writeup_list)

    # # 搜索返回全部特定writeup目录
    # @login_required
    # def post(self):
    #     req_data = request.get_json()
    #     keyword = req_data.get('keyword')  # 获取搜索关键字
    #     try:
    #         writeups = Writeup.query.filter(Writeup.name.contains(keyword)).all()  # 在数据库中查询包含关键字的题解
    #     except Exception as e:
    #         current_app.logger.error(e)
    #         return jsonify(errno=RET.DBERR, errmsg="调取题解失败")
    #     writeup_list = []
    #     for writeup in writeups:
    #         writeup_data = {
    #             'id': writeup.id,
    #             'tag': writeup.tag,
    #             'name': writeup.name,
    #             'auther': writeup.user_name,
    #             'update_time': writeup.update_time
    #         }
    #         writeup_list.append(writeup_data)
    #     return jsonify(errno=RET.OK, errmsg="OK", data=writeup_list)


class WriteupResource(Resource):
    @login_required
    def get(self, id):
        # 查看题解内容，单个题解具体内容
        try:
            writeup = Writeup.query.get(id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取题解失败")

        writeup_data = {
            'id': writeup.id,
            'tag': writeup.tag,
            'name': writeup.name,
            'auther': writeup.user_name,
            'content': writeup.content,
            'problem_name': writeup.problem_name,
            'update_time': writeup.update_time
        }
        return jsonify(errno=RET.OK, errmsg="OK", data=writeup_data)


class MyWriteupResource(Resource):
    # 查看个人发布题解
    @login_required
    def get(self):
        user_id = g.user_id
        user = User.query.get(user_id)

        try:
            writeups = Writeup.query.filter_by(user_name=user.name).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取个人题解列表失败")
        writeup_list = []
        for writeup in writeups:
            writeup_data = {
                'id': writeup.id,
                'tag': writeup.tag,
                'name': writeup.name,
                'auther': writeup.user_name,
                'update_time': writeup.update_time
            }
            writeup_list.append(writeup_data)
        return jsonify(errno=RET.OK, errmsg="OK", data=writeup_list)

    @login_required
    def post(self):
        user_id = g.user_id
        user = User.query.get(user_id)
        # 获取参数
        req_data = request.get_json()
        if not req_data:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        args = parser.parse_args()
        action = args['action']

        # 修改题解
        if action == "change_my_writeup":
            id = req_data.get("id")
            tag = req_data.get("tag").lower()
            name = req_data.get("name")
            problem_name = req_data.get("problem_name")
            content = req_data.get("content")
            try:
                writeup = Writeup.query.get(id)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="修改目标对象获取失败")
            if writeup.user_name != user.name:
                return jsonify(errno=RET.PARAMERR, errmsg="非发布者，无效操作")
            try:
                writeup.name = name
                writeup.content = content
                writeup.problem_name = problem_name
                writeup.tag = tag
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="保存题解失败,请检查对应题目是否错误")
            return jsonify(errno=RET.OK, errmsg="修改题解成功")

        elif action == "add_my_writeup":

            tag = req_data.get("tag").lower()
            name = req_data.get("name")
            problem_name = req_data.get("problem_name")
            content = req_data.get("content")

            writeup = Writeup(tag=tag, name=name, content=content, problem_name=problem_name, user_name=user.name)
            try:
                db.session.add(writeup)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="发布题解失败")

            return jsonify(errno=RET.OK, errmsg="发布题解成功")

        elif action == "delete_my_writeup":
            id = req_data.get("id")
            writeup = Writeup.query.get(id)
            if writeup.user_name != user.name:
                return jsonify(errno=RET.PARAMERR, errmsg="非发布者，无效操作")
            try:
                db.session.delete(writeup)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="删除题解失败")
            return jsonify(errno=RET.OK, errmsg="删除题解成功")
