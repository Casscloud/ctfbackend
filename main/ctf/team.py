# coding:utf-8

from flask import g, current_app, jsonify, request
from sqlalchemy import func

from main import parser, db
from flask_restful import Resource
from main.model import User, Team
from main.utils.commons import login_required
from main.utils.response_code import RET


class TeamResource(Resource):
    @login_required
    def get(self):
        user_id = g.user_id
        # 查询数据库获取团队对象
        try:
            user = User.query.get(user_id)
            team = Team.query.filter_by(name=user.team_name).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取团队信息失败")

        if team is None:
            return jsonify(errno=RET.NODATA, errmsg="尚未加入任何团队")

        team_data = {
            'name': team.name,
            'points': team.points,
            'rank': team.rank,
            'member': [{'username': mem.name} for mem in team.member.all()]
        }

        return jsonify(errno=RET.OK, errmsg="OK", data=team_data)

    @login_required
    def post(self):
        user_id = g.user_id
        # 查询数据库获取团队对象
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

        # 获取参数
        req_data = request.get_json()
        if not req_data:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        args = parser.parse_args()
        action = args['action']

        # 创建队伍
        if action == 'create_team':
            # 用户权限检验
            if user.is_captain is True or user.team_name is not None:
                return jsonify(errno=RET.PARAMERR, errmsg="已有所属队伍，无效操作")

            else:
                name = req_data.get("create_name")  # 创建的团队名
                code = req_data.get("create_code")   # 验证码

                tt = Team.query.filter_by(name=name).first()
                if tt is not None:
                    return jsonify(errno=RET.PARAMERR, errmsg="该名字已被使用，请更换")

                # 创建对象
                team = Team(name=name, code=code, num=1, captain_id=user_id)
                # 保存团队到数据库
                try:
                    db.session.add(team)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(e)
                    return jsonify(errno=RET.DBERR, errmsg="保存团队失败")
                try:
                    team.member.append(user)
                    user.team_name = name
                    user.team_id = team.id
                    user.is_captain = True
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(e)
                    return jsonify(errno=RET.DBERR, errmsg="保存队长失败")

                try:
                    # 更新队伍积分
                    team.points += user.points
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(e)
                    db.session.rollback()
                    return jsonify(errno=RET.DBERR, errmsg="团队分数更新失败")

                try:
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

            return jsonify(errno=RET.OK, errmsg="创建队伍成功")

        # 修改团队名
        elif action == 'change_team_name':
            name = req_data.get("change_name")  # 团队名

            tt = Team.query.filter_by(name=name).first()
            if tt is not None:
                return jsonify(errno=RET.PARAMERR, errmsg="该名字已被使用，请更换")

            try:
                team = Team.query.get(user.team_id)
                users = User.query.filter_by(team_name=user.team_name)
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="查询所属团队失败")
            if team is None:
                return jsonify(errno=RET.PARAMERR, errmsg="您尚未加入队伍，无效操作")

            try:
                team.name = name
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="保存团队名失败")

            try:
                for mem in users:
                    mem.team_name = name
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="更新成员团队名失败")

            return jsonify(errno=RET.OK, errmsg="OK")

        # 成员加入队伍
        elif action == 'join_team':
            if user.is_captain is True or user.team_name is not None:
                return jsonify(errno=RET.PARAMERR, errmsg="您已有所属队伍，无效操作")

            team_name = req_data.get("join_name")  # 团队名称
            code = req_data.get("code")  # 验证码

            team = Team.query.filter_by(name=team_name).first()
            if team is None:
                return jsonify(errno=RET.DATAERR, errmsg="该队伍不存在")

            if code != team.code:
                return jsonify(errno=RET.DATAERR, errmsg="验证码错误")

            # 团队名称
            try:
                user.team_name = team.name
                user.team_id = team.id
                team.num += 1
                team.member.append(user)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="加入队伍失败")

            try:
                team.points += user.points
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="团队分数更新失败")

            try:
                # 更新队伍排名
                teams_with_rank = db.session.query(Team, func.rank().over(order_by=Team.points.desc()).label('t_rank')).all()
                for team, t_rank in teams_with_rank:
                    team.rank = t_rank
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DBERR, errmsg="排名更新失败")

            return jsonify(errno=RET.OK, errmsg="OK")

            # 队长转让队伍
        elif action == 'trans_team':
            # 获取队伍
            team = Team.query.filter_by(name=user.team_name).first()

            if user.is_captain is not True:
                return jsonify(errno=RET.PARAMERR, errmsg="您不是队长，无效操作")

            name = req_data.get("captain_name")  # 新队长用户名
            try:
                captain = User.query.filter_by(name=name).first()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg="该用户不存在")

            if captain in team.member:
                try:
                    user.is_captain = False
                    captain.is_captain = True
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(e)
                    db.session.rollback()
                    return jsonify(errno=RET.DBERR, errmsg="转让队伍失败")
            else:
                return jsonify(errno=RET.DATAERR, errmsg="该用户不是团队成员")

            return jsonify(errno=RET.OK, errmsg="转让队伍成功")

        else:
            return jsonify(errno=RET.PARAMERR, errmsg="请求错误")

    @login_required
    def delete(self):
        user_id = g.user_id
        # 查询数据库获取团队对象
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

        # 成员退出队伍或队长注销队伍
        team = Team.query.filter_by(name=user.team_name).first()

        if team is None:
            return jsonify(errno=RET.PARAMERR, errmsg="尚未加入队伍，无效操作")

        # 如果用户是队长，若没有成员可以直接注销团队，若有成员需要先转让队长身份或者让成员们先退出
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
                    teams_with_rank = db.session.query(Team, func.rank().over(order_by=Team.points.desc()).label(
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
                                               func.rank().over(order_by=Team.points.desc()).label('t_rank')).all()
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
            team.num -= 1
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="退出队伍失败")

        return jsonify(errno=RET.OK, errmsg="OK")
