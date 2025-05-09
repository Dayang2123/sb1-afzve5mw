import os
import time
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'worker.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('worker')

def process_tasks():
    """处理待执行的任务"""
    from app import create_app
    from app.models import db, Task, Article, Image, Publication, PlatformAccount
    from app.utils import AIContentGenerator, ContentPublisher, generate_section_images
    
    app = create_app()
    
    with app.app_context():
        # 获取待处理的任务
        pending_tasks = Task.query.filter_by(status='pending').order_by(Task.created_at).limit(5).all()
        
        for task in pending_tasks:
            logger.info(f"处理任务 {task.id}: {task.task_type}")
            
            # 更新任务状态
            task.status = 'running'
            task.started_at = datetime.utcnow()
            db.session.commit()
            
            try:
                # 根据任务类型执行不同的操作
                if task.task_type == 'generate_article':
                    params = task.get_params()
                    topic = params.get('topic')
                    length = params.get('length', 3000)
                    style = params.get('style', 'informative')
                    api_type = params.get('api_type', 'openai')
                    api_key = params.get('api_key')
                    
                    # 生成文章
                    generator = AIContentGenerator(api_key=api_key, api_type=api_type)
                    result = generator.generate_article(topic, length, style)
                    
                    if result.get('success'):
                        # 创建文章
                        article = Article(
                            user_id=1,  # 默认为管理员
                            title=topic,
                            content=result.get('content'),
                            source='ai_generated',
                            status='draft'
                        )
                        db.session.add(article)
                        db.session.commit()
                        
                        # 为文章生成配图
                        images = generate_section_images(result.get('content'), generator)
                        
                        for img_data in images:
                            if img_data.get('image', {}).get('success'):
                                img = img_data.get('image')
                                image = Image(
                                    article_id=article.id,
                                    filename=img.get('filename'),
                                    file_path=img.get('file_path'),
                                    file_size=img.get('file_size'),
                                    width=img.get('width'),
                                    height=img.get('height'),
                                    description=img_data.get('section'),
                                    is_ai_generated=True,
                                    ai_prompt=img.get('prompt')
                                )
                                db.session.add(image)
                        
                        db.session.commit()
                        
                        # 更新任务结果
                        task.set_result({
                            'article_id': article.id,
                            'title': article.title,
                            'content_length': len(article.content),
                            'images_count': len(images)
                        })
                    else:
                        task.status = 'failed'
                        task.error_message = result.get('error')
                
                elif task.task_type == 'generate_image':
                    params = task.get_params()
                    prompt = params.get('prompt')
                    size = params.get('size', '1024x1024')
                    article_id = params.get('article_id')
                    api_type = params.get('api_type', 'openai')
                    api_key = params.get('api_key')
                    
                    # 生成图片
                    generator = AIContentGenerator(api_key=api_key, api_type=api_type)
                    result = generator.generate_image(prompt, size)
                    
                    if result.get('success'):
                        # 如果指定了文章，将图片关联到文章
                        if article_id:
                            image = Image(
                                article_id=article_id,
                                filename=result.get('filename'),
                                file_path=result.get('file_path'),
                                file_size=result.get('file_size'),
                                width=result.get('width'),
                                height=result.get('height'),
                                description=prompt,
                                is_ai_generated=True,
                                ai_prompt=prompt
                            )
                            db.session.add(image)
                            db.session.commit()
                        
                        # 更新任务结果
                        task.set_result({
                            'filename': result.get('filename'),
                            'file_path': result.get('file_path'),
                            'article_id': article_id
                        })
                    else:
                        task.status = 'failed'
                        task.error_message = result.get('error')
                
                elif task.task_type == 'publish_article':
                    params = task.get_params()
                    article_id = params.get('article_id')
                    platform_account_id = params.get('platform_account_id')
                    publication_id = params.get('publication_id')
                    
                    # 获取文章和平台账号
                    article = Article.query.get(article_id)
                    platform_account = PlatformAccount.query.get(platform_account_id)
                    publication = Publication.query.get(publication_id)
                    
                    if not article or not platform_account or not publication:
                        task.status = 'failed'
                        task.error_message = '找不到文章、平台账号或发布记录'
                    else:
                        # 获取文章图片
                        images = Image.query.filter_by(article_id=article_id).all()
                        
                        # 准备发布数据
                        article_data = {
                            'title': article.title,
                            'content': article.content,
                            'summary': article.summary,
                            'author': article.author.username,
                            'images': [{'file_path': img.file_path, 'description': img.description} for img in images]
                        }
                        
                        account_data = {
                            'platform': platform_account.platform_name,
                            'username': platform_account.username,
                            'password': platform_account.password_hash,
                            'app_id': platform_account.account_id,
                            'app_secret': platform_account.access_token
                        }
                        
                        # 发布文章
                        publisher = ContentPublisher()
                        result = publisher.publish_to_platform(article_data, platform_account.platform_name, account_data)
                        
                        if result.get('success'):
                            # 更新发布记录
                            publication.status = 'published'
                            publication.platform_article_id = result.get('article_id')
                            publication.platform_article_url = result.get('article_url', '')
                            publication.published_at = datetime.utcnow()
                            
                            # 更新任务结果
                            task.set_result({
                                'platform': platform_account.platform_name,
                                'article_id': result.get('article_id'),
                                'article_url': result.get('article_url', '')
                            })
                        else:
                            publication.status = 'failed'
                            publication.error_message = result.get('error')
                            
                            task.status = 'failed'
                            task.error_message = result.get('error')
                
                # 如果任务成功完成
                if task.status != 'failed':
                    task.status = 'completed'
                
                task.completed_at = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                logger.error(f"处理任务 {task.id} 失败: {str(e)}")
                
                # 更新任务状态
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.session.commit()

def fetch_hot_news():
    """采集热点资讯"""
    from app import create_app
    from app.models import db, NewsSource, Task
    
    app = create_app()
    
    with app.app_context():
        # 获取活跃的新闻源
        news_sources = NewsSource.query.filter_by(is_active=True).all()
        
        for source in news_sources:
            logger.info(f"从 {source.name} 采集新闻")
            
            # 创建采集任务
            task = Task(
                task_type='fetch_news',
                status='pending'
            )
            task.set_params({
                'source_id': source.id,
                'source_name': source.name,
                'source_url': source.url,
                'category': source.category
            })
            
            db.session.add(task)
            
            # 更新最后采集时间
            source.last_fetched_at = datetime.utcnow()
        
        db.session.commit()

if __name__ == '__main__':
    logger.info("启动任务处理器")
    
    # 每分钟处理一次任务
    schedule.every(1).minutes.do(process_tasks)
    
    # 每小时采集一次新闻
    schedule.every(1).hours.do(fetch_hot_news)
    
    # 运行调度器
    while True:
        schedule.run_pending()
        time.sleep(1)