"""
玄鉴放大镜 - 极简版
屏幕放大镜快捷控制工具

版本：v3.7
作者：INTP观察室
"""

import tkinter as tk
from tkinter import messagebox
import time
import json
import os
import hashlib
import base64
import platform
import webbrowser
import subprocess
import ctypes

# ==============================================
# 🔧 调试开关
# ==============================================
IS_DEBUG = False  # True=跳过授权
# ==============================================

# 系统检测
CURRENT_OS = platform.system()
IS_WINDOWS = (CURRENT_OS == "Windows")

# 颜色配置
COLORS = {
    "bg": "#F5F7FA",
    "card": "#FFFFFF",
    "border": "#E4E7EB",
    "text": "#1F2937",
    "text_light": "#6B7280",
    "brand": "#5A7A95",
    "brand_hover": "#6C8AAB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
}


class RoundedButton(tk.Canvas):
    """圆角按钮组件"""
    def __init__(self, parent, text="", command=None, bg_color=COLORS["brand"],
                 hover_color=COLORS["brand_hover"], corner_radius=8, 
                 width=100, height=32, font=None):
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.current_color = bg_color
        self.corner_radius = corner_radius
        self.text = text
        self.width = width
        self.height = height
        self.parent_bg = parent.cget("bg") if parent else COLORS["bg"]
        self._state = "normal"

        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, cursor="hand2",
                         bg=self.parent_bg)

        self.font = font or ("Microsoft YaHei", 9)
        self.draw_button()
        self._bind_events()

    def _bind_events(self):
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def draw_button(self):
        self.delete("all")
        self.create_rounded_rectangle(0, 0, self.width, self.height,
                                      radius=self.corner_radius,
                                      fill=self.current_color,
                                      outline="", tags="button")
        self.create_text(self.width // 2, self.height // 2,
                         text=self.text, fill="white",
                         font=self.font, tags="text")

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=8, **kwargs):
        points = []
        if radius > (x2 - x1) / 2:
            radius = (x2 - x1) / 2
        if radius > (y2 - y1) / 2:
            radius = (y2 - y1) / 2

        points.append((x1 + radius, y1))
        points.append((x2 - radius, y1))
        points.append((x2, y1))
        points.append((x2, y1 + radius))
        points.append((x2, y2 - radius))
        points.append((x2, y2))
        points.append((x2 - radius, y2))
        points.append((x1 + radius, y2))
        points.append((x1, y2))
        points.append((x1, y2 - radius))
        points.append((x1, y1 + radius))
        points.append((x1, y1))

        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_click(self, event):
        if self._state == "disabled":
            return
        if self.command:
            self.command()

    def _on_enter(self, event):
        if self._state == "disabled":
            return
        self.current_color = self.hover_color
        self.draw_button()

    def _on_leave(self, event):
        if self._state == "disabled":
            return
        self.current_color = self.bg_color
        self.draw_button()

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
            self.draw_button()
        if "state" in kwargs:
            self._state = kwargs["state"]
            if self._state == "disabled":
                self.configure(cursor="arrow")
            else:
                self.configure(cursor="hand2")
        if "bg_color" in kwargs:
            self.bg_color = kwargs["bg_color"]
            self.current_color = self.bg_color
            self.draw_button()


class XuanjianMagnifierLite:
    def __init__(self, root):
        self.root = root
        self.root.title("玄鉴放大镜")
        self.root.geometry("500x550")  # 增加高度
        self.root.minsize(450, 500)
        self.root.configure(bg=COLORS["bg"])

        # ========== 授权验证 ==========
        if IS_DEBUG:
            self.is_authorized = True
            self.root.title("【调试模式】玄鉴放大镜")
        else:
            self.is_authorized = self.check_authorization()
            if not self.is_authorized:
                self.show_activation_window()
                return

        # 非 Windows 系统提示
        if not IS_WINDOWS:
            messagebox.showwarning(
                "功能受限",
                "当前系统非 Windows，放大镜功能不可用。"
            )

        # 创建UI
        self.create_ui()

        # 关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------- 授权验证 ----------
    def get_machine_code(self):
        system = platform.system()
        node = platform.node()
        processor = platform.processor()
        raw = f"{system}_{node}_{processor}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def get_client_license_path(self):
        documents_path = os.path.expanduser("~/Documents/INTP观察室百宝箱")
        return os.path.join(documents_path, "licenses", "licenses.dat")

    def check_authorization(self):
        license_path = self.get_client_license_path()
        if not os.path.exists(license_path):
            return False
        try:
            with open(license_path, 'r', encoding='utf-8') as f:
                encrypted_data = f.read().strip()
            reversed_str = encrypted_data[::-1]
            decoded_bytes = base64.b64decode(reversed_str)
            decoded = decoded_bytes.decode('utf-8')
            data = json.loads(decoded)
            current_machine_code = self.get_machine_code()
            baby_id = "xuanjianfangdajing"
            if baby_id in data.get('activated_babies', []):
                license_info = data.get('licenses', {}).get(baby_id, {})
                return license_info.get('machine_code') == current_machine_code
            return False
        except Exception:
            return False

    def show_activation_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.configure(bg=COLORS["bg"])
        frame = tk.Frame(self.root, bg=COLORS["card"], relief=tk.FLAT)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)
        tk.Label(frame, text="🔒", font=("Segoe UI", 48), bg=COLORS["card"], fg=COLORS["warning"]).pack(pady=(30, 10))
        tk.Label(frame, text="玄鉴放大镜", font=("Microsoft YaHei", 18, "bold"), bg=COLORS["card"], fg=COLORS["brand"]).pack()
        tk.Label(frame, text="未激活", font=("Microsoft YaHei", 11), bg=COLORS["card"], fg=COLORS["error"]).pack(pady=5)
        tk.Label(frame, text="请在「INTP观察室·我的百宝箱」中激活", bg=COLORS["card"], fg=COLORS["text_light"]).pack()
        btn = RoundedButton(frame, text="关闭", command=self.root.destroy,
                            bg_color=COLORS["brand"], hover_color=COLORS["brand_hover"],
                            width=100, height=32)
        btn.pack(pady=20)

    # ---------- 模拟按键 ----------
    def send_hotkey(self, modifiers, key_code):
        """通用的模拟按键函数"""
        if not IS_WINDOWS:
            return False
        
        try:
            keybd_event = ctypes.windll.user32.keybd_event
            
            for mod in modifiers:
                keybd_event(mod, 0, 0, 0)
            
            keybd_event(key_code, 0, 0, 0)
            time.sleep(0.05)
            
            keybd_event(key_code, 0, 2, 0)
            
            for mod in reversed(modifiers):
                keybd_event(mod, 0, 2, 0)
            
            return True
        except:
            return False

    # ---------- 放大镜控制（分开的启动和关闭）----------
    def start_magnifier(self):
        """启动放大镜"""
        if not IS_WINDOWS:
            return
        
        try:
            system_root = os.environ.get("SystemRoot", "C:\\Windows")
            magnify_path = os.path.join(system_root, "System32", "magnify.exe")
            subprocess.Popen([magnify_path])
            
            self.status_label.config(text="● 放大镜运行中", fg=COLORS["success"])
            self.update_status("放大镜已启动")
            
            # 延迟切换到镜头模式
            self.root.after(1000, lambda: self.send_hotkey([0x11, 0x12], 0x4C))
            self.root.after(1200, lambda: self.update_status("放大镜运行中 - 镜头模式"))
        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动系统放大镜:\n{str(e)}")

    def stop_magnifier(self):
        """关闭放大镜"""
        if not IS_WINDOWS:
            return
        
        try:
            # 直接强制结束进程
            subprocess.run('taskkill /f /im magnify.exe', shell=True, capture_output=True)
            self.status_label.config(text="● 放大镜未启动", fg=COLORS["text_light"])
            self.update_status("放大镜已关闭")
        except:
            pass

    # ---------- 视图模式切换 ----------
    def fullscreen_mode(self):
        """全屏模式 (Ctrl+Alt+F)"""
        self.send_hotkey([0x11, 0x12], 0x46)
        self.update_status("已切换到全屏模式")

    def lens_mode(self):
        """镜头模式 (Ctrl+Alt+L)"""
        self.send_hotkey([0x11, 0x12], 0x4C)
        self.update_status("已切换到镜头模式")

    def docked_mode(self):
        """停靠模式 (Ctrl+Alt+D)"""
        self.send_hotkey([0x11, 0x12], 0x44)
        self.update_status("已切换到停靠模式")

    # ---------- UI 创建 ----------
    def create_ui(self):
        # 使用place布局确保绝对定位，避免遮挡
        main_container = tk.Frame(self.root, bg=COLORS["bg"])
        main_container.place(relx=0, rely=0, relwidth=1, relheight=1)

        # 品牌栏
        brand_frame = tk.Frame(main_container, bg=COLORS["card"], relief=tk.FLAT, bd=1)
        brand_frame.place(relx=0.03, rely=0.02, relwidth=0.94, height=50)
        brand_frame.configure(highlightbackground=COLORS["border"], highlightthickness=1)

        tk.Label(brand_frame, text="🧠", font=("Segoe UI", 20), bg=COLORS["card"]).place(x=15, y=5)
        tk.Label(brand_frame, text="INTP观察室", font=("Microsoft YaHei", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["brand"]).place(x=55, y=12)
        tk.Label(brand_frame, text="· 玄鉴放大镜", font=("Microsoft YaHei", 11),
                 bg=COLORS["card"], fg=COLORS["text_light"]).place(x=155, y=13)

        website_btn = tk.Label(brand_frame, text="🌐 intpwatch.cn", font=("Microsoft YaHei", 9),
                               bg=COLORS["card"], fg=COLORS["brand"], cursor="hand2")
        website_btn.place(relx=0.98, y=15, anchor="ne")
        website_btn.bind("<Button-1>", lambda e: webbrowser.open("https://intpwatch.cn"))

        # 主功能区
        control_card = tk.Frame(main_container, bg=COLORS["card"], relief=tk.FLAT, bd=1)
        control_card.place(relx=0.03, rely=0.13, relwidth=0.94, relheight=0.75)
        control_card.configure(highlightbackground=COLORS["border"], highlightthickness=1)

        # 标题
        tk.Label(control_card, text="🔍", font=("Segoe UI", 48),
                 bg=COLORS["card"], fg=COLORS["brand"]).place(relx=0.5, y=40, anchor="center")
        tk.Label(control_card, text="玄鉴放大镜", font=("Microsoft YaHei", 16, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).place(relx=0.5, y=100, anchor="center")

        btn_width, btn_height = 180, 38
        center_x = 0.5

        # 启动按钮
        self.start_btn = RoundedButton(
            control_card,
            text="▶ 启动放大镜",
            command=self.start_magnifier,
            bg_color=COLORS["success"],
            hover_color="#059669",
            width=btn_width,
            height=btn_height
        )
        self.start_btn.place(relx=center_x, y=150, anchor="center")
        if not IS_WINDOWS:
            self.start_btn.config(state="disabled")

        # 关闭按钮
        self.stop_btn = RoundedButton(
            control_card,
            text="■ 关闭放大镜",
            command=self.stop_magnifier,
            bg_color=COLORS["error"],
            hover_color="#DC2626",
            width=btn_width,
            height=btn_height
        )
        self.stop_btn.place(relx=center_x, y=200, anchor="center")
        if not IS_WINDOWS:
            self.stop_btn.config(state="disabled")

        # 分隔线
        separator = tk.Frame(control_card, height=1, bg=COLORS["border"])
        separator.place(relx=0.1, y=255, relwidth=0.8)

        # 全屏模式按钮
        RoundedButton(
            control_card,
            text="🖥️ 全屏模式",
            command=self.fullscreen_mode,
            bg_color=COLORS["brand"],
            hover_color=COLORS["brand_hover"],
            width=btn_width,
            height=btn_height
        ).place(relx=center_x, y=290, anchor="center")

        # 镜头模式按钮
        RoundedButton(
            control_card,
            text="🔎 镜头模式",
            command=self.lens_mode,
            bg_color=COLORS["brand"],
            hover_color=COLORS["brand_hover"],
            width=btn_width,
            height=btn_height
        ).place(relx=center_x, y=340, anchor="center")

        # 停靠模式按钮
        RoundedButton(
            control_card,
            text="📌 停靠模式",
            command=self.docked_mode,
            bg_color=COLORS["brand"],
            hover_color=COLORS["brand_hover"],
            width=btn_width,
            height=btn_height
        ).place(relx=center_x, y=390, anchor="center")

        # 状态指示
        self.status_label = tk.Label(control_card, text="● 放大镜未启动", font=("Microsoft YaHei", 10),
                                     bg=COLORS["card"], fg=COLORS["text_light"])
        self.status_label.place(relx=0.5, y=445, anchor="center")

        # 状态栏
        status_frame = tk.Frame(main_container, bg=COLORS["card"], relief=tk.FLAT, bd=1)
        status_frame.place(relx=0.03, rely=0.90, relwidth=0.94, height=35)
        status_frame.configure(highlightbackground=COLORS["border"], highlightthickness=1)

        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        tk.Label(status_frame, textvariable=self.status_var, font=("Microsoft YaHei", 9),
                 bg=COLORS["card"], fg=COLORS["text_light"], anchor=tk.W).place(x=15, y=8)

        tk.Label(status_frame, text="© 2025 INTP观察室", font=("Microsoft YaHei", 8),
                 bg=COLORS["card"], fg=COLORS["text_light"]).place(relx=0.98, y=9, anchor="ne")

    def update_status(self, message):
        self.status_var.set(message)

    def on_closing(self):
        self.root.destroy()


def main():
    root = tk.Tk()
    app = XuanjianMagnifierLite(root)
    root.mainloop()


if __name__ == "__main__":
    main()
