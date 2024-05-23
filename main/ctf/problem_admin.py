# coding:utf-8
import os

from flask import current_app, jsonify, request
from flask_restful import Resource

from config import Config
from main import db
from main.model import Problem, UserProblemState
from main.utils.commons import admin_required
from main.utils.response_code import RET
from werkzeug.utils import secure_filename


class AdminResource(Resource):
    # 添加题目
    # @admin_required
    # def post(self):
    #     req_data = request.get_json()
    #     tag = req_data.get("tag")
    #     name = req_data.get("name")
    #     flag = req_data.get("flag")
    #     content = req_data.get("content")
    #     points = req_data.get("points")
    #     file_path = req_data.get("file_path")
    #     problem = Problem(tag=tag, name=name, flag=flag, file_path=file_path, content=content, points=points)
    #     # 保存题目到数据库
    #     try:
    #         db.session.add(problem)
    #         db.session.commit()
    #     except Exception as e:
    #         db.session.rollback()
    #         current_app.logger.error(e)
    #         return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")
    #     return jsonify(errno=RET.OK, errmsg="保存题目成功")


    @admin_required
    def post(self):
        # req_data = request.get_json()
        req_data = request.form.to_dict()
        tag = req_data.get("tag")
        name = req_data.get("name")
        flag = req_data.get("flag")
        content = req_data.get("content")
        points = req_data.get("points")

        if not tag:
            return jsonify(errno=RET.DBERR, errmsg="未接收到数据")

        if tag == "web":
            file_path = req_data.get("link")
            problem = Problem(tag=tag, name=name, flag=flag, file_path=file_path, content=content, points=points)
            # 保存题目到数据库
            try:
                db.session.add(problem)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")
        else:
            if 'file' not in request.files:
                return jsonify(errno=RET.NODATA, errmsg="未上传文件")

            file = request.files['file']

            if file.filename == '':
                return jsonify(errno=RET.NODATA, errmsg="未选择文件")
            # 注意文件名只能是英文
            if file:
                try:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                    file.save(file_path)
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(e)
                    return jsonify(errno=RET.FILERR, errmsg="上传文件失败")

                problem = Problem(tag=tag, name=name, flag=flag, content=content, filename=filename,
                                  file_path=file_path, points=points)
                # 保存题目到数据库
                try:
                    db.session.add(problem)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(e)
                    return jsonify(errno=RET.DBERR, errmsg="保存题目失败")

        return jsonify(errno=RET.OK, errmsg="保存题目成功")


class DeleteResource(Resource):
    # 删除题目
    @admin_required
    def delete(self, wid):
        # 查询出要删除的题目
        try:
            problem = Problem.query.get(wid)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询题目异常")
        if problem is None:
            return jsonify(errno=RET.DATAERR, errmsg="该题目不存在或已被删除")

        # 查询题目状态数据
        try:
            user_problems = UserProblemState.query.filter_by(problem_id=wid).all()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询题目状态异常")

        # 删除题目状态数据
        try:
            for user_problem in user_problems:
                db.session.delete(user_problem)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="删除题目状态数据失败")

        if problem.file_path is not None:
            try:
                # 删除文件
                file_path = problem.file_path
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.FILERR, errmsg="删除文件失败")

        # 删除题目
        try:
            db.session.delete(problem)
            db.session.commit()  # 提交更改
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="删除题目失败")

        return jsonify(errno=RET.OK, errmsg="删除题目成功")
