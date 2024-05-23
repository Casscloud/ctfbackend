# coding:utf-8

from flask_mail import Mail
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS


from main import create_app, db
from main.ctf.assign import AssignResource
from main.ctf.file import FileResource
from main.ctf.logger import LogResource
from main.ctf.port import RegisterResource, LoginResource, ConfirmResource, AdminLoginResource
from main.ctf.problem import ProblemResource, PmenuResource, AdminProblemResource
from main.ctf.problem_admin import AdminResource, DeleteResource
from main.ctf.team import TeamResource
from main.ctf.user import UserResource, RankResource
from main.ctf.writeup import WriteupResource, WmenuResource, MyWriteupResource

# 创建flask的应用对象
app = create_app("develop")

# CORS(app, origins=['http://localhost:4200'],
#          methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
#          #  llow_headers=['Content-Type', 'Authorization'],
#          #  expose_headers='Custom-Header',
#          supports_credentials=True,
#          max_age=3600)

Migrate(app, db)

mail = Mail(app)

api = Api(app)


api.add_resource(LogResource, '/index')
api.add_resource(RegisterResource, '/register')
api.add_resource(ConfirmResource, '/confirm/<token>')
api.add_resource(LoginResource, '/session')
api.add_resource(UserResource, '/user')
api.add_resource(PmenuResource, '/problem_menu')
api.add_resource(ProblemResource, '/problem/<string:wid>')
api.add_resource(RankResource, '/rank/<type>')
api.add_resource(TeamResource, '/team')
api.add_resource(WmenuResource, '/writeup_menu')
api.add_resource(WriteupResource, '/writeup/<string:id>')
api.add_resource(MyWriteupResource, '/writeup/my_writeup')
api.add_resource(FileResource, '/download/<string:wid>')
api.add_resource(AssignResource, '/assign/problem/<string:wid>')
api.add_resource(AdminLoginResource, '/admin/session')
api.add_resource(AdminResource, '/admin/problem')
api.add_resource(DeleteResource, '/delete/problem/<wid>')
api.add_resource(AdminProblemResource, '/admin/problem/<string:wid>')


if __name__ == '__main__':
    CORS(app, supports_credentials=True)
    app.run(host='127.0.0.1', port=5000)  # 确保端口号与防火墙规则一致
