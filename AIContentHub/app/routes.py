from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from .models import db, User, Article, Draft, Image, ApiConfig, PlatformAccount, Publication, Task
from .utils import save_image, SensitiveFilter, AIContentGenerator, ContentPublisher, extract_sections, generate_section_images

# 创建蓝图
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
api = Blueprint('api', __name__)
admin = Blueprint('admin', __name__)

# 敏感词过滤器
sensitive_filter = None

# 内容发布器
content_publisher = None

# 初始化函数
def init_app_utils():
    global sensitive_filter, content_publisher
    sensitive_filter = SensitiveFilter()
    content_publisher = ContentPublisher()

# 主页路由
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    # 获取用户的文章统计
    articles_count = Article.query.filter_by(user_id=current_user.id).count()
    drafts_count = Draft.query.filter_by(user_id=current_user.id).count()
    published_count = Article.query.filter_by(user_id=current_user.id, status='published').count()
    
    # 获取最近的文章
    recent_articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.created_at.desc()).limit(5).all()
    
    # 获取最近的任务
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          articles_count=articles_count,
                          drafts_count=drafts_count,
                          published_count=published_count,
                          recent_articles=recent_articles,
                          recent_tasks=recent_tasks)

# 文章管理路由
@main.route('/articles')
@login_required
def articles():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('articles.html', articles=articles)

@main.route('/articles/new', methods=['GET', 'POST'])
@login_required
def new_article():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        summary = request.form.get('summary')
        category = request.form.get('category')
        
        # 过滤敏感词
        if sensitive_filter:
            content, found_words = sensitive_filter.filter_text(content)
            if found_words:
                flash(f'文章内容包含敏感词: {", ".join([w[1] for w in found_words])}，已自动过滤', 'warning')
        
        # 创建新文章
        article = Article(
            user_id=current_user.id,
            title=title,
            content=content,
            summary=summary,
            category=category,
            status='draft'
        )
        
        db.session.add(article)
        db.session.commit()
        
        # 处理上传的图片
        if 'images' in request.files:
            for file in request.files.getlist('images'):
                if file.filename:
                    image_data = save_image(file, article.id)
                    if image_data:
                        image = Image(
                            article_id=article.id,
                            filename=image_data['filename'],
                            original_filename=image_data['original_filename'],
                            file_path=image_data['file_path'],
                            file_size=image_data['file_size'],
                            width=image_data['width'],
                            height=image_data['height'],
                            mime_type=image_data['mime_type']
                        )
                        db.session.add(image)
        
        db.session.commit()
        
        flash('文章创建成功', 'success')
        return redirect(url_for('main.edit_article', article_id=article.id))
    
    return render_template('article_form.html')

@main.route('/articles/<int:article_id>')
@login_required
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 确保只有文章作者可以查看
    if article.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限查看此文章', 'danger')
        return redirect(url_for('main.articles'))
    
    # 获取文章图片
    images = Image.query.filter_by(article_id=article_id).all()
    
    # 获取发布记录
    publications = Publication.query.filter_by(article_id=article_id).all()
    
    return render_template('article_view.html', article=article, images=images, publications=publications)

@main.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 确保只有文章作者可以编辑
    if article.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此文章', 'danger')
        return redirect(url_for('main.articles'))
    
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.content = request.form.get('content')
        article.summary = request.form.get('summary')
        article.category = request.form.get('category')
        article.updated_at = datetime.utcnow()
        
        # 过滤敏感词
        if sensitive_filter:
            article.content, found_words = sensitive_filter.filter_text(article.content)
            if found_words:
                flash(f'文章内容包含敏感词: {", ".join([w[1] for w in found_words])}，已自动过滤', 'warning')
        
        # 处理上传的新图片
        if 'images' in request.files:
            for file in request.files.getlist('images'):
                if file.filename:
                    image_data = save_image(file, article.id)
                    if image_data:
                        image = Image(
                            article_id=article.id,
                            filename=image_data['filename'],
                            original_filename=image_data['original_filename'],
                            file_path=image_data['file_path'],
                            file_size=image_data['file_size'],
                            width=image_data['width'],
                            height=image_data['height'],
                            mime_type=image_data['mime_type']
                        )
                        db.session.add(image)
        
        db.session.commit()
        flash('文章更新成功', 'success')
        return redirect(url_for('main.view_article', article_id=article.id))
    
    # 获取文章图片
    images = Image.query.filter_by(article_id=article_id).all()
    
    return render_template('article_form.html', article=article, images=images)

@main.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 确保只有文章作者可以删除
    if article.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此文章', 'danger')
        return redirect(url_for('main.articles'))
    
    # 删除相关图片文件
    images = Image.query.filter_by(article_id=article_id).all()
    for image in images:
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
    
    # 删除数据库记录
    Image.query.filter_by(article_id=article_id).delete()
    Publication.query.filter_by(article_id=article_id).delete()
    db.session.delete(article)
    db.session.commit()
    
    flash('文章已删除', 'success')
    return redirect(url_for('main.articles'))

@main.route('/articles/<int:article_id>/publish', methods=['GET', 'POST'])
@login_required
def publish_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 确保只有文章作者可以发布
    if article.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限发布此文章', 'danger')
        return redirect(url_for('main.articles'))
    
    # 获取用户的平台账号
    platform_accounts = PlatformAccount.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        selected_platforms = request.form.getlist('platforms')
        
        if not selected_platforms:
            flash('请选择至少一个发布平台', 'warning')
            return redirect(url_for('main.publish_article', article_id=article_id))
        
        # 更新文章状态
        article.status = 'published'
        article.published_at = datetime.utcnow()
        db.session.commit()
        
        # 创建发布任务
        for platform_id in selected_platforms:
            platform_account = PlatformAccount.query.get(platform_id)
            if platform_account and platform_account.user_id == current_user.id:
                # 创建发布记录
                publication = Publication(
                    article_id=article.id,
                    platform_account_id=platform_account.id,
                    status='pending'
                )
                db.session.add(publication)
                
                # 创建发布任务
                task = Task(
                    task_type='publish_article',
                    status='pending'
                )
                task.set_params({
                    'article_id': article.id,
                    'platform_account_id': platform_account.id,
                    'publication_id': None  # 将在任务执行前更新
                })
                db.session.add(task)
        
        db.session.commit()
        
        # 更新任务中的publication_id
        for task in Task.query.filter_by(task_type='publish_article', status='pending').all():
            params = task.get_params()
            if params.get('article_id') == article.id:
                publication = Publication.query.filter_by(
                    article_id=article.id,
                    platform_account_id=params.get('platform_account_id')
                ).first()
                
                if publication:
                    params['publication_id'] = publication.id
                    task.set_params(params)
        
        db.session.commit()
        
        flash('文章已提交发布，请在发布记录中查看状态', 'success')
        return redirect(url_for('main.view_article', article_id=article.id))
    
    return render_template('publish_article.html', article=article, platform_accounts=platform_accounts)

# AI内容生成路由
@main.route('/ai/generate', methods=['GET', 'POST'])
@login_required
def ai_generate():
    # 获取用户的API配置
    api_configs = ApiConfig.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        topic = request.form.get('topic')
        length = int(request.form.get('length', 3000))
        style = request.form.get('style', 'informative')
        api_config_id = request.form.get('api_config')
        
        if not topic:
            flash('请输入文章主题', 'warning')
            return redirect(url_for('main.ai_generate'))
        
        # 获取选择的API配置
        api_config = ApiConfig.query.get(api_config_id) if api_config_id else None
        
        if not api_config and not current_app.config.get('OPENAI_API_KEY'):
            flash('请先配置AI API密钥', 'warning')
            return redirect(url_for('main.ai_generate'))
        
        # 创建生成任务
        task = Task(
            task_type='generate_article',
            status='pending'
        )
        task.set_params({
            'topic': topic,
            'length': length,
            'style': style,
            'api_type': api_config.api_name if api_config else 'openai',
            'api_key': api_config.api_key if api_config else current_app.config.get('OPENAI_API_KEY')
        })
        db.session.add(task)
        db.session.commit()
        
        flash('文章生成任务已创建，请稍后查看任务状态', 'success')
        return redirect(url_for('main.tasks'))
    
    return render_template('ai_generate.html', api_configs=api_configs)

@main.route('/ai/generate_image', methods=['GET', 'POST'])
@login_required
def ai_generate_image():
    # 获取用户的API配置
    api_configs = ApiConfig.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        size = request.form.get('size', '1024x1024')
        article_id = request.form.get('article_id')
        api_config_id = request.form.get('api_config')
        
        if not prompt:
            flash('请输入图片描述', 'warning')
            return redirect(url_for('main.ai_generate_image'))
        
        # 获取选择的API配置
        api_config = ApiConfig.query.get(api_config_id) if api_config_id else None
        
        if not api_config and not current_app.config.get('OPENAI_API_KEY'):
            flash('请先配置AI API密钥', 'warning')
            return redirect(url_for('main.ai_generate_image'))
        
        # 创建生成任务
        task = Task(
            task_type='generate_image',
            status='pending'
        )
        task.set_params({
            'prompt': prompt,
            'size': size,
            'article_id': article_id,
            'api_type': api_config.api_name if api_config else 'openai',
            'api_key': api_config.api_key if api_config else current_app.config.get('OPENAI_API_KEY')
        })
        db.session.add(task)
        db.session.commit()
        
        flash('图片生成任务已创建，请稍后查看任务状态', 'success')
        return redirect(url_for('main.tasks'))
    
    # 获取用户的文章列表
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.created_at.desc()).all()
    
    return render_template('ai_generate_image.html', api_configs=api_configs, articles=articles)

# 草稿管理路由
@main.route('/drafts')
@login_required
def drafts():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    drafts = Draft.query.filter_by(user_id=current_user.id).order_by(Draft.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('drafts.html', drafts=drafts)

@main.route('/drafts/new', methods=['GET', 'POST'])
@login_required
def new_draft():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        
        # 创建新草稿
        draft = Draft(
            user_id=current_user.id,
            title=title,
            content=content,
            category=category
        )
        
        db.session.add(draft)
        db.session.commit()
        
        flash('草稿保存成功', 'success')
        return redirect(url_for('main.edit_draft', draft_id=draft.id))
    
    return render_template('draft_form.html')

@main.route('/drafts/<int:draft_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_draft(draft_id):
    draft = Draft.query.get_or_404(draft_id)
    
    # 确保只有草稿作者可以编辑
    if draft.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此草稿', 'danger')
        return redirect(url_for('main.drafts'))
    
    if request.method == 'POST':
        draft.title = request.form.get('title')
        draft.content = request.form.get('content')
        draft.category = request.form.get('category')
        draft.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('草稿更新成功', 'success')
        return redirect(url_for('main.drafts'))
    
    return render_template('draft_form.html', draft=draft)

@main.route('/drafts/<int:draft_id>/delete', methods=['POST'])
@login_required
def delete_draft(draft_id):
    draft = Draft.query.get_or_404(draft_id)
    
    # 确保只有草稿作者可以删除
    if draft.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此草稿', 'danger')
        return redirect(url_for('main.drafts'))
    
    db.session.delete(draft)
    db.session.commit()
    
    flash('草稿已删除', 'success')
    return redirect(url_for('main.drafts'))

@main.route('/drafts/<int:draft_id>/convert', methods=['POST'])
@login_required
def convert_draft_to_article(draft_id):
    draft = Draft.query.get_or_404(draft_id)
    
    # 确保只有草稿作者可以转换
    if draft.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限转换此草稿', 'danger')
        return redirect(url_for('main.drafts'))
    
    # 创建新文章
    article = Article(
        user_id=current_user.id,
        title=draft.title,
        content=draft.content,
        category=draft.category,
        status='draft'
    )
    
    db.session.add(article)
    db.session.commit()
    
    flash('草稿已转换为文章', 'success')
    return redirect(url_for('main.edit_article', article_id=article.id))

# 任务管理路由
@main.route('/tasks')
@login_required
def tasks():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    per_page = 10
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Task.created_at.desc()).paginate(page=page, per_page=per_page)
    tasks = pagination.items
    
    return render_template('tasks.html', tasks=tasks, pagination=pagination)

@main.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # 确保只有任务所有者可以删除
    if task.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此任务', 'danger')
        return redirect(url_for('main.tasks'))
    
    # 只允许删除失败或等待中的任务
    if task.status not in ['failed', 'pending']:
        flash('只能删除失败或等待中的任务', 'danger')
        return redirect(url_for('main.tasks'))
    
    db.session.delete(task)
    db.session.commit()
    
    flash('任务已删除', 'success')
    return redirect(url_for('main.tasks'))

@main.route('/tasks/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    return render_template('task_view.html', task=task)

# 用户设置路由
@main.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def settings_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 更新用户信息
        if username and username != current_user.username:
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first() and User.query.filter_by(username=username).first().id != current_user.id:
                flash('用户名已被使用', 'danger')
                return redirect(url_for('main.settings_profile'))
            current_user.username = username
        
        if email and email != current_user.email:
            # 检查邮箱是否已存在
            if User.query.filter_by(email=email).first() and User.query.filter_by(email=email).first().id != current_user.id:
                flash('邮箱已被使用', 'danger')
                return redirect(url_for('main.settings_profile'))
            current_user.email = email
        
        # 更新密码
        if current_password and new_password and confirm_password:
            if not current_user.check_password(current_password):
                flash('当前密码不正确', 'danger')
                return redirect(url_for('main.settings_profile'))
            
            if new_password != confirm_password:
                flash('新密码和确认密码不匹配', 'danger')
                return redirect(url_for('main.settings_profile'))
            
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('个人资料更新成功', 'success')
        return redirect(url_for('main.settings_profile'))
    
    return render_template('settings_profile.html')

# API配置路由
@main.route('/settings/api')
@login_required
def settings_api():
    configs = ApiConfig.query.filter_by(user_id=current_user.id).all()
    return render_template('settings_api.html', configs=configs)

@main.route('/settings/api/new', methods=['GET', 'POST'])
@login_required
def new_api_config():
    if request.method == 'POST':
        api_name = request.form.get('api_name')
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        api_url = request.form.get('api_url')
        
        # 创建新API配置
        config = ApiConfig(
            user_id=current_user.id,
            api_name=api_name,
            api_key=api_key,
            api_secret=api_secret,
            api_url=api_url
        )
        
        db.session.add(config)
        db.session.commit()
        
        flash('API配置添加成功', 'success')
        return redirect(url_for('main.settings_api'))
    
    return render_template('api_config_form.html')

@main.route('/settings/api/<int:config_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_api_config(config_id):
    config = ApiConfig.query.get_or_404(config_id)
    
    # 确保只有配置所有者可以编辑
    if config.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此配置', 'danger')
        return redirect(url_for('main.settings_api'))
    
    if request.method == 'POST':
        config.api_name = request.form.get('api_name')
        config.api_key = request.form.get('api_key')
        config.api_secret = request.form.get('api_secret')
        config.api_url = request.form.get('api_url')
        config.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('API配置更新成功', 'success')
        return redirect(url_for('main.settings_api'))
    
    return render_template('api_config_form.html', config=config)

@main.route('/settings/api/<int:config_id>/delete', methods=['POST'])
@login_required
def delete_api_config(config_id):
    config = ApiConfig.query.get_or_404(config_id)
    
    # 确保只有配置所有者可以删除
    if config.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此配置', 'danger')
        return redirect(url_for('main.settings_api'))
    
    db.session.delete(config)
    db.session.commit()
    
    flash('API配置已删除', 'success')
    return redirect(url_for('main.settings_api'))

# 平台账号路由
@main.route('/settings/platforms')
@login_required
def settings_platforms():
    accounts = PlatformAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('settings_platforms.html', accounts=accounts)

# 敏感词管理路由
@main.route('/settings/sensitive_words')
@login_required
def settings_sensitive_words():
    legal_words = SensitiveWord.query.filter_by(user_id=current_user.id, category='legal').all()
    ad_words = SensitiveWord.query.filter_by(user_id=current_user.id, category='ad').all()
    custom_words = SensitiveWord.query.filter_by(user_id=current_user.id, category='custom').all()
    
    return render_template('settings_sensitive_words.html', 
                          legal_words=legal_words, 
                          ad_words=ad_words, 
                          custom_words=custom_words)

@main.route('/platform_accounts')
@login_required
def platform_accounts():
    accounts = PlatformAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('platform_accounts.html', accounts=accounts)

@main.route('/platform_accounts/new', methods=['GET', 'POST'])
@login_required
def new_platform_account():
    if request.method == 'POST':
        platform_name = request.form.get('platform_name')
        account_name = request.form.get('account_name')
        account_id = request.form.get('account_id')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 创建新平台账号
        account = PlatformAccount(
            user_id=current_user.id,
            platform_name=platform_name,
            account_name=account_name,
            account_id=account_id,
            username=username,
            password_hash=generate_password_hash(password) if password else None
        )
        
        db.session.add(account)
        db.session.commit()
        
        flash('平台账号添加成功', 'success')
        return redirect(url_for('main.platform_accounts'))
    
    return render_template('platform_account_form.html')

@main.route('/platform_accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_platform_account(account_id):
    account = PlatformAccount.query.get_or_404(account_id)
    
    # 确保只有账号所有者可以编辑
    if account.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此账号', 'danger')
        return redirect(url_for('main.platform_accounts'))
    
    if request.method == 'POST':
        account.platform_name = request.form.get('platform_name')
        account.account_name = request.form.get('account_name')
        account.account_id = request.form.get('account_id')
        account.username = request.form.get('username')
        
        password = request.form.get('password')
        if password:
            account.password_hash = generate_password_hash(password)
        
        account.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('平台账号更新成功', 'success')
        return redirect(url_for('main.platform_accounts'))
    
    return render_template('platform_account_form.html', account=account)

@main.route('/platform_accounts/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_platform_account(account_id):
    account = PlatformAccount.query.get_or_404(account_id)
    
    # 确保只有账号所有者可以删除
    if account.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此账号', 'danger')
        return redirect(url_for('main.platform_accounts'))
    
    db.session.delete(account)
    db.session.commit()
    
    flash('平台账号已删除', 'success')
    return redirect(url_for('main.platform_accounts'))

# 认证路由
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        
        flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('register.html')
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# API路由
@api.route('/articles', methods=['GET'])
@login_required
def api_articles():
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.created_at.desc()).all()
    return jsonify([article.to_dict() for article in articles])

@api.route('/articles/<int:article_id>', methods=['GET'])
@login_required
def api_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 确保只有文章作者可以访问
    if article.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': '没有权限访问此文章'}), 403
    
    return jsonify(article.to_dict())

@api.route('/filter_text', methods=['POST'])
@login_required
def api_filter_text():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': '文本不能为空'}), 400
    
    # 过滤敏感词
    if sensitive_filter:
        filtered_text, found_words = sensitive_filter.filter_text(text)
        return jsonify({
            'original_text': text,
            'filtered_text': filtered_text,
            'found_words': [{'type': w[0], 'word': w[1]} for w in found_words]
        })
    
    return jsonify({'error': '敏感词过滤器未初始化'}), 500

@api.route('/generate_article', methods=['POST'])
@login_required
def api_generate_article():
    data = request.get_json()
    topic = data.get('topic')
    length = data.get('length', 3000)
    style = data.get('style', 'informative')
    api_key = data.get('api_key')
    api_type = data.get('api_type', 'openai')
    
    if not topic:
        return jsonify({'error': '主题不能为空'}), 400
    
    # 创建生成任务
    task = Task(
        task_type='generate_article',
        status='pending'
    )
    task.set_params({
        'topic': topic,
        'length': length,
        'style': style,
        'api_type': api_type,
        'api_key': api_key
    })
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'task_id': task.id,
        'status': 'pending',
        'message': '文章生成任务已创建'
    })

@api.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def api_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    return jsonify({
        'id': task.id,
        'task_type': task.task_type,
        'status': task.status,
        'params': task.get_params(),
        'result': task.get_result(),
        'error_message': task.error_message,
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'started_at': task.started_at.strftime('%Y-%m-%d %H:%M:%S') if task.started_at else None,
        'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else None
    })

# 静态文件路由
@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# 管理员路由
@admin.route('/')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('您没有管理员权限', 'danger')
        return redirect(url_for('main.dashboard'))
    
    users_count = User.query.count()
    articles_count = Article.query.count()
    tasks_count = Task.query.count()
    
    return render_template('admin/dashboard.html', 
                          users_count=users_count,
                          articles_count=articles_count,
                          tasks_count=tasks_count)

@admin.route('/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('您没有管理员权限', 'danger')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/tasks')
@login_required
def admin_tasks():
    if not current_user.is_admin:
        flash('您没有管理员权限', 'danger')
        return redirect(url_for('main.dashboard'))
    
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('admin/tasks.html', tasks=tasks)