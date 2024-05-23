# coding:utf-8

from flask import g, current_app, jsonify, request
from flask_restful import Resource
from main import db
from main.model import Problem, UserProblemState, User, Team
from main.utils.commons import login_required, login_or_admin_required, admin_required
from main.utils.constants import URL_DOMAIN
from main.utils.response_code import RET
from sqlalchemy import and_, func


class PmenuResource(Resource):
    # 返回特定类型的题目
    @login_or_admin_required
    def get(self):
        problems = Problem.query.all()
        problem_list = []
        for problem in problems:
            problem_data = {
                'wid': problem.id,
                'tag': problem.tag,
                'name': problem.name,
                'points': problem.points
            }
            problem_list.append(problem_data)
        return jsonify(errno=RET.OK, errmsg="OK", data=problem_list)

    @login_required
    def post(self):
        data = request.get_json()
        tag = data.get("tag")
        problems = Problem.query.filter_by(tag=tag)
        problem_list = []
        for problem in problems:
            problem_data = {
                'wid': problem.id,
                'tag': problem.tag,
                'name': problem.name,
                'points': problem.points
            }
            problem_list.append(problem_data)
        return jsonify(errno=RET.OK, errmsg="OK", data=problem_list)


# 管理员获取题目详情
class AdminProblemResource(Resource):
    @admin_required
    def get(self, wid):
        # 获取单道题目信息
        try:
            problem = Problem.query.get(wid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取题目信息失败")
        if problem is None:
            return jsonify(errno=RET.NODATA, errmsg="无效操作")

        if problem.tag == "web" and problem.link is None:
            problem.link = f'{URL_DOMAIN}/assign/problem/{problem.id}'
        if problem.tag != "web" and problem.link is None:
            problem.link = f'{URL_DOMAIN}/download/{problem.id}'

        # 返回结果json格式
        user_problem_data = {
            'wid': problem.id,
            'tag': problem.tag,
            'name': problem.name,
            'content': problem.content,
            'link': problem.link,
            'points': problem.points,
        }

        return jsonify(errno=RET.OK, errmsg="OK", data=user_problem_data)


class ProblemResource(Resource):
    @login_required
    def get(self, wid):
        user_id = g.user_id
        # 获取单道题目信息
        try:
            problem = Problem.query.get(wid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取题目信息失败")
        if problem is None:
            return jsonify(errno=RET.NODATA, errmsg="无效操作")

        user_problem = UserProblemState.query.filter(and_(
            UserProblemState.user_id == user_id,
            UserProblemState.problem_id == wid
        )).first()
        if user_problem is None:
            try:
                up = UserProblemState(user_id=user_id, problem_id=wid)
                db.session.add(up)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

        try:
            # 查询用户的题目状态
            status = user_problem.status
            # status = db.session.query(UserProblemState). \
            #     join(UserProblemState, UserProblemState.problem_id == wid). \
            #     filter(UserProblemState.user_id == user_id).get('status')
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取题目状态失败")

        if problem.tag == "web" and problem.link is None:
            problem.link = f'{URL_DOMAIN}/assign/problem/{problem.id}'
        if problem.tag != "web" and problem.link is None:
            problem.link = f'{URL_DOMAIN}/download/{problem.id}'

        # 返回结果json格式
        user_problem_data = {
            'wid': problem.id,
            'tag': problem.tag,
            'name': problem.name,
            'content': problem.content,
            'link': problem.link,
            'points': problem.points,
            'status': status
        }

        return jsonify(errno=RET.OK, errmsg="OK", data=user_problem_data)

    @login_required
    def post(self, wid):
        user_id = g.user_id
        user = User.query.get(user_id)
        problem = Problem.query.get(wid)
        # user = User.query.filter_by(id=user_id)
        # problem = Problem.query.filter_by(id=wid)
        user_problem = UserProblemState.query.filter(and_(
                        UserProblemState.user_id == user_id,
                        UserProblemState.problem_id == wid
                    )).first()
        # 获取参数
        req_data = request.get_json()
        if not req_data:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        # 获取参数
        req_dict = request.get_json()
        flag = req_dict.get("flag")

        if problem.flag == flag:

            # 验证是否重复提交
            if user_problem.status == "CORRECT":
                return jsonify(errno=RET.OK, errmsg="作答正确，但不可重复积分")

            try:
                user_problem.query.update({"status": "CORRECT"})
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="题目状态更新失败")
            try:
                user.points += problem.points
                if user.team:
                    user.team.points += problem.points
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="积分更新失败")
            try:
                # 计算排名并将排名信息保存到数据库
                users_with_rank = db.session.query(User, func.rank().over(order_by=User.points.desc()).label('rank')).all()
                for user, rank in users_with_rank:
                    user.rank = rank
                if user.team:
                    # 更新队伍排名
                    teams_with_rank = db.session.query(Team, func.rank().over(order_by=Team.points.desc()).label(
                        't_rank')).all()
                    for team, t_rank in teams_with_rank:
                        team.rank = t_rank

                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="排名更新失败")

            return jsonify(errno=RET.OK, errmsg="作答正确")

        else:
            try:
                user_problem.query.update({"status": "INCORRECT"})
                db.session.commit()
                return jsonify(errno=RET.PARAMERR, errmsg="flag错误")
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="题目状态更新失败")

