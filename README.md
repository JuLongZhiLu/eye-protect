# eye-protect
用PyQt5写的强制护眼软件

## 如何紧急退出？
因为代码中严格实现了“不能退出”的要求（屏蔽了键盘和关闭按钮），如果你在测试时设置了太长的时间导致无法使用电脑，请使用以下方法：

方法 1：按下 Ctrl + Alt + Del 调出任务管理器（这是系统级中断，PyQt 无法屏蔽），然后强制结束 Python 进程。

建议：初次运行测试时，建议将休息时长设置为 1 分钟或更短，以防逻辑卡死。

## 运行效果

<img width="389" height="259" alt="PixPin_2025-12-05_23-14-09" src="https://github.com/user-attachments/assets/bc1725b1-bd3b-4e00-9625-2185e0cc16d2" />

<img width="1920" height="1080" alt="PixPin_2025-12-05_23-16-17" src="https://github.com/user-attachments/assets/19677d32-8e76-4dc1-8b5e-b78a681db1dd" />
