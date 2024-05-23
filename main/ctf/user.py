# coding:utf-8

from flask import g, current_app, jsonify, request, session
from flask_mail import Message
from sqlalchemy import func
from main import parser, db, serializer
from flask_restful import Resource
import re
from main.model import User, Team, UserProblemState
from main.utils.commons import login_required
from main.utils.constants import URL_DOMAIN
from main.utils.response_code import RET


class UserResource(Resource):
    @login_required
    def get(self):
        user_id = g.user_id
        # 查询数据库获取个人信息
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

        if user is None:
            return jsonify(errno=RET.NODATA, errmsg="无效操作")

        user_data = {
            'name': user.name,
            'password': 'invisible',
            'email': user.email,
            'real_name': user.real_name,
            'id_card': 'invisible',
            'points': user.points,
            'rank': user.rank,
            'team': user.team_name
        }
        return jsonify(errno=RET.OK, errmsg="OK", data=user_data)

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

        if action == 'change_information':
            name = req_data.get("name")  # 用户名
            if name != user.name:
                try:
                    user.name = name
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(e)
                    db.session.rollback()
                    return jsonify(errno=RET.DBERR, errmsg="保存用户名失败")
                # return jsonify(errno=RET.OK, errmsg="OK")

        # elif action == 'change_identity':
            real_name = req_data.get("real_name")  # 真实姓名
            id_card = req_data.get("id_card")  # 身份证号

            # 参数校验
            if not all([real_name, id_card]):
                return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

            # 保存用户的姓名与身份证号
            try:
                User.query.filter_by(id=user_id).update({"real_name": real_name, "id_card": id_card})
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")

            return jsonify(errno=RET.OK, errmsg="OK")

        elif action == 'change_password':
            password_old = req_data.get("password_old")  # 原密码
            password_new = req_data.get("password_new")  # 新密码

            # 参数校验,两个变量需完整
            if not all([password_old, password_new]):
                return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

            # 验证原密码并修改密码
            if user.check_password(password_old):
                try:
                    user.password = password_new
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(e)
                    db.session.rollback()
                    return jsonify(errno=RET.DBERR, errmsg="修改密码失败")

                return jsonify(errno=RET.OK, errmsg="OK")
            return jsonify(errno=RET.PARAMERR, errmsg="密码错误")

        elif action == 'change_email':
            email = req_data.get("email")  # 邮箱

            # 判断邮箱是否已注册
            ee = User.query.filter_by(email=email).first()
            if ee:
                return jsonify(errno=RET.DATAEXIST, errmsg="邮箱已经被注册")
            # 判断邮箱格式
            if not re.match(r"^[\w\\.-]+@[\w\\.-]+\.\w+$", email):
                # 表示格式不对
                return jsonify(errno=RET.PARAMERR, errmsg="邮箱格式错误")

            try:
                # 生成验证链接
                token = serializer.dumps(email, salt='email-confirmation')
                confirm_url = f'{URL_DOMAIN}/confirm/{token}'  # 替换为前端的URL

                # 发送验证邮箱
                mail = current_app.extensions.get('mail')
                msg = Message('邮箱验证', recipients=[email])
                msg.body = f'请点击以下链接完成邮箱验证: {confirm_url}'
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.MAILERR, errmsg="验证邮件发送失败")

            try:
                user.email = email
                user.is_verified = False
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="邮箱更新失败")
            return jsonify(errno=RET.OK, errmsg="验证邮件已发送，请检查您的邮箱。若填错邮箱，请不要登出，重新填写邮箱。")

        # elif action == 'change_avatar':
        #     #参数： 图片(多媒体表单格式)
        #     # 获取图片
        #     image_file = request.files.get("avatar")
        #
        #     if image_file is None:
        #         return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")
        #
        #     image_data = image_file.read()
        #
        #     # 上传图片, 返回文件名
        #     try:
        #         file_name = storage(image_data)               #注意这个函数还没写！！！
        #     except Exception as e:
        #         current_app.logger.error(e)
        #         return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")
        #
        #     # 保存文件名到数据库中
        #     try:
        #         user.update({"avatar": file_name})
        #         db.session.commit()
        #     except Exception as e:
        #         db.session.rollback()
        #         current_app.logger.error(e)
        #         return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")
        #
        #     avatar_url = constants.URL_DOMAIN + file_name
        #     # 保存成功返回
        #     return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})

        else:
            return jsonify(errno=RET.PARAMERR, errmsg="请求错误")

    # 用户注销
    @login_required
    def delete(self):
        user_id = g.user_id
        user = User.query.get(user_id)
        if user:
            if user:
                team = Team.query.filter_by(name=user.team_name).first()
                if team:
                    if user.is_captain is True:
                        if team.num == 1:
                            try:
                                db.session.delete(team)
                                user.team_id = None
                                user.is_captain = False
                                user.team_name = None
                                db.session.commit()  # 提交更改
                            except Exception as e:
                                current_app.logger.error(e)
                                db.session.rollback()
                                return jsonify(errno=RET.DBERR, errmsg="注销团队失败")

                            try:
                                # 更新队伍排名
                                teams_with_rank = db.session.query(Team,
                                                                   func.rank().over(order_by=Team.points.desc()).label(
                                                                       't_rank')).all()
                                for team, t_rank in teams_with_rank:
                                    team.rank = t_rank
                                db.session.commit()
                            except Exception as e:
                                current_app.logger.error(e)
                                db.session.rollback()
                                return jsonify(errno=RET.DBERR, errmsg="排名更新失败")

                            return jsonify(errno=RET.OK, errmsg="注销队伍成功")

                        return jsonify(errno=RET.PARAMERR, errmsg="您是该队伍的队长，请先转让队长")

                    # 成员退出队伍
                    try:
                        # 更新团队分数
                        team.points -= user.points
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(e)
                        db.session.rollback()
                        return jsonify(errno=RET.DBERR, errmsg="团队分数更新失败")

                    # 更新队伍排名
                    try:
                        teams_with_rank = db.session.query(Team,
                                                           func.rank().over(order_by=Team.points.desc()).label(
                                                               't_rank')).all()
                        for team, t_rank in teams_with_rank:
                            team.rank = t_rank
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(e)
                        db.session.rollback()
                        return jsonify(errno=RET.DBERR, errmsg="排名更新失败")

                    try:
                        user.team_name = None
                        user.team_id = None
                        team.member.remove(user)
                        team.num = team.num-1
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(e)
                        db.session.rollback()
                        return jsonify(errno=RET.DBERR, errmsg="退出队伍失败")
                    


            # 查询题目状态数据
            try:
                user_problems = UserProblemState.query.filter_by(user_id=user_id).all()
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

            try:
                db.session.delete(user)  # 删除用户记录
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="用户注销失败")

        session.clear()  # 删除会话数据
        return jsonify(errno=RET.OK, errmsg="用户注销成功")


# class RankResource(Resource):
#     @login_required
#     def get(self, type):
#         if type == 'users':
#             # 从数据库中获取用户数据，并进行排序和排名
#             try:
#                 user_points = User.query.order_by(User.points.desc()).filter_by(is_verified=True)
#             except Exception as e:
#                 current_app.logger.error(e)
#                 return jsonify(errno=RET.DBERR, errmsg="获取用户排名失败")
#             ranked_users = [{'name': user.name, 'points': user.points, 'rank': user.rank}
#                             for user in user_points]
#             return jsonify(errno=RET.OK, errmsg="OK", data=ranked_users)
#
#         elif type == 'teams':
#             # 获取队伍积分信息
#             try:
#                 team_points = Team.query.order_by(Team.points.desc()).all()
#             except Exception as e:
#                 current_app.logger.error(e)
#                 return jsonify(errno=RET.DBERR, errmsg="获取团队排名失败")
#             ranked_teams = [{'name': team.name, 'points': team.points, 'rank': team.rank}
#                             for team in team_points]
#             return jsonify(errno=RET.OK, errmsg="OK", data=ranked_teams)

class RankResource(Resource):
    @login_required
    def get(self, type):
        if type == 'users':
            try:
                # 计算排名并将排名信息保存到数据库
                users_with_rank = db.session.query(User, func.rank().over(order_by=User.points.desc()).label('rank')).all()
                for user, rank in users_with_rank:
                    user.rank = rank
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="用户排名更新失败")
            # 从数据库中获取用户数据，并进行排序和排名
            try:
                user_points = User.query.order_by(User.points.desc()).filter_by(is_verified=True)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="获取用户排名失败")
            ranked_users = [{'name': user.name, 'points': user.points, 'rank': user.rank}
                            for user in user_points]
            return jsonify(errno=RET.OK, errmsg="OK", data=ranked_users)

        elif type == 'teams':
            try:
                # 更新队伍排名
                teams_with_rank = db.session.query(Team, func.rank().over(order_by=Team.points.desc()).label('t_rank')).all()
                for team, t_rank in teams_with_rank:
                    team.rank = t_rank
                    db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="队伍排名更新失败")
            # 获取队伍积分信息
            try:
                team_points = Team.query.order_by(Team.points.desc()).all()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="获取团队排名失败")
            ranked_teams = [{'name': team.name, 'points': team.points, 'rank': team.rank}
                            for team in team_points]
            return jsonify(errno=RET.OK, errmsg="OK", data=ranked_teams)

