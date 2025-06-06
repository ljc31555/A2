@echo off
chcp 65001 >nul
echo ========================================
echo     AI视频生成器 - Git版本控制设置
echo ========================================
echo.

echo [1/6] 检查Git是否已安装...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git未安装，请先安装Git: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git已安装

echo.
echo [2/6] 初始化Git仓库...
git init
if errorlevel 1 (
    echo ❌ Git初始化失败
    pause
    exit /b 1
)
echo ✅ Git仓库初始化成功

echo.
echo [3/6] 创建.gitignore文件...
echo # Python > .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo *.so >> .gitignore
echo .Python >> .gitignore
echo build/ >> .gitignore
echo develop-eggs/ >> .gitignore
echo dist/ >> .gitignore
echo downloads/ >> .gitignore
echo eggs/ >> .gitignore
echo .eggs/ >> .gitignore
echo lib/ >> .gitignore
echo lib64/ >> .gitignore
echo parts/ >> .gitignore
echo sdist/ >> .gitignore
echo var/ >> .gitignore
echo wheels/ >> .gitignore
echo *.egg-info/ >> .gitignore
echo .installed.cfg >> .gitignore
echo *.egg >> .gitignore
echo. >> .gitignore
echo # 虚拟环境 >> .gitignore
echo .venv/ >> .gitignore
echo venv/ >> .gitignore
echo ENV/ >> .gitignore
echo env/ >> .gitignore
echo. >> .gitignore
echo # IDE >> .gitignore
echo .vscode/ >> .gitignore
echo .idea/ >> .gitignore
echo *.swp >> .gitignore
echo *.swo >> .gitignore
echo *~ >> .gitignore
echo. >> .gitignore
echo # 项目特定 >> .gitignore
echo logs/ >> .gitignore
echo output/ >> .gitignore
echo config/projects/ >> .gitignore
echo *.log >> .gitignore
echo. >> .gitignore
echo # 临时文件 >> .gitignore
echo *.tmp >> .gitignore
echo *.bak >> .gitignore
echo *.old >> .gitignore
echo temp/ >> .gitignore
echo. >> .gitignore
echo # 敏感信息 >> .gitignore
echo *.key >> .gitignore
echo *.secret >> .gitignore
echo config/*_config.json >> .gitignore
echo ✅ .gitignore文件创建成功

echo.
echo [4/6] 配置Git用户信息...
set /p username="请输入您的用户名: "
set /p email="请输入您的邮箱: "
git config user.name "%username%"
git config user.email "%email%"
echo ✅ Git用户信息配置成功

echo.
echo [5/6] 添加所有文件到Git...
git add .
if errorlevel 1 (
    echo ❌ 添加文件失败
    pause
    exit /b 1
)
echo ✅ 文件添加成功

echo.
echo [6/6] 创建初始提交...
git commit -m "初始提交：AI视频生成器项目基础版本 - 包含改进的种子设置功能"
if errorlevel 1 (
    echo ❌ 提交失败
    pause
    exit /b 1
)
echo ✅ 初始提交成功

echo.
echo [额外] 创建开发分支...
git branch develop
git checkout develop
echo ✅ 开发分支创建成功

echo.
echo ========================================
echo           🎉 设置完成！
echo ========================================
echo.
echo 接下来您可以：
echo 1. 在GitHub/Gitee创建远程仓库
echo 2. 使用以下命令连接远程仓库：
echo    git remote add origin [您的仓库地址]
echo    git push -u origin main
echo    git push -u origin develop
echo.
echo 3. 日常开发流程：
echo    - 开发新功能前：git checkout -b feature/功能名
echo    - 完成开发后：git add . && git commit -m "描述"
echo    - 合并功能：git checkout develop && git merge feature/功能名
echo.
echo 详细说明请查看：版本控制指南.md
echo.
pause