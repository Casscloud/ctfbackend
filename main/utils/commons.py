from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from main.utils.response_code import RET
import functools


# 定义正则转换器
class ReConverter(BaseConverter):
    """"""
    def __init__(self, url_map, regex):
        # 调用父类的初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# 定义的验证登录状态的装饰器
def login_required(view_func):
    # wraps函数的作用是将wrapper内层函数的属性设置为被装饰函数view_func的属性
    @functools.wraps(view_func)  # 不改变被装饰函数的属性相关
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        user_id = session.get("user_id")

        # 如果用户是登录的， 执行视图函数
        if user_id is not None:
            # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存数据
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 如果未登录，返回未登录的信息
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    return wrapper


# 定义验证登管理员登录状态的装饰器
def admin_required(view_func):
    # wraps函数的作用是将wrapper内层函数的属性设置为被装饰函数view_func的属性
    @functools.wraps(view_func)  # 不改变被装饰函数的属性相关
    def wrapper(*args, **kwargs):
        # 判断管理员的登录状态
        admin_id = session.get("admin_id")

        # 如果管理员是登录的， 执行视图函数
        if admin_id is not None:
            # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存数据
            g.admin_id = admin_id
            return view_func(*args, **kwargs)
        else:
            # 如果未登录，返回未登录的信息
            return jsonify(errno=RET.ADMINERR, errmsg="管理员未登录，无效操作")

    return wrapper


def login_or_admin_required(view_func):
    # wraps函数的作用是将wrapper内层函数的属性设置为被装饰函数view_func的属性
    @functools.wraps(view_func)  # 不改变被装饰函数的属性相关
    def wrapper(*args, **kwargs):
        # 判断管理员的登录状态
        user_id = session.get("user_id")
        admin_id = session.get("admin_id")

        # 如果管理员是登录的， 执行视图函数
        if admin_id is not None:
            # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存数据
            g.admin_id = admin_id
            return view_func(*args, **kwargs)
        else:
            if user_id is not None:
                # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存数据
                g.user_id = user_id
                return view_func(*args, **kwargs)
            else:
                # 如果未登录，返回未登录的信息
                return jsonify(errno=RET.ADMINERR, errmsg="未登录，无效操作")

    return wrapper