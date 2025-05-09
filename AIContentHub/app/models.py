from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    drafts = db.relationship('Draft', backref='author', lazy='dynamic')
    api_configs = db.relationship('ApiConfig', backref='user', lazy='dynamic')
    platform_accounts = db.relationship('PlatformAccount', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'

class ApiConfig(db.Model):
    __tablename__ = 'api_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    api_name = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(256), nullable=False)
    api_secret = db.Column(db.String(256))
    api_url = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiConfig {self.api_name}>'

class PlatformAccount(db.Model):
    __tablename__ = 'platform_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform_name = db.Column(db.String(64), nullable=False)
    account_name = db.Column(db.String(128), nullable=False)
    account_id = db.Column(db.String(128))
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(256))
    access_token = db.Column(db.String(512))
    refresh_token = db.Column(db.String(512))
    token_expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    publications = db.relationship('Publication', backref='account', lazy='dynamic')
    
    def __repr__(self):
        return f'<PlatformAccount {self.platform_name}:{self.account_name}>'

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    source = db.Column(db.String(128))  # 'ai_generated', 'news_source', 'manual', etc.
    source_url = db.Column(db.String(512))
    keywords = db.Column(db.String(256))
    category = db.Column(db.String(64))
    status = db.Column(db.String(32), default='draft')  # 'draft', 'published', 'archived'
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    images = db.relationship('Image', backref='article', lazy='dynamic')
    publications = db.relationship('Publication', backref='article', lazy='dynamic')
    
    def __repr__(self):
        return f'<Article {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'category': self.category,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'published_at': self.published_at.strftime('%Y-%m-%d %H:%M:%S') if self.published_at else None,
        }

class Draft(db.Model):
    __tablename__ = 'drafts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(256))
    content = db.Column(db.Text)
    source = db.Column(db.String(128))
    source_url = db.Column(db.String(512))
    category = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Draft {self.title}>'

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(256))
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    mime_type = db.Column(db.String(64))
    description = db.Column(db.Text)
    position = db.Column(db.Integer)  # 图片在文章中的位置
    is_cover = db.Column(db.Boolean, default=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    ai_prompt = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Image {self.filename}>'

class Publication(db.Model):
    __tablename__ = 'publications'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    platform_account_id = db.Column(db.Integer, db.ForeignKey('platform_accounts.id'), nullable=False)
    platform_article_id = db.Column(db.String(128))
    platform_article_url = db.Column(db.String(512))
    status = db.Column(db.String(32), default='pending')  # 'pending', 'published', 'failed'
    error_message = db.Column(db.Text)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Publication {self.id}>'

class NewsSource(db.Model):
    __tablename__ = 'news_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    category = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    last_fetched_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NewsSource {self.name}>'

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_type = db.Column(db.String(64), nullable=False)  # 'fetch_news', 'generate_article', 'publish_article', etc.
    status = db.Column(db.String(32), default='pending')  # 'pending', 'running', 'completed', 'failed'
    params = db.Column(db.Text)  # JSON string of parameters
    result = db.Column(db.Text)  # JSON string of result
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.task_type}:{self.status}>'
    
    def set_params(self, params_dict):
        self.params = json.dumps(params_dict)
    
    def get_params(self):
        return json.loads(self.params) if self.params else {}
    
    def set_result(self, result_dict):
        self.result = json.dumps(result_dict)
    
    def get_result(self):
        return json.loads(self.result) if self.result else {}