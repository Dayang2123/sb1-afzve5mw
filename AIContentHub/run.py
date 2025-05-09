import os
from app import create_app
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 12000))
    app.run(host='0.0.0.0', port=port, debug=True)