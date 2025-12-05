import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QHBoxLayout, QSpinBox, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette

class RestWindow(QWidget):
    """
    黑屏休息窗口
    """
    # 定义信号，仅用于通知主窗口“时间到了”
    rest_finished = pyqtSignal()

    def __init__(self, is_primary=False):
        super().__init__()
        self.is_primary = is_primary # 标记是否为主窗口（只有主窗口负责倒计时逻辑）
        self.remaining_seconds = 0
        self.initUI()
        
        # 只有主窗口才需要定时器来计算时间
        if self.is_primary:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_countdown)

    def initUI(self):
        # 标志：无边框 | 置顶 | 工具窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # 背景黑色
        palette = self.palette()
        palette.setColor(QPalette.Background, Qt.black)
        self.setPalette(palette)

        # 布局
        layout = QVBoxLayout()
        
        # 只有主屏幕显示文字，副屏幕纯黑（也可以都显示，看你喜好，这里都显示）
        self.info_label = QLabel("眼睛休息中...", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: white; font-size: 40px; font-weight: bold;")
        
        self.time_label = QLabel("", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #00FF00; font-size: 60px; font-weight: bold;")

        layout.addStretch()
        layout.addWidget(self.info_label)
        layout.addWidget(self.time_label)
        layout.addStretch()
        self.setLayout(layout)

    def start_rest(self, total_seconds, screen_geometry):
        """
        开始休息
        :param total_seconds: 休息时长
        :param screen_geometry: 当前屏幕的坐标尺寸信息
        """
        self.remaining_seconds = total_seconds
        
        # 1. 移动窗口到对应屏幕的左上角
        self.move(screen_geometry.x(), screen_geometry.y())
        # 2. 调整大小为该屏幕大小
        self.resize(screen_geometry.width(), screen_geometry.height())
        # 3. 强制全屏
        self.showFullScreen()
        
        # 刷新一下显示
        self.update_display()

        # 只有主控窗口启动定时器
        if self.is_primary:
            self.timer.start(1000) 

    def update_countdown(self):
        """定时器回调（仅主窗口运行）"""
        self.remaining_seconds -= 1
        
        # 发送信号通知外部更新所有窗口的显示数字（如果不嫌麻烦，也可以让外部每秒刷新）
        # 这里为了简单，我们让主窗口发射信号给自己处理，或者直接修改主逻辑
        # 但为了架构简单，我们只处理逻辑：
        
        # 如果时间到了
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.rest_finished.emit() # 通知 Main 关闭所有窗口
        else:
            # 如果你有需求让所有屏幕倒计时同步，需要主窗口广播。
            # 简化版：我们只更新自己的，副屏幕的数字如果不动也行，或者副屏幕也启动定时器。
            # 为了让所有屏幕数字都在动，我们在 start_rest 外部统一控制可能更好。
            # 但为了改动最小，这里我们在 MainWindow 里做一个 hack，或者干脆让每个窗口自己倒计时。
            pass

        self.update_display()

    def set_display_time(self, seconds):
        """用于外部强制同步时间显示"""
        self.remaining_seconds = seconds
        self.update_display()

    def update_display(self):
        mins, secs = divmod(self.remaining_seconds, 60)
        self.time_label.setText(f"{mins:02d}:{secs:02d}")

    def close_window(self):
        """关闭当前窗口"""
        if self.is_primary and self.timer.isActive():
            self.timer.stop()
        self.showNormal()
        self.close() # 这里直接 close 销毁，下次休息重新创建，适应屏幕插拔变化

    # --- 强制性逻辑 ---
    def keyPressEvent(self, event):
        pass 

    def closeEvent(self, event):
        # 只有当被显式调用 close() 时才允许关闭，否则忽略 Alt+F4
        # 这里通过判断 remaining_seconds 是否还大于0来决定是否允许
        # 但由于我们现在是多窗口管理，逻辑由 Main 控制。
        # 简单处理：如果是系统信号关闭(spontaneous)，则忽略。
        if event.spontaneous():
            event.ignore()
        else:
            event.accept()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # 存储当前打开的所有黑屏窗口列表
        self.rest_window_list = []

        self.work_timer = QTimer(self)
        self.work_timer.timeout.connect(self.on_work_finished)
        
        # 额外的定时器：用于同步所有副屏幕的倒计时显示
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.sync_screens)
        self.current_rest_seconds = 0
        
        self.is_running = False

    def initUI(self):
        self.setWindowTitle("PyQt5 护眼工具 (多屏版)")
        self.resize(350, 220)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        # 1. 工作时间
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(QLabel("工作时长:"))
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 240)
        self.work_spin.setValue(45) 
        h_layout1.addWidget(self.work_spin)
        h_layout1.addWidget(QLabel("分钟"))
        h_layout1.addStretch()
        layout.addLayout(h_layout1)

        # 2. 休息时间
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(QLabel("休息时长:"))
        self.rest_min_spin = QSpinBox()
        self.rest_min_spin.setRange(0, 60)
        self.rest_min_spin.setValue(0) 
        h_layout2.addWidget(self.rest_min_spin)
        h_layout2.addWidget(QLabel("分"))
        
        self.rest_sec_spin = QSpinBox()
        self.rest_sec_spin.setRange(0, 59)
        self.rest_sec_spin.setValue(10)
        h_layout2.addWidget(self.rest_sec_spin)
        h_layout2.addWidget(QLabel("秒"))
        layout.addLayout(h_layout2)

        self.status_label = QLabel("状态: 等待开始")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.btn_start = QPushButton("开始护眼模式")
        self.btn_start.clicked.connect(self.toggle_timer)
        layout.addWidget(self.btn_start)

        self.setLayout(layout)

    def toggle_timer(self):
        if not self.is_running:
            rest_total = self.rest_min_spin.value() * 60 + self.rest_sec_spin.value()
            if rest_total <= 0:
                self.status_label.setText("错误：休息时间不能为0")
                return

            work_time = self.work_spin.value()
            self.work_timer.start(work_time * 60 * 1000) 
            
            self.is_running = True
            self.btn_start.setText("停止护眼模式")
            self.status_label.setText(f"工作中... {work_time}分钟后休息")
            
            self.work_spin.setEnabled(False)
            self.rest_min_spin.setEnabled(False)
            self.rest_sec_spin.setEnabled(False)
        else:
            self.work_timer.stop()
            self.is_running = False
            self.btn_start.setText("开始护眼模式")
            self.status_label.setText("状态: 已停止")
            
            self.work_spin.setEnabled(True)
            self.rest_min_spin.setEnabled(True)
            self.rest_sec_spin.setEnabled(True)

    def on_work_finished(self):
        """工作结束，开始休息"""
        self.work_timer.stop()
        self.status_label.setText("正在休息中...")
        
        mins = self.rest_min_spin.value()
        secs = self.rest_sec_spin.value()
        self.current_rest_seconds = mins * 60 + secs
        
        # --- 多屏幕处理逻辑 ---
        screens = QApplication.screens() # 获取所有屏幕列表
        self.rest_window_list.clear() # 清空列表

        for index, screen in enumerate(screens):
            # 只有第0个窗口（主屏）作为 Primary，负责触发结束信号
            is_primary = (index == 0)
            
            # 创建窗口
            rw = RestWindow(is_primary=is_primary)
            
            # 连接主屏的结束信号
            if is_primary:
                rw.rest_finished.connect(self.on_rest_finished)
            
            # 启动休息窗口，传入对应的屏幕几何信息
            rw.start_rest(self.current_rest_seconds, screen.geometry())
            
            self.rest_window_list.append(rw)
        
        # 启动一个同步定时器，每秒让所有副屏幕更新时间显示
        # 这样所有屏幕的倒计时是一致的
        self.sync_timer.start(1000)

    def sync_screens(self):
        """每秒运行一次，同步倒计时"""
        self.current_rest_seconds -= 1
        if self.current_rest_seconds < 0:
            self.sync_timer.stop()
            return
            
        # 遍历所有窗口，强制更新显示时间
        for w in self.rest_window_list:
            # 主窗口自己有定时器，可以不用管，也可以强制覆盖，这里强制覆盖确保完全同步
            w.set_display_time(self.current_rest_seconds)

    def on_rest_finished(self):
        """休息结束"""
        self.sync_timer.stop()
        
        # 关闭所有屏幕的黑屏窗口
        for w in self.rest_window_list:
            w.close_window() # 调用我们自定义的 close_window
        self.rest_window_list.clear()

        # 重启工作循环
        if self.is_running:
            work_time = self.work_spin.value()
            self.work_timer.start(work_time * 60 * 1000)
            self.status_label.setText(f"工作中... {work_time}分钟后休息")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())