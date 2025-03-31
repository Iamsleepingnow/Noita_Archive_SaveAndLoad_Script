# 开发者：_Iamsleepingnow
# 开发时间：2025-03-30 15:28
# 开发功能：Noita存档备份程序3.0
# encoding = utf-8
# -----------------------------------------
import os, sys, json, shutil, uuid, random, psutil
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QFontDatabase, QCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QLineEdit, QTextEdit, QLabel, QMessageBox, QScrollBar, QSizePolicy
)

# 定义全局变量
user_manual = '''
🧩脚本介绍🧩
- 此脚本用于实现半自动Noita存读档，通过复制替换原存档save00来完成（save00是游戏的当前存档路径）。
- 在使用脚本之前，需要事先在游戏中关闭steam云存档，否则脚本不会正常工作。
- 在使用此脚本前，请务必要先将你的“save00”存档进行手动备份，数据无价，潜在的程序bug或误操作造成的丢档的损失作者将不予承担。

🛠️如何使用🛠️
1. 在需要保存游戏进度的时候，点游戏内部的“保存与退出”来手动保存游戏，待游戏正常退出后进入下一步：
2. 点击脚本中的“新建存档栏位”，这时就能在下面的窗口中看见一个存档表单，注意：目前该存档是空存档，重启脚本后该空存档会被自动移除。
3. 点击存档栏位中的“备份存档”，这时会将游戏存档“save00”复制一份并覆盖该存档栏位，这个过程需要一定时间，请耐心等待。当弹出成功提示时，代表该栏位不再是空存档了，重启脚本后该存档会被永久记录。
4. 当点击存档栏位中的“替换存档”时，程序会将该栏位中的存档复制一份来替换“save00”存档。在该流程进行过程中请不要随便关闭脚本或开启游戏。
5. 当替换存档弹出成功提示时，代表存档被替换完成，这时才能打开游戏并继续游戏。
6. 当点击存档栏位中的“删除存档”时，程序会移除该栏位的存档，该操作不会影响“save00”存档。

🧾其他事项🧾
- 备份中的存档会被放置在总存档路径中，一般前缀为“save00”，如果脚本丢失了存档栏位的信息，可以将备份的存档进行手动重命名来替换“save00”存档。
- 脚本的存档记录文件“archives.json”被放置在脚本的同级目录中，里面记录了存档的位置以及id号，除非出现了存档bug，否则不要删除它。
- 每当有存档栏位备份存档时，都会在存档路径中更新“save00_Safe”安全存档，也就是说，安全存档永远是最后一次备份的存档，当存档崩溃时可以通过安全存档找回。
''' # 用户手册
font_path = ".\\UI\\unifont.ttf" # 全局字体路径
image_path = ".\\Images" # 图片路径
title_text = 'NOITA存档备份3.0' # 标题文本
basic_color_A = '#8777ae' # 基础色：紫色
basic_color_B = '#cfbf6f' # 基础色：黄色
basic_color_C = '#000000' # 基础色：黑色
basic_color_D = '#ffffff' # 基础色：白色
scrollbar_stylesheet = '''
    QScrollBar:vertical{
        margin:16px 0px 16px 0px; background-color:#8777ae; border:1px #000000; width:18px;
    }
    QScrollBar::handle:vertical{
        background-color:#000000; border:1px #000000; border-radius:1px; width:18px;
    }
    QScrollBar::handle:vertical:hover{
        background-color:#ffffff;
    }
    QScrollBar::sub-line:vertical{
        subcontrol-position:top; subcontrol-origin:margin;
        background-color:#8777ae; border:1px solid #8777ae; height:16px;
    }
    QScrollBar::add-line:vertical{
        subcontrol-position:bottom; subcontrol-origin:margin;
        background-color:#8777ae; border:1px solid #8777ae; height:16px;
    }
    QScrollBar::up-arrow:vertical{
        width:12px; height:6px;
    }
    QScrollBar::down-arrow:vertical{
        width:12px; height:6px;
    }
    QScrollBar::sub-page:vertical,QScrollBar::add-page:vertical{
        background-color:#8777ae;
    }
''' # 滚动条样式表

# 存档管理器类
class ArchiveManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_path = os.path.join(os.getenv("LOCALAPPDATA") + "Low", "Nolla_Games_Noita")
        self.config_file = "archives.json"
        self.archives = []
        self.allow_close = True
        self.init_ui()
        self.load_archives()

    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle("Noita 存档备份程序 V3.0  by _Iamsleepingnow Bilibili")
        self.resize(1280, 1280)
        self.setMinimumSize(890, 620)
        self.setStyleSheet("background-color: {0};".format(basic_color_A))

        # 设置主窗口
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 获取全局字体
        fontId = QFontDatabase.addApplicationFont(font_path)
        fontFamily = QFontDatabase.applicationFontFamilies(fontId)
        self.font_name = ''
        if fontFamily:
            self.font_name = fontFamily[0]

        # 标题
        self.title_label = QLabel(title_text, self)
        self.title_label.setFont(QFont(self.font_name, 24))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("background-color: {0};".format(basic_color_B))
        self.title_label.setMargin(10)
        layout.addWidget(self.title_label)

        # 顶部按钮
        btn_layout = QHBoxLayout()
        self.btn_new = self.add_pushbutton('📮新建存档栏位📮', f'border: 5px solid {basic_color_C}; margin: 0px;'
                                                           f'background-color: {basic_color_B};', 14, -1, 70)
        self.btn_new.clicked.connect(self.create_new_archive)
        btn_layout.addWidget(self.btn_new)
        self.btn_open = self.add_pushbutton('🚧打开存档路径🚧', f'border: 5px solid {basic_color_C}; margin: 0px;'
                                                            f'background-color: {basic_color_B};', 14, -1, 70)
        self.btn_open.clicked.connect(self.open_archive_dir)
        btn_layout.addWidget(self.btn_open)
        self.btn_info = self.add_pushbutton('📖功能使用说明📖', f'border: 5px solid {basic_color_C}; margin: 0px;'
                                                              f'background-color: {basic_color_B};', 14, -1, 70)
        self.btn_info.clicked.connect(self.open_manual_tip)
        btn_layout.addWidget(self.btn_info)
        layout.addLayout(btn_layout)

        # 滚动区域
        scrollbar = QScrollBar() # 创建滚动条
        scrollbar.setStyleSheet(scrollbar_stylesheet)
        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBar(scrollbar)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setViewportMargins(0, 0, 0, 0)
        self.scroll.setStyleSheet(f'border: 3px solid {basic_color_C};')
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

    # 实用功能
    def add_pushbutton(self, title, stylesheet, font_size, max_width, min_height):
        """ 创建QPushButton按钮 """
        btn = QPushButton(title) # 创建QPushButton实例并设置标题
        btn.setStyleSheet(stylesheet) # 设置QPushButton的样式表
        btn.setFont(QFont(self.font_name, font_size)) # 设置QPushButton的字体大小
        btn.setCursor(QCursor(Qt.PointingHandCursor)) # 设置QPushButton的光标为指向手形状
        if max_width != -1: # 如果max_width不为-1，则设置QPushButton的最大宽度
            btn.setMaximumWidth(max_width)
            btn.setMinimumWidth(max_width)
        if min_height != -1: # 如果min_height不为-1，则设置QPushButton的最小高度
            btn.setMaximumHeight(min_height)
            btn.setMinimumHeight(min_height)
        return btn

    def open_archive_dir(self):
        """打开总存档目录"""
        target_dir = self.game_path
        if not os.path.exists(target_dir):
            self.open_warning_box("错误", "存档目录不存在！", QMessageBox.Ok)
            return
        try:
            os.startfile(target_dir) # Windows打开路径
        except Exception as e:
            self.open_warning_box("错误", f"无法打开目录：{str(e)}", QMessageBox.Ok)

    def open_archive_dir_by_id(self, archive_id):
        """通过ID号打开存档目录"""
        archive_path = os.path.join(self.game_path, f"save00_{archive_id}")
        if not os.path.exists(archive_path):
            self.open_warning_box("错误", "存档目录不存在！", QMessageBox.Ok)
            return

        try:
            os.startfile(archive_path)  # Windows打开路径
        except Exception as e:
            self.open_warning_box("错误", f"无法打开目录：{str(e)}", QMessageBox.Ok)

    def open_manual_tip(self):
        """打开用户手册"""
        box = QMessageBox()
        box.setFont(QFont(self.font_name, 12))
        box.setWindowTitle("使用说明")
        box.setText(user_manual)
        box.setStandardButtons(QMessageBox.Yes)
        box.setStyleSheet('QLabel{' + f'border: 3px solid {basic_color_C};'
                                 f'background-color: {basic_color_B}; min-width: 800px; padding: 10px;' + '}')
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        box.exec_()

    def open_warning_box(self, title, text, choices):
        """打开警告框"""
        box = QMessageBox()
        box.setFont(QFont(self.font_name, 12))
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(choices)
        box.setStyleSheet('QLabel{' + f'border: 3px solid {basic_color_C};'
                                 f'background-color: {basic_color_B}; min-width: 800px; padding: 10px; alignment: center;' + '}')
        box.exec_()
        return box.result()

    def get_random_imagepath(self):
        """获取随机图片路径"""
        try:
            image_list = os.listdir(image_path)
            if not image_list:
                self.open_warning_box("错误", "图片目录为空！", QMessageBox.Ok)
                return None

            # 使用更安全的路径拼接方式
            return os.path.join(image_path, random.choice(image_list))

        except Exception as e:
            self.open_warning_box("错误", f"访问图片目录失败：{str(e)}", QMessageBox.Ok)
            return None

    def get_pixmap_from_imagepath(self, image_path, width, height):
        """使用图片路径构建QPixmap"""
        try:
            pixmap = QPixmap(image_path)
            proporation = pixmap.height() / pixmap.width()
            pixmap.setDevicePixelRatio(proporation)
            pixmap = pixmap.scaled(width, height)
            return pixmap
        except Exception as e:
            self.open_warning_box("错误", f"图像加载失败，请检查图像路径是否正确。\n{e}", QMessageBox.Ok)
            return QPixmap()

    def check_game_running(self):
        """检测Noita进程是否在运行"""
        if psutil is None:
            self.open_warning_box("错误", "缺少依赖库psutil，无法进行进程检测", QMessageBox.Ok)
            return False  # 假设允许操作继续

        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'noita.exe':
                    return True
            return False
        except Exception as e:
            self.open_warning_box("错误", f"进程检测失败：{str(e)}", QMessageBox.Ok)
            return False

    def show_game_running_warning(self):
        """显示游戏运行警告对话框"""
        return self.open_warning_box(
            "警告",
            "检测到Noita游戏正在运行！\n"
            "💣️在游戏运行时操作存档可能导致数据丢失💣️\n\n"
            "确定要操作吗？\n\n"
            "虽然不影响存档的正常游玩，但是可能会出现一些不可预料的情况：\n"
            "1. 战争迷雾信息丢失\n"
            "2. 游戏背景贴图丢失\n"
            "2. 米娜被卡在墙里\n"
            "3. 进度可能会回退\n",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes

    # 存档栏位管理
    def load_archives(self):
        """加载存档数据"""
        try:
            with open(self.config_file, "r") as f:
                saved_archives = json.load(f)

            valid_archives = []
            for archive in saved_archives:
                # 验证路径格式
                if not archive["path"].startswith(self.game_path):
                    continue
                # 路径存在性检查
                if not os.path.exists(archive["path"]):
                    continue
                valid_archives.append(archive)

            self.archives = valid_archives
            for archive in self.archives:
                self.add_archive_item(archive)

            self.save_archives()  # 自动清理无效存档

        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            self.open_warning_box(self, "错误", "配置文件损坏，已重置存档列表。")

    def save_archives(self):
        """保存存档数据"""
        with open(self.config_file, "w") as f:
            json.dump(self.archives, f, indent=2)

    def update_archive_metadata(self, archive_id, title, comment, picture):
        """更新存档元数据"""
        for archive in self.archives:
            if archive["id"] == archive_id:
                archive["title"] = title
                archive["comment"] = comment
                archive["picture"] = picture
        self.save_archives()

    def create_new_archive(self):
        """创建新存档"""
        # 生成唯一路径
        while True:
            archive_id = str(uuid.uuid4())
            new_path = os.path.join(self.game_path, f"save00_{archive_id}")
            if not os.path.exists(new_path):
                break
        # 生成图片地址
        random_image_path = self.get_random_imagepath()
        archive_data = {
            "id": archive_id,
            "title": "新存档",
            "comment": "",
            "picture": random_image_path,
            "path": new_path
        }
        self.archives.append(archive_data)
        self.add_archive_item(archive_data)
        self.save_archives()

    def add_archive_item(self, archive_data):
        """添加存档条目"""
        item = ArchiveItem(
            self,
            archive_data["id"],
            archive_data["title"],
            archive_data["comment"],
            archive_data["picture"],
            archive_data["path"]
        )
        self.scroll_layout.addWidget(item)

    # 关闭事件处理（重写）
    def closeEvent(self, event):
        """重写关闭事件处理"""
        if self.allow_close:
            event.accept()
        else:
            event.ignore()
            # 可选：添加操作中的提示
            self.open_warning_box("操作进行中", "米娜别急，请等待当前操作完成后再关闭程序", QMessageBox.Ok)

    # 存档修改方法
    def backup_archive(self, archive_id):
        """备份存档"""
        if self.check_game_running() and not self.show_game_running_warning():
            return  # 用户取消操作
        archive = next(a for a in self.archives if a["id"] == archive_id)
        src = os.path.join(self.game_path, "save00")
        dest = archive["path"]

        if not os.path.exists(src):
            self.open_warning_box("错误", "未找到游戏存档目录！请检查C:\\Users\\[用户名]\\AppData\\LocalLow\\Nolla_Games_Noita\\save00路径是否合法。", QMessageBox.Ok)
            return

        self.current_worker = FileWorker(src, dest, "backup", self.game_path)
        self.current_worker.finished.connect(
            lambda d, s, e: self.on_operation_finished(archive_id, s, e)
        )
        self.toggle_buttons(False)
        self.allow_close = False  # 禁止关闭
        self.title_label.setText("正在备份文件，请不要关闭窗口！")
        self.current_worker.start()

    def restore_archive(self, archive_id):
        """恢复存档"""
        if self.check_game_running() and not self.show_game_running_warning():
            return
        archive = next(a for a in self.archives if a["id"] == archive_id)
        src = archive["path"]
        dest = os.path.join(self.game_path, "save00")

        if not os.path.exists(src):
            self.open_warning_box(
                "警告",
                "备份存档不存在！\n"
                "请检查存档是否未进行备份，或列表中该存档的备份路径是否正确。",
                QMessageBox.Yes
            )
            return

        self.current_worker = FileWorker(src, dest, "restore")
        self.current_worker.finished.connect(
            lambda d, s, e: self.on_operation_finished(archive_id, s, e)
        )
        self.toggle_buttons(False)
        self.allow_close = False  # 禁止关闭
        self.title_label.setText("正在覆盖文件，请不要关闭窗口！")
        self.current_worker.start()

    def delete_archive(self, archive_id):
        """删除存档"""
        if any(a["id"] == archive_id and a["path"].endswith("_Safe") # 在删除操作前添加安全存档保护检查
               for a in self.archives):
            self.open_warning_box("保护机制", "安全存档受保护不可删除", QMessageBox.Ok)
            return

        if self.check_game_running() and not self.show_game_running_warning():
            return
        reply = self.open_warning_box(
            "确认删除", "确定要删除这个备份吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        archive = next(a for a in self.archives if a["id"] == archive_id)
        self.current_worker = FileWorker(None, archive["path"], "delete")
        self.current_worker.finished.connect(
            lambda d, s, e: self.on_delete_finished(archive_id, s, e)
        )
        self.toggle_buttons(False)
        self.allow_close = False  # 禁止关闭
        self.title_label.setText("正在删除文件，请不要关闭窗口！")
        self.current_worker.start()

    def on_operation_finished(self, archive_id, success, error_msg):
        """当操作结束时"""
        self.toggle_buttons(True)
        self.allow_close = True  # 恢复关闭
        self.title_label.setText(title_text)
        if success:
            self.open_warning_box("成功", f"操作已完成。\n存档Id：{archive_id}", QMessageBox.Ok)
        else:
            self.open_warning_box("错误", f"操作失败：\n{error_msg}", QMessageBox.Ok)

    def on_delete_finished(self, archive_id, success, error_msg):
        """当删除结束时"""
        self.toggle_buttons(True)
        self.allow_close = True  # 恢复关闭
        self.title_label.setText(title_text)
        if success:
            # 从界面和配置中移除
            self.archives = [a for a in self.archives if a["id"] != archive_id]
            for i in reversed(range(self.scroll_layout.count())):
                widget = self.scroll_layout.itemAt(i).widget()
                if widget.archive_id == archive_id:
                    widget.deleteLater()
                    break
            self.save_archives()
            self.open_warning_box("成功", f"已删除备份：{archive_id}", QMessageBox.Ok)
        else:
            self.open_warning_box("错误", f"删除失败：\n{error_msg}", QMessageBox.Ok)

    # 启用或禁用按钮
    def toggle_buttons(self, enabled):
        """统一控制按钮状态"""
        self.btn_new.setEnabled(enabled)
        self.btn_open.setEnabled(enabled)
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.btn_backup.setEnabled(enabled)
                widget.btn_restore.setEnabled(enabled)
                widget.btn_delete.setEnabled(enabled)
                widget.btn_up.setEnabled(enabled)
                widget.btn_down.setEnabled(enabled)

    # 上下移动存档
    def move_archive_up(self, archive_id):
        """上移存档项"""
        # 查找存档索引
        index = next((i for i, a in enumerate(self.archives) if a["id"] == archive_id), -1)
        if index <= 0:
            return
        # 调整数据顺序
        self.archives.insert(index - 1, self.archives.pop(index))

        # 调整界面顺序
        item = self.scroll_layout.takeAt(index)
        self.scroll_layout.insertWidget(index - 1, item.widget())

        self.save_archives()

    def move_archive_down(self, archive_id):
        """下移存档项"""
        # 查找存档索引
        index = next((i for i, a in enumerate(self.archives) if a["id"] == archive_id), -1)
        if index == -1 or index >= len(self.archives) - 1:
            return
        # 调整数据顺序
        self.archives.insert(index + 1, self.archives.pop(index))

        # 调整界面顺序
        item = self.scroll_layout.takeAt(index)
        self.scroll_layout.insertWidget(index + 1, item.widget())

        self.save_archives()

# 存档栏位子窗口
class ArchiveItem(QFrame):
    def __init__(self, parent, archive_id, title, comment, picture, path):
        super().__init__()
        self.parent = parent
        self.archive_id = archive_id
        self.init_ui(title, comment, picture, path)

    def init_ui(self, title, comment, picture, path):
        # 获取全局字体
        fontId = QFontDatabase.addApplicationFont(font_path)
        fontFamily = QFontDatabase.applicationFontFamilies(fontId)
        self.font_name = ''
        if fontFamily:
            self.font_name = fontFamily[0]

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setStyleSheet(f"border: 3px solid {basic_color_C};"
                           f"margin: 0px; padding: 3px; background-color: {basic_color_B};")
        self.setFixedHeight(250)

        # 标题和注释等信息显示组件
        message_displayer_layout = QHBoxLayout()
        layout.addLayout(message_displayer_layout)

        title_comment_layout = QVBoxLayout()
        message_displayer_layout.addLayout(title_comment_layout)
        # 标题编辑框
        self.title_edit = QLineEdit(title)
        self.title_edit.textChanged.connect(self.save_metadata)
        self.title_edit.setFont(QFont(self.font_name, 12))
        self.title_edit.setStyleSheet(f'background-color: {basic_color_C}; color: {basic_color_B};')
        title_comment_layout.addWidget(self.title_edit)
        # 注释编辑框
        scrollbar = QScrollBar() # 创建滚动条
        scrollbar.setStyleSheet(scrollbar_stylesheet)
        self.comment_edit = QTextEdit(comment)
        self.comment_edit.setVerticalScrollBar(scrollbar)
        self.comment_edit.textChanged.connect(self.save_metadata)
        self.comment_edit.setFont(QFont(self.font_name, 12))
        # 图片显示
        self.image_path = picture
        self.image_displayer = QLabel()
        self.image_displayer.setFont(QFont(self.font_name, 12))
        self.image_displayer.setMinimumSize(QSize(110, 110))
        self.image_displayer.setStyleSheet(f"border: 3px solid; background: {basic_color_C}")
        self.image_displayer.setAlignment(Qt.AlignCenter)
        self.image_displayer.setCursor(QCursor(Qt.PointingHandCursor))  # 设置手型光标
        # 加载初始图片
        self.update_display_image()
        # 绑定点击事件
        self.image_displayer.mousePressEvent = self.on_image_clicked
        message_displayer_layout.addWidget(self.image_displayer)
        title_comment_layout.addWidget(self.comment_edit)

        # 信息显示
        info_layout = QHBoxLayout()
        path_label = QLabel(f"{path}")
        path_label.setFont(QFont(self.font_name, 8))
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_label.setCursor(QCursor(Qt.IBeamCursor))
        path_label.setStyleSheet(f"border: 0px solid;")
        info_layout.addWidget(path_label)
        layout.addLayout(info_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_backup = self.parent.add_pushbutton('💾备份存档💾', f'background-color: {basic_color_B};', 14, -1, 50)
        self.btn_restore = self.parent.add_pushbutton('🎯覆盖存档🎯', f'background-color: {basic_color_B};', 14, -1, 50)
        self.btn_delete = self.parent.add_pushbutton('🗑️删除备份🗑️', f'background-color: {basic_color_B};', 14, -1, 50)
        self.btn_up = self.parent.add_pushbutton('🔼', f'background-color: {basic_color_B};', 18, 50, 50)
        self.btn_down = self.parent.add_pushbutton('🔽', f'background-color: {basic_color_B};', 18, 50, 50)
        self.btn_openpath = self.parent.add_pushbutton('📁', f'background-color: {basic_color_B};', 18, 50, 50)

        self.btn_openpath.clicked.connect(lambda: self.parent.open_archive_dir_by_id(self.archive_id))
        self.btn_backup.clicked.connect(lambda: self.parent.backup_archive(self.archive_id))
        self.btn_restore.clicked.connect(lambda: self.parent.restore_archive(self.archive_id))
        self.btn_delete.clicked.connect(lambda: self.parent.delete_archive(self.archive_id))
        self.btn_up.clicked.connect(lambda: self.parent.move_archive_up(self.archive_id))
        self.btn_down.clicked.connect(lambda: self.parent.move_archive_down(self.archive_id))

        btn_layout.addWidget(self.btn_backup)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_openpath)
        layout.addLayout(btn_layout)

    def update_display_image(self):
        """更新显示的图片"""
        pix = self.parent.get_pixmap_from_imagepath(self.image_path, 110, 110)
        if not pix.isNull():
            self.image_displayer.setPixmap(pix)
        else:  # 图片加载失败时显示默认文本
            self.image_displayer.setText("点击更换\n存档图片")

    def on_image_clicked(self, event):
        """处理图片点击事件"""
        # 获取新图片路径
        new_path = self.parent.get_random_imagepath()
        if not new_path:
            return

        # 更新图片显示
        self.image_path = new_path
        self.update_display_image()

        # 保存到配置文件
        self.save_metadata()

    def save_metadata(self):
        """存储元数据"""
        self.parent.update_archive_metadata(
            self.archive_id,
            self.title_edit.text(),
            self.comment_edit.toPlainText(),
            self.image_path
        )

# 文件操作线程
class FileWorker(QThread):
    finished = pyqtSignal(str, bool, str)  # (archive_id, success, error_msg)

    def __init__(self, src, dest, operation, game_path=None):
        super().__init__()
        self.src = src
        self.dest = dest
        self.operation = operation
        self.game_path = game_path

    def run(self):
        """运行操作"""
        error_msg = ""
        success = False
        try:
            if self.operation == "backup":
                main_success = False
                safe_success = False
                safe_error = ""

                # 主备份逻辑
                try:
                    if os.path.exists(self.dest):
                        shutil.rmtree(self.dest)
                    shutil.copytree(self.src, self.dest)
                    main_success = True
                except Exception as e:
                    error_msg = f"主备份失败：{str(e)}"

                # 安全备份逻辑（无论主备份是否成功都执行）
                if self.game_path:
                    safe_dest = os.path.join(self.game_path, "save00_Safe")
                    try:
                        if os.path.exists(safe_dest):
                            shutil.rmtree(safe_dest)
                        shutil.copytree(self.src, safe_dest)
                        safe_success = True
                    except Exception as e:
                        safe_error = f"\n安全备份失败：{str(e)}"

                # 组合结果信息
                success = main_success
                if safe_error:
                    error_msg += safe_error
                elif not main_success and safe_success:
                    error_msg += "\n(安全备份成功但主备份失败)"

            elif self.operation == "restore":
                # 备份原始存档以防万一
                temp_backup = f"{self.dest}_temp_{uuid.uuid4().hex}"
                if os.path.exists(self.dest):
                    shutil.copytree(self.dest, temp_backup)

                try:
                    shutil.rmtree(self.dest)
                    shutil.copytree(self.src, self.dest)
                    # 清理临时备份
                    if os.path.exists(temp_backup):
                        shutil.rmtree(temp_backup)
                    success = True
                except Exception as e:
                    # 恢复操作失败时尝试恢复备份
                    if os.path.exists(temp_backup):
                        shutil.rmtree(self.dest)
                        shutil.copytree(temp_backup, self.dest)
                    error_msg = f"恢复失败：{str(e)}"

            elif self.operation == "delete":
                if os.path.exists(self.dest):
                    shutil.rmtree(self.dest)
                success = True

        except Exception as e:
            error_msg = str(e)

        self.finished.emit(self.dest, success, error_msg)

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = ArchiveManager()
    manager.show()
    sys.exit(app.exec_())