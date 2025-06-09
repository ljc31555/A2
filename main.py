"""
AI 视频生成系统主入口
"""

import sys
import os
import signal
import traceback
import atexit
# 使用绝对路径并插入到sys.path开头
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from utils.logger import logger
from gui.new_main_window import NewMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import qInstallMessageHandler, QtMsgType

def qt_message_handler(mode, context, message):
    """处理Qt的调试信息和错误信息"""
    # 过滤掉一些不重要的Qt警告
    if mode == QtMsgType.QtWarningMsg:
        # 过滤QTextBlock和QTextCursor相关的警告，这些是Qt内部的非关键警告
        if "QTextBlock" in message or "QTextCursor" in message:
            return
    
    if mode == QtMsgType.QtDebugMsg:
        logger.debug(f"Qt Debug: {message}")
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning(f"Qt Warning: {message}")
    elif mode == QtMsgType.QtCriticalMsg:
        logger.error(f"Qt Critical: {message}")
    elif mode == QtMsgType.QtFatalMsg:
        logger.critical(f"Qt Fatal: {message}")
        # Qt致命错误时记录堆栈信息，但不让程序退出
        logger.critical(f"Qt Fatal Error Stack Trace: {''.join(traceback.format_stack())}")
        logger.warning("Qt致命错误已被捕获，程序继续运行")

def signal_handler(signum, frame):
    """处理系统信号"""
    logger.warning(f"收到系统信号 {signum}，但不强制退出程序")
    logger.warning(f"信号处理时的堆栈信息: {''.join(traceback.format_stack(frame))}")
    # 不直接调用sys.exit，让程序自然结束
    # sys.exit(1)

def exit_handler():
    """程序退出时的处理函数"""
    logger.info("程序正常退出")

if __name__ == "__main__":
    # 注册退出处理函数
    atexit.register(exit_handler)
    
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动时自动清空日志
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "system.log")
        #保留原有的日志内容，不再清空
        # if os.path.exists(log_path):
        #     with open(log_path, "w", encoding="utf-8") as f:
        #         f.write("")
        
        logger.info("=== 系统启动 ===")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {os.getcwd()}")
        logger.info(f"命令行参数: {sys.argv}")
        
        # 安装Qt消息处理器
        qInstallMessageHandler(qt_message_handler)
        logger.info("Qt消息处理器已安装")
        
        app = QApplication(sys.argv)
        logger.info("QApplication创建成功")
        
        # 设置应用程序图标
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            logger.info(f"应用程序图标已设置: {icon_path}")
        
        # 设置应用程序异常处理
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logger.critical(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
            logger.critical(f"异常堆栈: {''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
        
        sys.excepthook = handle_exception
        logger.info("全局异常处理器已安装")
        
        window = NewMainWindow()
        logger.info("NewMainWindow创建成功")
        
        window.show()
        logger.info("NewMainWindow显示成功，开始事件循环")

        exit_code = app.exec_()
        logger.info(f"事件循环结束，退出码: {exit_code}")
        
        del window  # 在事件循环退出后销毁 NewMainWindow，确保组件生命周期完整
        logger.info("NewMainWindow已销毁")
        
        sys.exit(exit_code)
        
    except SystemExit as e:
        # logger.warning(f"捕获到SystemExit异常: {str(e)}，但不退出程序")
        # logger.warning(f"系统退出堆栈: {traceback.format_exc()}")
        # 不重新抛出SystemExit异常，让程序继续运行
        # 重新启动事件循环
        try:
            if 'window' in locals() and window:
                logger.info("重新启动Qt事件循环")
                exit_code = app.exec_()
                logger.info(f"事件循环重新结束，退出码: {exit_code}")
        except Exception as restart_error:
            logger.error(f"重新启动事件循环失败: {restart_error}")
        # raise
    except ImportError as e:
        logger.critical(f"导入模块失败: {e}")
        logger.critical(f"导入错误堆栈: {traceback.format_exc()}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"主程序异常退出: {e}")
        logger.critical(f"异常类型: {type(e).__name__}")
        logger.critical(f"异常堆栈: {traceback.format_exc()}")
        print(f"程序发生错误: {e}")
        sys.exit(1)
    finally:
        logger.info("=== 程序结束 ===")