# AI内容创作平台

AI内容创作平台是一个功能强大的内容创作和发布工具，利用人工智能技术自动生成高质量文章，并支持一键发布到多个平台。

## 主要功能

- **AI内容生成**：自动生成3000字以上的深度文章
- **智能配图**：根据文章内容自动生成相关图片
- **敏感词过滤**：自动过滤法律违禁词和广告法敏感词
- **多平台发布**：支持一键发布到微信公众号、知乎、头条号等平台
- **内容管理**：完善的文章、草稿和图片管理功能
- **数据分析**：提供详细的内容创作和发布数据分析

## 技术栈

- **后端**：Python + Flask
- **前端**：HTML + CSS + JavaScript + Bootstrap 5
- **数据库**：SQLite（可扩展到MySQL、PostgreSQL）
- **AI接口**：支持OpenAI、百度文心一言等多种AI模型

## 安装与运行

### 环境要求

- Python 3.8+
- pip

### 安装步骤

1. 克隆代码库

```bash
git clone https://github.com/yourusername/ai-content-hub.git
cd ai-content-hub
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

复制`.env.example`文件为`.env`，并填写相关配置：

```bash
cp .env.example .env
# 编辑.env文件，填写API密钥等信息
```

4. 初始化数据库

```bash
python init_db.py
```

5. 运行应用

```bash
python run.py
```

应用将在 http://localhost:12000 运行。

### 后台任务处理

启动后台任务处理器：

```bash
python worker.py
```

## 使用指南

1. 注册并登录系统
2. 配置AI API密钥（设置 -> API配置）
3. 配置发布平台账号（设置 -> 平台账号）
4. 使用AI生成文章或手动创建文章
5. 编辑文章内容，添加或生成图片
6. 选择目标平台发布文章

## 配置说明

### AI API配置

- **OpenAI**：需要提供API密钥
- **百度文心一言**：需要提供API密钥和Secret Key
- **讯飞星火**：需要提供AppID、API密钥和Secret

### 平台发布配置

- **微信公众号**：需要提供AppID和AppSecret
- **知乎**：需要提供用户名和密码
- **头条号**：需要提供用户名和密码
- **百家号**：需要提供用户名和密码
- **搜狐号**：需要提供用户名和密码
- **微博**：需要提供用户名和密码

## 许可证

MIT

## 联系方式

如有问题或建议，请联系：your-email@example.com