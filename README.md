# Noita存档备份程序

此脚本的UI部分是使用中文来写的，没有做英文适配，所以Readme里我也不写英文了。
Python版本：3.10.10

> （我是初学者，写代码比较菜）
> 详细介绍请看Bilibili专栏：https://www.bilibili.com/read/cv41214908/

# 构建方法

- 在合适的路径中打开 Powershell
- 先将工程拉到本地：`git clone https://github.com/Iamsleepingnow/Noita_Archive_SaveAndLoad_Script.git`
- 进入工程路径：`cd Noita_Archive_SaveAndLoad_Script`
- 然后构建Python虚拟环境：`python -m venv ./venv/`
- 激活该环境，安装模块：`./venv/Scripts/activate` -> `python -m pip install -r requirements.txt`
- 在该环境中运行py脚本：`python NoitaSLScript3.py`

# 打包

- 可以使用Pyinstaller来打包：
  - 使用之前的方法进入工程中的Python虚拟环境
  - 使用`python -m pip install pyinstaller`来安装一下pyinstaller
  - 对py脚本进行打包：`pyinstaller -F --noconsole -n <程序名称> -i ./UI/Icon.ico NoitaSLScript3.py`
  - 当Powershell提示`INFO: Build complete!`后，将`./dist/`中的exe执行文件、`./UI`文件夹、`./Images`文件夹放在同一路径中即可完成打包
