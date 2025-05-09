import os
from datetime import timedelta

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:////' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data', 'aicontenthub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data', 'images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 日志配置
    LOG_FOLDER = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    # AI API配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    BAIDU_API_KEY = os.environ.get('BAIDU_API_KEY', '')
    BAIDU_SECRET_KEY = os.environ.get('BAIDU_SECRET_KEY', '')
    XFYUN_APP_ID = os.environ.get('XFYUN_APP_ID', '')
    XFYUN_API_KEY = os.environ.get('XFYUN_API_KEY', '')
    XFYUN_API_SECRET = os.environ.get('XFYUN_API_SECRET', '')
    
    # 微信公众号配置
    WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID', '')
    WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET', '')
    
    # 其他平台配置
    ZHIHU_USERNAME = os.environ.get('ZHIHU_USERNAME', '')
    ZHIHU_PASSWORD = os.environ.get('ZHIHU_PASSWORD', '')
    
    TOUTIAO_USERNAME = os.environ.get('TOUTIAO_USERNAME', '')
    TOUTIAO_PASSWORD = os.environ.get('TOUTIAO_PASSWORD', '')
    
    BAIJIAHAO_USERNAME = os.environ.get('BAIJIAHAO_USERNAME', '')
    BAIJIAHAO_PASSWORD = os.environ.get('BAIJIAHAO_PASSWORD', '')
    
    SOHU_USERNAME = os.environ.get('SOHU_USERNAME', '')
    SOHU_PASSWORD = os.environ.get('SOHU_PASSWORD', '')
    
    WEIBO_USERNAME = os.environ.get('WEIBO_USERNAME', '')
    WEIBO_PASSWORD = os.environ.get('WEIBO_PASSWORD', '')
    
    # 敏感词过滤配置
    SENSITIVE_WORDS_FILE = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'config', 'sensitive_words.txt')
    AD_LAW_WORDS_FILE = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'config', 'ad_law_words.txt')