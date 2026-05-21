@echo off
chcp 65001 >nul
echo ============================================================
echo EUDAMED批量注册XML转换工具 v2.1
echo ============================================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    echo 请确保已安装Python 3.7或更高版本
    pause
    exit /b 1
)

REM 检查模板文件
if not exist "templates\EUDAMED_Template_v2.xlsx" (
    echo 错误: 未找到模板文件 templates\EUDAMED_Template_v2.xlsx
    pause
    exit /b 1
)

echo 正在运行转换程序...
echo.

REM 运行转换程序
python eudamed_converter_v2.1.py --input templates\EUDAMED_Template_v2.xlsx

echo.
echo ============================================================
echo 按任意键退出...
pause >nul
