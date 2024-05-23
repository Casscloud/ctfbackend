# coding:utf-8
from flask_mail import Message
from flask import jsonify, request, current_app, session
import re
from flask_restful import Resource
from main import db, serializer, redis_store
from main.model import User, Admin
from main.utils import constants
from main.utils.constants import URL_DOMAIN
from main.utils.response_code import RET


class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        real_name = data.get('real_name')  # 真实姓名
        id_card = data.get('id_card')  # 身份证号
        name = data.get('name')
        email = data.get('email')
        password = data.get("password")
        password2 = data.get("password2")

        # 校验参数
        if not all([email, password, password2, real_name, id_card, name]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
        # 判断邮箱是否为空
        if not email:
            return jsonify(errno=RET.PARAMERR, errmsg="邮箱不能为空")
        # 判断邮箱是否已注册
        ee = User.query.filter_by(email=email).first()
        if ee:
            return jsonify(errno=RET.DATAEXIST, errmsg="邮箱已经被注册")
        # 判断邮箱格式
        if not re.match(r"^[\w\\.-]+@[\w\\.-]+\.\w+$", email):
            # 表示格式不对
            return jsonify(errno=RET.PARAMERR, errmsg="邮箱格式错误")
        if not re.match(r"^\d17}(\d|X|x)$", id_card):
            return jsonify(errno=RET.PARAMERR, errmsg="身份证号无效")
        # 判断密码是否输入一致
        if password != password2:
            return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

        try:
            # 生成验证链接
            token = serializer.dumps(email, salt='email-confirmation')
            confirm_url = f'{URL_DOMAIN}/confirm/{token}'  # 注意部署后需要替换为前端的URL

            # 发送验证邮箱
            mail = current_app.extensions.get('mail')
            msg = Message('邮箱验证', recipients=[email])
            print(msg)
            msg.body = f'请点击以下链接完成邮箱验证: {confirm_url}'

            mail.send(msg)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.MAILERR, errmsg="邮件发送失败")

        user = User(name=name, email=email, real_name=real_name, id_card=id_card)
        user.password = password  # 设置属性
        # 保存用户到数据库
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

        # 返回通知
        return jsonify(errno=RET.OK, errmsg="验证邮件已发送，请检查您的邮箱")


# 处理邮箱验证链接
class ConfirmResource(Resource):
    def get(self, token):
        try:
            email = serializer.loads(token, salt='email-confirmation', max_age=3600)  # 一小时内有效
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_verified = True
                db.session.commit()
                return jsonify(errno=RET.OK, errmsg="邮箱验证成功")
            else:
                return jsonify(errno=RET.MAILERR, errmsg="邮箱验证失败")
        except:
            return jsonify(errno=RET.TIMERR, errmsg="您的验证链接已过期")


class LoginResource(Resource):
    def post(self):
        """用户登录
            参数： 邮箱、密码， json
            """
        # 获取参数
        req_dict = request.get_json()
        email = req_dict.get("email")
        password = req_dict.get("password")

        # 校验参数
        # 参数完整的校验
        if not all([email, password]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

        # 邮箱的格式
        if not re.match(r'^[\w\\.-]+@[\w\\.-]+\.\w+$', email):
            return jsonify(errno=RET.PARAMERR, errmsg="邮箱格式错误")

        # 判断错误次数是否超过限制，如果超过限制，则返回
        # redis记录： "access_nums_请求的ip": "次数"
        user_ip = request.remote_addr  # 用户的ip地址
        try:
            access_nums = redis_store.get("access_num_%s" % user_ip)
        except Exception as e:
            current_app.logger.error(e)
        else:
            if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
                return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

        # 从数据库中根据邮箱查询用户的数据对象
        try:
            user = User.query.filter_by(email=email).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")
        if user is None:
            return jsonify(errno=RET.DATAERR, errmsg="用户不存在，请先完成注册")

        if user.is_verified is False:
            return jsonify(errno=RET.PARAMERR, errmsg="请先完成邮箱验证")

        # 用数据库的密码与用户填写的密码进行对比验证
        if not user.check_password(password):
            # 如果验证失败，记录错误次数，返回信息
            try:
                # redis的incr可以对字符串类型的数字数据进行加一操作，如果数据一开始不存在，则会初始化为1
                redis_store.incr("access_num_%s" % user_ip)
                redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
            except Exception as e:
                current_app.logger.error(e)

            return jsonify(errno=RET.DATAERR, errmsg="邮箱或密码错误")

        try:
            # 如果验证相同成功，保存登录状态， 在session中
            session["name"] = user.name
            session["user_id"] = user.id
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.SESSIONERR, errmsg="登陆失败")

        return jsonify(errno=RET.OK, errmsg="登录成功")

    def get(self):
        """检查登陆状态"""
        # 尝试从session中获取用户的名字
        user_id = session.get("user_id")
        # 如果session中数据name名字存在，则表示用户已登录，否则未登录
        if user_id is not None:
            return jsonify(errno=RET.OK, errmsg="true")
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="false")

    def delete(self):
        """登出"""
        # 清除session数据
        session.clear()
        return jsonify(errno=RET.OK, errmsg="OK")


class AdminLoginResource(Resource):
    def post(self):
        """管理员登录
            参数： 用户名、密码， json
            """
        # 获取参数
        req_dict = request.get_json()
        name = req_dict.get("name")
        password = req_dict.get("password")

        # 校验参数
        # 参数完整的校验
        if not all([name, password]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

        # 判断错误次数是否超过限制，如果超过限制，则返回
        # redis记录： "access_nums_请求的ip": "次数"
        admin_ip = request.remote_addr  # 管理员的ip地址

        try:
            access_nums = redis_store.get("access_num_%s" % admin_ip)
        except Exception as e:
            current_app.logger.error(e)
        else:
            if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
                return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

        # 从数据库中根据邮箱查询用户的数据对象
        try:
            admin = Admin.query.filter_by(name=name).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取管理员信息失败")
        if admin is None:
            return jsonify(errno=RET.DATAERR, errmsg="此管理员不存在，无效操作")

        # 用数据库的密码与用户填写的密码进行对比验证
        if not admin.check_password(password):
            # 如果验证失败，记录错误次数，返回信息
            try:
                # redis的incr可以对字符串类型的数字数据进行加一操作，如果数据一开始不存在，则会初始化为1
                redis_store.incr("access_num_%s" % admin_ip)
                redis_store.expire("access_num_%s" % admin_ip, constants.LOGIN_ERROR_FORBID_TIME)
            except Exception as e:
                current_app.logger.error(e)

            return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

        # 如果验证相同成功，保存登录状态， 在session中
        session["admin_id"] = admin.id

        return jsonify(errno=RET.OK, errmsg="登录成功")

    def get(self):
        """检查登陆状态"""
        # 尝试从session中获取用户的名字
        admin_id = session.get("admin_id")
        # 如果session中数据name名字存在，则表示用户已登录，否则未登录
        if admin_id is not None:
            return jsonify(errno=RET.OK, errmsg="true")
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="false")

    def delete(self):
        """登出"""
        # 清除session数据
        session.clear()
        return jsonify(errno=RET.OK, errmsg="OK")
