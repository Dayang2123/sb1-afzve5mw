# AIContentHub
AI-powered content creation and publishing platform with features for AI-generated articles, image generation, multi-platform publishing, and content management.

## 下载项目
您可以通过以下链接下载完整的项目代码：
[下载AIContentHub.zip](https://work-2-rgodiiaotguweuxy.prod-runtime.all-hands.dev/AIContentHub.zip)

## 项目说明
AIContentHub是一个功能强大的内容创作和发布平台，具有以下特点：
- 支持AI自动生成文章内容
- 根据文章内容自动生成配图
- 过滤法律违禁词和广告法敏感词
- 支持多平台发布（微信公众号、知乎、头条号、百家号、搜狐号、微博等）
- 内容管理仪表盘
- 美观的用户界面和简单的操作流程

## 安装说明
1. 下载并解压AIContentHub.zip
2. 安装所需依赖：
   ```
   pip install -r AIContentHub/requirements.txt
   ```
3. 初始化数据库：
   ```
   python AIContentHub/init_db.py
   ```
4. 启动应用：
   ```
   python AIContentHub/run.py
   ```
5. 在另一个终端启动后台任务处理器：
   ```
   python AIContentHub/worker.py
   ```
6. 访问 http://localhost:5000 开始使用

## 主要功能
### 1. 内容创作
- AI辅助内容生成：支持OpenAI和百度文心一言等多种AI引擎
- 热点资讯采集：自动获取热门话题和新闻
- 内容编辑：支持手动编辑标题和正文
- 敏感词过滤：自动过滤法律违禁词和广告法敏感词

### 2. 图片生成
- 根据文章内容自动生成相关图片
- 支持多种图片生成引擎
- 图片历史记录和管理

### 3. 多平台发布
- 微信公众号：通过AppID和AppSecret自动发布
- 知乎、头条号、百家号、搜狐号、微博等平台支持
- 发布状态跟踪和管理

### 4. 内容管理
- 草稿管理：保存和编辑草稿
- 发布历史：查看已发布内容
- 数据统计：创作和发布数据分析
- 用户管理：多用户支持

## 系统要求
- 操作系统：Windows 10或更高版本
- Python 3.8或更高版本
- 网络连接（用于API调用和内容发布）
- 各平台的API密钥和账号信息

## 配置说明
系统配置文件位于`AIContentHub/config/config.py`，您需要配置以下内容：

1. AI API设置
   - OpenAI API密钥
   - 百度文心一言API密钥
   - 其他AI服务提供商的API密钥

2. 平台账号设置
   - 微信公众号的AppID和AppSecret
   - 知乎、头条号、百家号、搜狐号、微博等平台的账号和密码

3. 敏感词设置
   - 法律违禁词列表
   - 广告法敏感词列表

## 使用说明
1. 登录系统
   - 使用默认管理员账号：admin/admin123
   - 或注册新用户

2. 配置API和平台账号
   - 在设置页面配置AI API密钥
   - 添加各平台的账号信息
   - 自定义敏感词列表

3. 创建内容
   - 选择AI生成内容或手动创建
   - 编辑标题和正文
   - 生成配图

4. 发布内容
   - 选择目标平台
   - 设置发布时间
   - 提交发布任务

5. 管理内容
   - 查看发布状态
   - 管理草稿
   - 查看数据统计

## 联系方式
如有任何问题或建议，请联系开发者。
