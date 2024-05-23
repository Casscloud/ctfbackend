# -*- coding:utf-8 -*-


from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""

    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


class Admin(BaseModel, db.Model):
    """管理"""
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户暱称
    password_hash = db.Column(db.String(256), nullable=False)  # 加密的密码

    # 加上property装饰器后，会把函数变为属性，属性名即为函数名
    @property
    def password(self):
        """读取属性的函数行为"""
        # print(user.password)  # 读取属性时被调用
        # 函数的返回值会作为属性值
        # return "xxxx"
        raise AttributeError("这个属性只能设置，不能读取")

    # 使用这个装饰器, 对应设置属性操作
    @password.setter
    def password(self, value):
        """
        设置属性  user.password = "xxxxx"
        :param value: 设置属性时的数据 value就是"xxxxx", 原始的明文密码
        :return:
        """
        self.password_hash = generate_password_hash(value)

    # def generate_password_hash(self, origin_password):
    #     """对密码进行加密"""
    #     self.password_hash = generate_password_hash(origin_password)

    def check_password(self, passwd):
        """
        检验密码的正确性
        :param passwd:  用户登录时填写的原始密码
        :return: 如果正确，返回True， 否则返回False
        """
        return check_password_hash(self.password_hash, passwd)


class User(BaseModel, db.Model):
    """用户"""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    name = db.Column(db.String(32), nullable=False)  # 用户暱称
    password_hash = db.Column(db.String(256), nullable=False)  # 加密的密码
    email = db.Column(db.String(120), unique=True, nullable=False)  # 邮箱
    real_name = db.Column(db.String(32))  # 真实姓名
    id_card = db.Column(db.String(20))  # 身份证号
    points = db.Column(db.Integer, default=0)  # 用户积分，默认积分为0
    rank = db.Column(db.Integer)  # 用户排名
    is_verified = db.Column(db.Boolean, default=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))  # 队伍编号
    team_name = db.Column(db.String(32))  # 团队
    is_captain = db.Column(db.Boolean, default=False)
    writeup = db.relationship("Writeup", backref="user", foreign_keys='Writeup.user_name')
    problem_states = db.relationship('UserProblemState', backref='user')

    # 加上property装饰器后，会把函数变为属性，属性名即为函数名
    @property
    def password(self):
        """读取属性的函数行为"""
        # print(user.password)  # 读取属性时被调用
        # 函数的返回值会作为属性值
        # return "xxxx"
        raise AttributeError("这个属性只能设置，不能读取")

    # 使用这个装饰器, 对应设置属性操作
    @password.setter
    def password(self, value):
        """
        设置属性  user.password = "xxxxx"
        :param value: 设置属性时的数据 value就是"xxxxx", 原始的明文密码
        :return:
        """
        self.password_hash = generate_password_hash(value)

    # def generate_password_hash(self, origin_password):
    #     """对密码进行加密"""
    #     self.password_hash = generate_password_hash(origin_password)

    def check_password(self, passwd):
        """
        检验密码的正确性
        :param passwd:  用户登录时填写的原始密码
        :return: 如果正确，返回True， 否则返回False
        """
        return check_password_hash(self.password_hash, passwd)


class Team(BaseModel, db.Model):
    """队伍"""
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)  # 队伍编号
    name = db.Column(db.String(32), unique=True, nullable=False)  # 队伍名
    code = db.Column(db.String(32), nullable=False)  # 验证码
    num = db.Column(db.Integer, default=0,)  # 人数，默认为0，最多为10
    points = db.Column(db.Integer, default=0)  # 队伍积分，默认积分为0
    rank = db.Column(db.Integer)  # 队伍排名
    captain_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    member = db.relationship('User', backref='team', foreign_keys='User.team_id', lazy='dynamic')  # 团队成员


class Problem(BaseModel, db.Model):
    """题目"""
    __tablename__ = "problems"
    id = db.Column(db.Integer, primary_key=True)  # 题目编号
    tag = db.Column(db.String(32), nullable=False)  # 题目类型
    name = db.Column(db.String(64), unique=True, nullable=False)  # 题目名
    flag = db.Column(db.String(256), unique=True, nullable=False)  # flag
    content = db.Column(db.String(256), nullable=False)  # 题目内容
    link = db.Column(db.String(256), nullable=True)  # 题目链接
    filename = db.Column(db.String(255), nullable=True)  # 文件名
    file_path = db.Column(db.String(255), nullable=True)  # 题目文件路径
    points = db.Column(db.Integer, default=100, )  # 题目积分，默认积分为100
    writeup = db.relationship("Writeup", backref="problem", foreign_keys='Writeup.problem_name')
    problem_states = db.relationship('UserProblemState', backref='problem')


class Writeup(BaseModel, db.Model):
    """题解"""
    __tablename__ = "writeups"
    id = db.Column(db.Integer, primary_key=True)  # 题解编号
    problem_name = db.Column(db.String(64), db.ForeignKey('problems.name'))
    user_name = db.Column(db.String(32), db.ForeignKey('users.name'))
    tag = db.Column(db.String(32), nullable=False)  # 题解对应题目类型
    name = db.Column(db.String(64), nullable=False)  # 题解标题
    content = db.Column(db.String(1024), nullable=False)  # 题解内容


class UserProblemState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'))
    # Define a field to represent the state (e.g., 'answered', 'correct', 'unanswered')
    status = db.Column(
            db.Enum(
                "UNANSWERED",  # 未作答
                "INCORRECT",  # 不正确
                "CORRECT",  # 正确
            ), default="UNANSWERED")
