# coding:utf-8
import os

from flask import jsonify, send_from_directory, send_file
from flask_restful import Resource

import config
from main.model import Problem
from main.utils.commons import login_required
from main.utils.response_code import RET


class FileResource(Resource):
    @login_required
    def get(self, wid):
        problem = Problem.query.get(wid)

        if problem and problem.file_path:
            return send_file(problem.file_path)
            # return send_from_directory(config.Config.UPLOAD_FOLDER, os.path.basename(problem.file_path),
            #                            as_attachment=True)
        else:
            return jsonify(errno=RET.DBERR, errmsg="下载文件失败")
