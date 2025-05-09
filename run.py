import os
import sys
from app import create_app
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = create_app()

if __name__ == '__main__':
    # 从命令行参数获取端口
    port = 12001
    host = '0.0.0.0'
    
    # 解析命令行参数
    for i, arg in enumerate(sys.argv):
        if arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
        elif arg.startswith('--port='):
            port = int(arg.split('=')[1])
        elif arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg.startswith('--host='):
            host = arg.split('=')[1]
    
    print(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=True)