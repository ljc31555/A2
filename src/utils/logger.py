import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOG_FILE = os.path.join(PROJECT_ROOT, 'logs', 'system.log')

class Logger:
    def __init__(self, name='AIVideoLogger', level=logging.DEBUG, fmt=None, remote_url=None, console_output=True):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 详细的日志格式，包含更多上下文信息
        log_format = fmt or '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] [%(funcName)s] %(message)s'
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        
        # 清除现有的处理器，避免重复
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 文件处理器 - 使用RotatingFileHandler避免日志文件过大
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(LOG_FILE)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 清空上一次的日志内容
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'w', encoding='utf-8') as f:
                    f.write('')  # 清空文件内容
                
            fh = RotatingFileHandler(
                LOG_FILE, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            fh.setLevel(level)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        except Exception as e:
            print(f"创建文件日志处理器失败: {e}", file=sys.stderr)
        
        # 控制台处理器 - 用于实时查看日志
        if console_output:
            try:
                ch = logging.StreamHandler(sys.stdout)
                ch.setLevel(level)
                ch.setFormatter(formatter)
                self.logger.addHandler(ch)
            except Exception as e:
                print(f"创建控制台日志处理器失败: {e}", file=sys.stderr)

    def get_logger(self):
        return self.logger

# 全局日志记录器实例
# logger = Logger().get_logger()

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

    def exception(self, msg):
        self.logger.exception(msg)
        
    def flush(self):
        """强制刷新日志到文件"""
        try:
            for handler in self.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        except Exception as e:
            # 如果flush失败，不要影响程序运行
            pass

# 创建全局logger实例
_logger_instance = Logger()
logger = _logger_instance.logger

# 为标准logger对象添加flush方法，以兼容现有代码
def _logger_flush():
    """为标准logger添加flush方法"""
    _logger_instance.flush()

# 动态添加flush方法到logger对象
logger.flush = _logger_flush