@echo off
:: ==============================================================================
:: 脚本名称: deploy.bat
:: 适用环境: Windows 10 / Windows 11 (CMD / PowerShell / 直接双击)
:: 脚本功能: 自动化配置工业级.gitignore、自动生成纯净项目树、一键推送GitHub
:: ==============================================================================
chcp 65001 >nul
echo ======================================================================
echo  开始执行 Windows 环境下无人机/视觉项目自动化 Git 部署流...
echo ======================================================================

:: ------------------------------------------------------------------------------
:: 【配置核心】：未来如果开新仓库，只需要修改下面这一行真正的 GitHub 网址即可！
:: ------------------------------------------------------------------------------
set "REMOTE_URL=https://github.com/Fantastic-Jing/uav-autonomous-navigation-and-trajectory-planning.git"


:: 1. 自动化写入符合 UAV/MATLAB/ROS 规范的 .gitignore
echo 1. 正在本地生成工业级 .gitignore 防火墙...
(
echo # MATLAB 编译与自动保存缓存
echo *.asv
echo *.slxc
echo *.mex*
echo *.mat
echo matrix_log.txt
echo.
echo # ROS / C++ 编译与中间件产物
echo devel/
echo logs/
echo build/
echo bin/
echo lib/
echo .catkin_workspace
echo .catkin_tools/
echo.
echo # 操作系统与集成环境缓存
echo .DS_Store
echo Thumbs.db
echo .vscode/
echo .idea/
echo *.workspace
echo.
echo # 排除自动化脚本自身
echo deploy.bat
) > .gitignore
echo ✅ .gitignore 创建成功。

:: 2. 利用 Windows 原生机制与 Git 引擎生成绝对纯净的目录树
echo 2. 正在调用 Git 引擎扫描工作区拓扑，过滤垃圾缓存...
set "TREE_FILE=temp_tree.txt"
if exist "%TREE_FILE%" del "%TREE_FILE%"

:: 核心逻辑：利用 git ls-files 借刀杀人，只列出被 Git 追踪的合规文件，完美规避垃圾多余文件
for /f "tokens=*" %%i in ('git ls-files') do (
    echo %%i >> "%TREE_FILE%"
)
:: 如果是完全未初始化的空库，则用原生 dir 兜底列出当前一级目录
if not exist "%TREE_FILE%" (
    dir /b /a-d > "%TREE_FILE%"
)

:: 3. 自动化创建/覆盖符合评审标准的精简版 README.md
echo 3. 正在初始化 README.md 骨架并注入拓扑结构...
(
echo # UAV Autonomous Navigation and Trajectory Planning
echo.
echo An end-to-end industrial computer vision and autonomous robotics repository focusing on quadrotor state estimation, dynamic obstacle avoidance, and optimal trajectory generation.
echo.
echo ## 1. Project Directory Topology
echo ```text
) > README.md

:: 将过滤出来的纯净目录树追加导入到 README 中
if exist "%TREE_FILE%" (
    type "%TREE_FILE%" >> README.md
    del "%TREE_FILE%"
)

(
echo ```
echo.
echo ## 2. Mathematical Framework ^& Implementation
echo *(Algorithm formulas and flight verification figures will be generated systematically during development)*
) >> README.md
echo ✅ README.md 部署成功，纯净文件树已完美嵌入。

:: 4. 执行本地 Git 核心状态机控制流
echo 4. 启动本地 Git 核心状态机...
git init
git add .
git commit -m "feat: initial release of structured autonomous UAV platform with explicit gitignore boundaries"
git branch -M main

:: 5. 强行重置并绑定远程 GitHub 仓库，执行全量推送
echo 5. 建立云端物理链条 -^> %REMOTE_URL%
git remote remove origin >nul 2>&1
git remote add origin %REMOTE_URL%

echo 正在将本地代码流无缝同步至 GitHub 远程 main 分支...
git push -u origin main

echo ======================================================================
echo 🎉 恭喜！Windows 自动化全量部署圆满完成！
echo 您的 GitHub 仓库已完美就绪。
echo ======================================================================
pause