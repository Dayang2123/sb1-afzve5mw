from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

def init_database():
    """初始化数据库并创建管理员账号"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已存在管理员账号
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # 创建管理员账号
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("已创建管理员账号: admin / admin123")
        else:
            print("管理员账号已存在")
        
        print("数据库初始化完成")

if __name__ == '__main__':
    init_database()