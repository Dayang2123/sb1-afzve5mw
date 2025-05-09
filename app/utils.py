import os
import re
import json
import uuid
import jieba
import logging
import requests
from datetime import datetime
from PIL import Image as PILImage
from werkzeug.utils import secure_filename
from flask import current_app

# 配置日志
def setup_logger(name, log_file, level=logging.INFO):
    """设置应用日志"""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# 文件处理
def allowed_file(filename):
    """检查文件扩展名是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file, article_id=None):
    """保存上传的图片文件"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 确保目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if article_id:
            upload_folder = os.path.join(upload_folder, str(article_id))
        
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # 获取图片信息
        try:
            with PILImage.open(file_path) as img:
                width, height = img.size
                mime_type = img.get_format_mimetype()
        except Exception as e:
            width, height = 0, 0
            mime_type = file.content_type
        
        return {
            'filename': unique_filename,
            'original_filename': filename,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'width': width,
            'height': height,
            'mime_type': mime_type
        }
    
    return None

# 敏感词过滤
class SensitiveFilter:
    def __init__(self):
        self.sensitive_words = set()
        self.ad_law_words = set()
        self._load_words()
    
    def _load_words(self):
        """加载敏感词和广告法禁用词"""
        try:
            sensitive_file = current_app.config['SENSITIVE_WORDS_FILE']
            if os.path.exists(sensitive_file):
                with open(sensitive_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word:
                            self.sensitive_words.add(word)
            
            ad_law_file = current_app.config['AD_LAW_WORDS_FILE']
            if os.path.exists(ad_law_file):
                with open(ad_law_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word:
                            self.ad_law_words.add(word)
        except Exception as e:
            print(f"加载敏感词文件失败: {e}")
    
    def filter_text(self, text, replace_char='*'):
        """过滤文本中的敏感词"""
        if not text:
            return text, []
        
        found_words = []
        
        # 使用结巴分词提高匹配效率
        seg_list = jieba.cut(text)
        
        # 检查敏感词
        for word in self.sensitive_words:
            if word in text:
                found_words.append(('sensitive', word))
                text = text.replace(word, replace_char * len(word))
        
        # 检查广告法禁用词
        for word in self.ad_law_words:
            if word in text:
                found_words.append(('ad_law', word))
                text = text.replace(word, replace_char * len(word))
        
        return text, found_words

# AI 内容生成
class AIContentGenerator:
    def __init__(self, api_key=None, api_type='openai'):
        self.api_key = api_key or current_app.config.get('OPENAI_API_KEY', '')
        self.api_type = api_type
    
    def generate_article(self, topic, length=3000, style='informative'):
        """生成文章内容"""
        if self.api_type == 'openai':
            return self._generate_with_openai(topic, length, style)
        elif self.api_type == 'baidu':
            return self._generate_with_baidu(topic, length, style)
        else:
            raise ValueError(f"不支持的API类型: {self.api_type}")
    
    def _generate_with_openai(self, topic, length=3000, style='informative'):
        """使用OpenAI API生成文章"""
        import openai
        
        openai.api_key = self.api_key
        
        try:
            # 构建提示词
            prompt = f"""
            请以"{topic}"为主题，创作一篇{length}字左右的深度文章。
            要求：
            1. 文章结构清晰，分为引言、多个主要章节和结论
            2. 每个章节都有小标题
            3. 文章风格为{style}
            4. 内容要有深度，包含相关数据、案例或观点
            5. 避免使用敏感词汇和广告法禁用词
            6. 确保文章原创性，不要直接复制网络内容
            7. 文章总字数控制在{length}字左右
            8. 使用中文撰写
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一位专业的内容创作者，擅长撰写深度文章。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            return {
                'content': response.choices[0].message['content'],
                'success': True
            }
        
        except Exception as e:
            return {
                'content': '',
                'success': False,
                'error': str(e)
            }
    
    def _generate_with_baidu(self, topic, length=3000, style='informative'):
        """使用百度文心一言API生成文章"""
        api_key = current_app.config.get('BAIDU_API_KEY', '')
        secret_key = current_app.config.get('BAIDU_SECRET_KEY', '')
        
        # 获取访问令牌
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        response = requests.post(token_url)
        if response.status_code != 200:
            return {
                'content': '',
                'success': False,
                'error': f"获取百度API访问令牌失败: {response.text}"
            }
        
        access_token = response.json().get('access_token')
        
        # 调用文心一言API
        api_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
        
        prompt = f"""
        请以"{topic}"为主题，创作一篇{length}字左右的深度文章。
        要求：
        1. 文章结构清晰，分为引言、多个主要章节和结论
        2. 每个章节都有小标题
        3. 文章风格为{style}
        4. 内容要有深度，包含相关数据、案例或观点
        5. 避免使用敏感词汇和广告法禁用词
        6. 确保文章原创性，不要直接复制网络内容
        7. 文章总字数控制在{length}字左右
        8. 使用中文撰写
        """
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code != 200:
                return {
                    'content': '',
                    'success': False,
                    'error': f"调用百度API失败: {response.text}"
                }
            
            result = response.json()
            return {
                'content': result.get('result', ''),
                'success': True
            }
        
        except Exception as e:
            return {
                'content': '',
                'success': False,
                'error': str(e)
            }
    
    def generate_image(self, prompt, size="1024x1024"):
        """根据提示词生成图片"""
        if self.api_type == 'openai':
            return self._generate_image_with_openai(prompt, size)
        else:
            raise ValueError(f"图片生成不支持的API类型: {self.api_type}")
    
    def _generate_image_with_openai(self, prompt, size="1024x1024"):
        """使用OpenAI DALL-E API生成图片"""
        import openai
        
        openai.api_key = self.api_key
        
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size=size
            )
            
            image_url = response['data'][0]['url']
            
            # 下载图片
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                # 生成唯一文件名
                filename = f"{uuid.uuid4().hex}.png"
                
                # 确保目录存在
                upload_folder = current_app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                
                # 保存图片
                with open(file_path, 'wb') as f:
                    f.write(image_response.content)
                
                # 获取图片信息
                with PILImage.open(file_path) as img:
                    width, height = img.size
                
                return {
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'width': width,
                    'height': height,
                    'prompt': prompt,
                    'success': True
                }
            
            return {
                'success': False,
                'error': f"下载图片失败: {image_response.status_code}"
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# 文章分析
def extract_sections(content):
    """从文章内容中提取章节"""
    # 使用正则表达式匹配标题
    section_pattern = r'(#+\s+.+?)\n'
    sections = re.findall(section_pattern, content)
    
    # 如果没有找到标题，尝试匹配其他格式
    if not sections:
        section_pattern = r'([一二三四五六七八九十]+、.+?)\n'
        sections = re.findall(section_pattern, content)
    
    # 如果仍然没有找到，尝试按段落分割
    if not sections:
        paragraphs = content.split('\n\n')
        sections = [p[:20] + '...' for p in paragraphs if len(p) > 30][:5]
    
    return sections

def generate_section_images(content, generator):
    """为文章章节生成配图"""
    sections = extract_sections(content)
    images = []
    
    for section in sections[:3]:  # 限制只为前3个章节生成图片
        # 从章节标题生成提示词
        prompt = f"创建一张与'{section}'相关的专业、高质量插图，适合用于文章配图"
        
        image_result = generator.generate_image(prompt)
        if image_result.get('success'):
            images.append({
                'section': section,
                'image': image_result
            })
    
    return images

# 新闻采集
def fetch_news(url, category=None):
    """从指定URL获取新闻内容"""
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f"获取页面失败: {response.status_code}"
            }
        
        # 这里应该使用BeautifulSoup等工具解析HTML
        # 简化处理，仅返回原始内容
        return {
            'content': response.text,
            'url': url,
            'category': category,
            'success': True
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# 平台发布
class ContentPublisher:
    def __init__(self):
        pass
    
    def publish_to_wechat(self, article, account):
        """发布文章到微信公众号"""
        app_id = account.get('app_id') or current_app.config.get('WECHAT_APP_ID')
        app_secret = account.get('app_secret') or current_app.config.get('WECHAT_APP_SECRET')
        
        if not app_id or not app_secret:
            return {
                'success': False,
                'error': '缺少微信公众号配置信息'
            }
        
        # 获取访问令牌
        token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        response = requests.get(token_url)
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f"获取微信访问令牌失败: {response.text}"
            }
        
        access_token = response.json().get('access_token')
        
        # 上传图片
        image_urls = []
        for image in article.get('images', []):
            media_url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image"
            with open(image.get('file_path'), 'rb') as f:
                files = {'media': f}
                media_response = requests.post(media_url, files=files)
                
                if media_response.status_code == 200:
                    media_id = media_response.json().get('media_id')
                    image_urls.append(media_id)
        
        # 发布文章
        publish_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
        
        articles = [{
            "title": article.get('title'),
            "thumb_media_id": image_urls[0] if image_urls else "",
            "author": article.get('author', ''),
            "digest": article.get('summary', ''),
            "content": article.get('content'),
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
        
        payload = {
            "articles": articles
        }
        
        publish_response = requests.post(publish_url, json=payload)
        
        if publish_response.status_code != 200:
            return {
                'success': False,
                'error': f"发布到微信公众号失败: {publish_response.text}"
            }
        
        media_id = publish_response.json().get('media_id')
        
        # 提交发布
        submit_url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
        submit_payload = {
            "media_id": media_id
        }
        
        submit_response = requests.post(submit_url, json=submit_payload)
        
        if submit_response.status_code != 200:
            return {
                'success': False,
                'error': f"提交发布失败: {submit_response.text}"
            }
        
        publish_id = submit_response.json().get('publish_id')
        
        return {
            'success': True,
            'platform': 'wechat',
            'article_id': publish_id
        }
    
    def publish_to_platform(self, article, platform, account):
        """发布文章到指定平台"""
        if platform == 'wechat':
            return self.publish_to_wechat(article, account)
        elif platform == 'zhihu':
            # 实现知乎发布逻辑
            pass
        elif platform == 'toutiao':
            # 实现头条号发布逻辑
            pass
        elif platform == 'baijiahao':
            # 实现百家号发布逻辑
            pass
        elif platform == 'sohu':
            # 实现搜狐号发布逻辑
            pass
        elif platform == 'weibo':
            # 实现微博发布逻辑
            pass
        else:
            return {
                'success': False,
                'error': f"不支持的平台: {platform}"
            }