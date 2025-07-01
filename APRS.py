import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, time, timedelta
import threading
import time as time_module
import os
import json
import webbrowser
from tkintermapview import TkinterMapView
import random

def calculate_aprs_verification_code(callsign):
    """
    根据呼号计算APRS验证码
    
    参数:
    callsign - 呼号 (可以包含SSID，如N0CALL-1)
    
    返回:
    int - 计算出的验证码
    """
    # 处理呼号格式，去除SSID部分并转换为大写
    callsign = callsign.upper().strip()
    if '-' in callsign:
        callsign = callsign.split('-')[0]
    
    # APRS验证码计算算法
    code = 0x73e2  # 初始值
    for i, char in enumerate(callsign):
        # 根据字符位置进行位运算
        code ^= ord(char) << (8 if i % 2 == 0 else 0)
    
    # 确保验证码在0-32767范围内
    verification_code = code & 0x7fff 
    return verification_code

def send_aprs_packet(
    callsign="N0CALL-1",
    path="WIDE1-1",
    latitude="2947.76N",
    longitude="11941.12E",
    symbol_table="/",  # 主符号表
    symbol_code="L",   # 符号代码 (L = 天气站)
    comment="TEST APRS.TV",
    aprs_word=None,    # 可选: 自定义APRS验证码
    speed=None,        # 速度 (km/h)
    course=None,       # 方向 (°)
    altitude=None,     # 海拔 (m)
    power=None,        # 功率 (W)
    antenna_height=None, # 天线高度 (m)
    gain=None,          # 增益 (dB)
    device_info=None,   # 设备信息
    software_info=None  # 软件信息
):
    """
    发送自定义APRS数据包到aprs.tv
    
    参数:
    callsign     - 呼号 (默认: N0CALL-1)
    path         - 转发路径 (默认: WIDE1-1)
    latitude     - 纬度 (格式: ddmm.mmN/S, 默认: 2947.76N)
    longitude    - 经度 (格式: dddmm.mmE/W, 默认: 11941.12E)
    symbol_table - 符号表 (默认: / = 主表)
    symbol_code  - 符号代码 (默认: L = 天气站)
    comment      - 注释信息 (默认: TEST APRS.TV)
    aprs_word    - 可选: 自定义APRS验证码 (如果不提供则自动计算)
    speed        - 可选: 速度 (km/h)
    course       - 可选: 方向 (°)
    altitude     - 可选: 海拔 (m)
    power        - 可选: 功率 (W)
    antenna_height - 可选: 天线高度 (m)
    gain         - 可选: 增益 (dB)
    device_info   - 可选: 设备信息
    software_info - 可选: 软件信息
    
    返回:
    dict - 服务器响应结果
    """
    # 自动计算APRS验证码（如果未提供）
    if aprs_word is None:
        try:
            aprs_word = str(calculate_aprs_verification_code(callsign))
        except Exception as e:
            aprs_word = "13023"  # 默认值
            return {"rs": "err", "message": f"验证码计算错误: {str(e)}", "aprs_word": aprs_word}
    
    # 构建APRS数据包内容 - 使用标准位置报告格式
    # 格式: /时间h纬度/经度e速度/方向/A=海拔 附加信息
    now = datetime.utcnow()
    timestamp = now.strftime("%H%M%S")
    
    # 构建位置报告部分
    aprs_data = f"{callsign}>APRSTV,{path}:/{timestamp}h{latitude}{symbol_table}{longitude}e"
    
    # 添加速度和方向（如果提供）
    if speed is not None and course is not None:
        # 速度格式为三位数字 (000-999)
        speed_str = f"{int(float(speed)):03d}"
        # 方向格式为三位数字 (000-360)
        course_str = f"{int(float(course)):03d}"
        aprs_data += f"{speed_str}/{course_str}"
    else:
        aprs_data += "   /   "  # 空值
    
    # 添加海拔（如果提供）
    if altitude is not None:
        # 海拔转换为英尺并格式化为六位数字
        altitude_ft = float(altitude) * 3.28084
        aprs_data += f"/A={int(altitude_ft):06d}"
    
    # 构建状态信息部分（功率、天线高度、增益等）
    status_info = []
    
    # 添加功率信息（如果提供）
    if power is not None:
        status_info.append(f"功率{power}W")
    
    # 添加天线高度信息（如果提供）
    if antenna_height is not None:
        status_info.append(f"天线高度{antenna_height}m")
    
    # 添加增益信息（如果提供）
    if gain is not None:
        status_info.append(f"增益{gain}dB")
    
    # 添加设备信息（如果提供）
    if device_info:
        status_info.append(device_info)
    
    # 添加软件信息（如果提供）
    if software_info:
        status_info.append(software_info)
    
    # 将状态信息组合成字符串
    status_str = " ".join(status_info)
    
    # 添加注释和附加信息
    if status_str:
        full_comment = status_str + " " + comment
    else:
        full_comment = comment
        
    aprs_data += f" {full_comment}"
    
    # 准备POST数据
    post_data = {
        "aprs": aprs_data,
        "isword": aprs_word
    }
    
    # 设置请求头 (模拟浏览器请求)
    headers = {
        "authority": "aprs.tv",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "dnt": "1",
        "origin": "https://aprs.tv",
        "priority": "u=1, i",
        "referer": "https://aprs.tv/makeaprs",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "x-requested-with": "XMLHttpRequest"
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            "https://aprs.tv/makeaprs",
            data=post_data,
            headers=headers,
            timeout=10
        )
        
        # 尝试解析JSON响应
        try:
            result = response.json()
        except:
            result = {
                "rs": "err",
                "message": f"非JSON响应: {response.status_code} {response.text[:100]}",
                "raw_response": response.text
            }
        
        # 添加验证码信息
        result["aprs_word"] = aprs_word
        result["aprs_data"] = aprs_data  # 添加构建的数据包内容
        return result
    except Exception as e:
        return {
            "rs": "err",
            "message": f"请求失败: {str(e)}",
            "aprs_word": aprs_word,
            "aprs_data": aprs_data  # 添加构建的数据包内容
        }

class APRSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("APRS数据包发送工具 - BG5FNL")
        self.root.state('zoomed')  # 启动时最大化窗口
        self.root.minsize(1000, 700)  # 设置最小尺寸
        
        # 创建图标目录
        self.icon_dir = "aprs_icons"
        if not os.path.exists(self.icon_dir):
            os.makedirs(self.icon_dir)
        
        # 加载图标配置（修正后的符号表）
        self.symbols = self.load_symbol_config()
        
        # 定时发送控制变量
        self.scheduled_enabled = False
        self.schedule_thread = None
        
        # 创建主框架（左右分栏）
        self.create_main_frames()
        
        # 创建输入字段
        self.create_input_fields()
        
        # 创建按钮区域
        self.create_button_area()
        
        # 创建图标选择区域
        self.create_icon_selector()
        
        # 创建日志区域
        self.create_log_area()
        
        # 创建定时发送区域
        self.create_schedule_area()
        
        # 创建地图区域
        self.create_map_area()
        
        # 创建APRS地图区域
        self.create_aprs_map_area()
        
        # 默认值
        self.set_default_values()
        
        # 加载图标
        self.load_icons()
        
        # 绑定全屏切换快捷键 (F11)
        self.root.bind("<F11>", self.toggle_fullscreen)
        
    def create_main_frames(self):
        """创建主框架（左右分栏）"""
        # 创建主分栏
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧框架（配置区域）
        self.left_frame = ttk.Frame(self.main_paned, width=500)
        self.main_paned.add(self.left_frame, weight=1)
        
        # 右侧框架（地图区域）
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=1)
        
        # 在左侧框架内创建滚动区域
        self.create_scrollable_frame()
        
    def create_scrollable_frame(self):
        """在左侧框架内创建可滚动的配置区域"""
        # 创建画布
        self.canvas = tk.Canvas(self.left_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置画布
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # 创建内部框架（所有内容都放在这里）
        self.main_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
        # 绑定鼠标滚轮事件
        self.main_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
    def on_frame_configure(self, event):
        """更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def on_mousewheel(self, event):
        """鼠标滚轮滚动"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def toggle_fullscreen(self, event=None):
        """切换全屏模式"""
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
    
    def load_symbol_config(self):
        """加载图标配置（修正后的符号表）"""
        symbols = {
            "primary": {
                "/": {
                    ">": {"name": "汽车", "color": "red"},
                    "<": {"name": "摩托车", "color": "blue"},
                    "v": {"name": "面包车", "color": "green"},
                    "^": {"name": "大型飞机", "color": "purple"},
                    "L": {"name": "PC 用户", "color": "cyan"},
                    "K": {"name": "学校", "color": "orange"},
                    "H": {"name": "酒店", "color": "brown"},
                    "h": {"name": "医院", "color": "pink"},
                    "b": {"name": "自行车", "color": "navy"},
                    "B": {"name": "BBS", "color": "teal"},
                    "Y": {"name": "帆船", "color": "gray"},
                    "O": {"name": "气球", "color": "magenta"},
                    "C": {"name": "独木舟", "color": "darkred"}
                }
            },
            "secondary": {
                "\\": {
                    ">": {"name": "红色汽车", "color": "red"},
                    "<": {"name": "单个红色旗帜", "color": "blue"},
                    "t": {"name": "龙卷风", "color": "green"},
                    "^": {"name": "飞机", "color": "purple"},
                    "L": {"name": "灯塔", "color": "cyan"},
                    "N": {"name": "导航浮标", "color": "orange"},
                    "H": {"name": "薄雾", "color": "brown"},
                    "h": {"name": "商店", "color": "pink"},
                    "b": {"name": "沙尘", "color": "navy"},
                    "B": {"name": "吹雪", "color": "teal"},
                    "S": {"name": "卫星", "color": "gray"},
                    "O": {"name": "火箭", "color": "magenta"},
                    "J": {"name": "闪电", "color": "darkred"}
                }
            }
        }
        
        # 保存配置到文件
        config_path = os.path.join(self.icon_dir, "symbols.json")
        with open(config_path, "w") as f:
            json.dump(symbols, f, indent=4)
        
        return symbols
    
    def load_icons(self):
        """加载图标到界面"""
        # 清空当前图标
        for widget in self.primary_frame.winfo_children():
            widget.destroy()
        for widget in self.secondary_frame.winfo_children():
            widget.destroy()
        
        # 加载主表图标
        ttk.Label(self.primary_frame, text="主符号表 (/):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        for code, info in self.symbols["primary"]["/"].items():
            frame = ttk.Frame(self.primary_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 创建颜色方块
            color_label = tk.Label(frame, bg=info["color"], width=3, height=1)
            color_label.pack(side=tk.LEFT, padx=(0, 5))
            
            # 图标名称
            name_label = ttk.Label(frame, text=f"{info['name']} ({code})", width=20)
            name_label.pack(side=tk.LEFT, padx=5)
            
            # 选择按钮
            btn = ttk.Button(
                frame, 
                text="选择", 
                width=6,
                command=lambda c=code, t="/", name=info["name"]: self.select_icon(c, t, name)
            )
            btn.pack(side=tk.RIGHT)
        
        # 加载副表图标
        ttk.Label(self.secondary_frame, text="副符号表 (\\):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        for code, info in self.symbols["secondary"]["\\"].items():
            frame = ttk.Frame(self.secondary_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 创建颜色方块
            color_label = tk.Label(frame, bg=info["color"], width=3, height=1)
            color_label.pack(side=tk.LEFT, padx=(0, 5))
            
            # 图标名称
            name_label = ttk.Label(frame, text=f"{info['name']} ({code})", width=20)
            name_label.pack(side=tk.LEFT, padx=5)
            
            # 选择按钮
            btn = ttk.Button(
                frame, 
                text="选择", 
                width=6,
                command=lambda c=code, t="\\", name=info["name"]: self.select_icon(c, t, name)
            )
            btn.pack(side=tk.RIGHT)
    
    def select_icon(self, symbol_code, symbol_table, symbol_name):
        """选择图标"""
        # 修正符号表值
        actual_table = "/" if symbol_table == "/" else "\\"
        self.symbol_table_var.set(actual_table)
        self.symbol_code_var.set(symbol_code)
        self.log_message(f"已选择图标: {symbol_name} ({actual_table}{symbol_code})")
    
    def create_input_fields(self):
        """创建输入字段（添加速度、方向、海拔等扩展信息）"""
        input_frame = ttk.LabelFrame(self.main_frame, text="APRS数据包配置", padding="10")
        input_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # 作者信息
        author_label = ttk.Label(input_frame, text="作者: BG5FNL", font=("Arial", 9, "italic"))
        author_label.pack(anchor=tk.E, pady=(0, 10))
        
        # 使用网格布局
        grid_frame = ttk.Frame(input_frame)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # 呼号
        ttk.Label(grid_frame, text="呼号 (带标识):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.callsign_entry = ttk.Entry(grid_frame, width=20)
        self.callsign_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: BG5FNL-7").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 验证码显示
        self.code_label = ttk.Label(grid_frame, text="验证码: 自动计算")
        self.code_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 转发路径
        ttk.Label(grid_frame, text="转发路径:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.path_entry = ttk.Entry(grid_frame, width=30)
        self.path_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: APRSTV,TCPIP*,qAC,BG2LBF").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 纬度
        ttk.Label(grid_frame, text="纬度 (ddmm.mmN/S):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.latitude_entry = ttk.Entry(grid_frame, width=15)
        self.latitude_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: 2947.76N").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 经度
        ttk.Label(grid_frame, text="经度 (dddmm.mmE/W):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.longitude_entry = ttk.Entry(grid_frame, width=15)
        self.longitude_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: 11941.12E").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 符号表
        ttk.Label(grid_frame, text="符号表:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.symbol_table_var = tk.StringVar()
        self.symbol_table_combobox = ttk.Combobox(grid_frame, width=5, textvariable=self.symbol_table_var, state="readonly")
        self.symbol_table_combobox['values'] = ('/', '\\')
        self.symbol_table_combobox.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 符号代码
        ttk.Label(grid_frame, text="符号代码:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.symbol_code_var = tk.StringVar()
        self.symbol_code_entry = ttk.Entry(grid_frame, width=5, textvariable=self.symbol_code_var, state="readonly")
        self.symbol_code_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 注释
        ttk.Label(grid_frame, text="消息:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.comment_entry = ttk.Entry(grid_frame, width=50)
        self.comment_entry.grid(row=row, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: TEST APRS.TV").grid(row=row, column=4, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 添加设备信息区域
        ttk.Label(grid_frame, text="设备信息:", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 设备信息
        ttk.Label(grid_frame, text="设备信息:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.device_info_entry = ttk.Entry(grid_frame, width=50)
        self.device_info_entry.grid(row=row, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: imei:*418 rssi:-56 sat:20/33").grid(row=row, column=4, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 软件信息
        ttk.Label(grid_frame, text="软件信息:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.software_info_entry = ttk.Entry(grid_frame, width=50)
        self.software_info_entry.grid(row=row, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Label(grid_frame, text="例如: https://aprs.tv 1.0.39").grid(row=row, column=4, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 添加台站信息区域
        ttk.Label(grid_frame, text="台站信息:", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 功率
        ttk.Label(grid_frame, text="功率 (W):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.power_entry = ttk.Entry(grid_frame, width=10)
        self.power_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 天线高度
        ttk.Label(grid_frame, text="天线高度 (m):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.antenna_height_entry = ttk.Entry(grid_frame, width=10)
        self.antenna_height_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 增益
        ttk.Label(grid_frame, text="增益 (dB):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.gain_entry = ttk.Entry(grid_frame, width=10)
        self.gain_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 添加移动信息区域
        ttk.Label(grid_frame, text="移动信息:", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 速度
        ttk.Label(grid_frame, text="速度 (km/h):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.speed_entry = ttk.Entry(grid_frame, width=10)
        self.speed_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 方向
        ttk.Label(grid_frame, text="方向 (°):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.course_entry = ttk.Entry(grid_frame, width=10)
        self.course_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 海拔
        ttk.Label(grid_frame, text="海拔 (m):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.altitude_entry = ttk.Entry(grid_frame, width=10)
        self.altitude_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 最新状态
        ttk.Label(grid_frame, text="最新状态:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.status_entry = ttk.Entry(grid_frame, width=20)
        self.status_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)
        row += 1
    
    def create_icon_selector(self):
        """创建图标选择区域"""
        icon_frame = ttk.LabelFrame(self.main_frame, text="图标选择", padding="10")
        icon_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # 创建左右两个框架
        columns_frame = ttk.Frame(icon_frame)
        columns_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.primary_frame = ttk.Frame(columns_frame)
        self.primary_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        self.secondary_frame = ttk.Frame(columns_frame)
        self.secondary_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
    
    def create_button_area(self):
        """创建按钮区域"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # 发送按钮
        self.send_button = ttk.Button(button_frame, text="立即发送", command=self.send_packet, width=15)
        self.send_button.pack(side=tk.LEFT, padx=10)
        
        # 计算验证码按钮
        self.calc_button = ttk.Button(button_frame, text="计算验证码", command=self.calculate_code, width=15)
        self.calc_button.pack(side=tk.LEFT, padx=10)
        
        # 清空日志按钮
        self.clear_button = ttk.Button(button_frame, text="清空日志", command=self.clear_log, width=15)
        self.clear_button.pack(side=tk.LEFT, padx=10)
        
        # 退出全屏按钮
        self.fullscreen_button = ttk.Button(button_frame, text="退出全屏 (F11)", command=self.toggle_fullscreen, width=15)
        self.fullscreen_button.pack(side=tk.RIGHT, padx=10)
    
    def create_log_area(self):
        """创建日志区域（修复滚动条问题）"""
        log_frame = ttk.LabelFrame(self.main_frame, text="发送日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # 添加JSON显示开关
        switch_frame = ttk.Frame(log_frame)
        switch_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.show_json_var = tk.BooleanVar(value=False)
        self.show_json_switch = ttk.Checkbutton(
            switch_frame, 
            text="显示完整JSON响应", 
            variable=self.show_json_var,
            command=self.toggle_json_display
        )
        self.show_json_switch.pack(side=tk.LEFT)
        
        # 创建日志文本框容器（修复滚动条位置）
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建文本框
        self.log_text = tk.Text(log_container, height=15, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置文本框
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def toggle_json_display(self):
        """切换JSON显示状态"""
        state = "开启" if self.show_json_var.get() else "关闭"
        self.log_message(f"完整JSON显示已{state}")
    
    def create_schedule_area(self):
        """创建定时发送区域"""
        schedule_frame = ttk.LabelFrame(self.main_frame, text="定时发送", padding="10")
        schedule_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # 时间间隔选择
        ttk.Label(schedule_frame, text="发送间隔:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.interval_var = tk.IntVar(value=30)
        self.interval_combobox = ttk.Combobox(
            schedule_frame, 
            width=5, 
            textvariable=self.interval_var,
            values=[5, 10, 15, 30, 60],
            state="readonly"
        )
        self.interval_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(schedule_frame, text="分钟").grid(row=0, column=2, sticky=tk.W, padx=0, pady=5)
        
        # 定时开关
        self.schedule_button = ttk.Button(
            schedule_frame, 
            text="启动定时发送", 
            command=self.toggle_schedule,
            width=15
        )
        self.schedule_button.grid(row=0, column=3, sticky=tk.E, padx=10, pady=5)
        
        # 状态标签
        self.status_label = ttk.Label(schedule_frame, text="状态: 未启动")
        self.status_label.grid(row=0, column=4, sticky=tk.W, padx=10, pady=5)
    
    def create_map_area(self):
        """创建地图选点区域（使用鼠标中键选点）"""
        map_frame = ttk.LabelFrame(self.main_frame, text="地图选点 (使用鼠标中键设置位置)", padding="10")
        map_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # 创建地图容器
        map_container = ttk.Frame(map_frame)
        map_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建地图控件 - 使用高德地图
        self.map_widget = TkinterMapView(
            map_container, 
            width=400, 
            height=200,
            corner_radius=0
        )
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        
        # 设置高德矢量地图
        self.map_widget.set_tile_server(
            "https://webrd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}",
            max_zoom=19
        )
        
        # 设置初始位置（杭州）
        self.map_widget.set_position(30.2741, 120.1551)
        self.map_widget.set_zoom(12)
        
        # 添加标记
        self.marker = None
        
        # 绑定地图滚轮事件（缩放）
        self.map_widget.canvas.bind("<MouseWheel>", self.on_map_mousewheel)
        
        # 绑定鼠标中键点击事件（选点）
        self.map_widget.canvas.bind("<Button-2>", self.on_map_middle_click)
        
        # 按钮框架
        btn_frame = ttk.Frame(map_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # 当前位置按钮
        ttk.Button(
            btn_frame, 
            text="获取当前位置", 
            command=self.get_current_location,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 设置位置按钮
        ttk.Button(
            btn_frame, 
            text="设置为当前位置", 
            command=self.set_current_location,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 帮助按钮
        ttk.Button(
            btn_frame, 
            text="帮助", 
            command=self.show_map_help,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
    
    def on_map_mousewheel(self, event):
        """地图滚轮事件处理（缩放）"""
        # 计算新的缩放级别
        current_zoom = self.map_widget.zoom
        if event.delta > 0:  # 滚轮向上滚动
            new_zoom = current_zoom + 1
        else:  # 滚轮向下滚动
            new_zoom = current_zoom - 1
        
        # 限制缩放级别范围
        new_zoom = max(1, min(new_zoom, 19))
        
        # 设置新缩放级别
        self.map_widget.set_zoom(new_zoom)
        
        # 阻止事件传播
        return "break"
    
    def on_map_middle_click(self, event):
        """地图鼠标中键点击事件处理（选点）"""
        # 获取点击的像素坐标
        x, y = event.x, event.y
        
        # 将像素坐标转换为地理坐标 - 修复方法名
        lat, lon = self.map_widget.convert_canvas_coords_to_decimal_coords(x, y)
        
        # 删除旧标记
        if self.marker:
            self.map_widget.delete(self.marker)
        
        # 添加新标记
        self.marker = self.map_widget.set_marker(lat, lon, text="当前位置")
        
        # 转换为APRS格式
        aprs_lat = self.decimal_to_aprs_lat(lat)
        aprs_lon = self.decimal_to_aprs_lon(lon)
        
        # 更新输入框
        self.latitude_entry.delete(0, tk.END)
        self.latitude_entry.insert(0, aprs_lat)
        
        self.longitude_entry.delete(0, tk.END)
        self.longitude_entry.insert(0, aprs_lon)
        
        # 显示消息
        self.log_message(f"地图选点: 纬度 {aprs_lat}, 经度 {aprs_lon}")
    
    def create_aprs_map_area(self):
        """创建APRS在线地图区域（居中显示标签）"""
        aprs_frame = ttk.LabelFrame(self.right_frame, text="APRS实时地图", padding="10")
        aprs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建控制面板
        control_frame = ttk.Frame(aprs_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 呼号输入
        ttk.Label(control_frame, text="跟踪呼号:").pack(side=tk.LEFT, padx=(10, 5))
        self.aprs_callsign_var = tk.StringVar(value="BG5FNL-7")
        self.aprs_callsign_entry = ttk.Entry(control_frame, width=15, textvariable=self.aprs_callsign_var)
        self.aprs_callsign_entry.pack(side=tk.LEFT, padx=5)
        
        # 缩放级别
        ttk.Label(control_frame, text="缩放级别:").pack(side=tk.LEFT, padx=(10, 5))
        self.aprs_zoom_var = tk.IntVar(value=10)
        self.aprs_zoom_spinbox = ttk.Spinbox(
            control_frame, 
            from_=6, 
            to=18, 
            width=5, 
            textvariable=self.aprs_zoom_var
        )
        self.aprs_zoom_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 地图类型
        ttk.Label(control_frame, text="地图类型:").pack(side=tk.LEFT, padx=(10, 5))
        self.aprs_maptype_var = tk.StringVar(value="m")
        self.aprs_maptype_combobox = ttk.Combobox(
            control_frame, 
            width=10, 
            textvariable=self.aprs_maptype_var,
            values=["m", "k", "h"]
        )
        self.aprs_maptype_combobox.pack(side=tk.LEFT, padx=5)
        
        # 加载按钮
        ttk.Button(
            control_frame, 
            text="加载地图", 
            command=self.load_aprs_map,
            width=10
        ).pack(side=tk.RIGHT, padx=10)
        
        # 说明文本标签（居中显示）
        info_frame = ttk.Frame(aprs_frame)
        info_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(
            info_frame, 
            text="地图加载可能需要几秒钟时间，请耐心等待",
            justify=tk.CENTER,
            font=("Arial", 10)
        ).pack(anchor=tk.CENTER)
        
        # 在浏览器中打开按钮（居中显示）
        open_frame = ttk.Frame(aprs_frame)
        open_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            open_frame, 
            text="在浏览器中打开APRS地图", 
            command=self.open_aprs_map_in_browser,
            width=25
        ).pack(anchor=tk.CENTER)
    
    def load_aprs_map(self):
        """加载APRS地图到浏览器"""
        # 获取配置
        callsign = self.aprs_callsign_var.get().strip()
        zoom = self.aprs_zoom_var.get()
        maptype = self.aprs_maptype_var.get()
        
        # 构建URL
        if callsign:
            url = f"https://aprs.tv/embedded?z={zoom}&track={callsign}&maptype={maptype}&ct=call,time,dev,speed,dir,alt,power,gain"
        else:
            # 如果不指定呼号，直接打开aprs.tv
            url = "https://aprs.tv/"
        
        # 在浏览器中打开地图
        try:
            webbrowser.open(url)
            self.log_message(f"已在浏览器中打开APRS地图: {url}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开浏览器: {str(e)}")
    
    def open_aprs_map_in_browser(self):
        """在浏览器中打开APRS地图（直接访问aprs.tv）"""
        try:
            webbrowser.open("https://aprs.tv/")
            self.log_message("已打开APRS.TV网站")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开浏览器: {str(e)}")
    
    def decimal_to_aprs_lat(self, decimal):
        """将十进制纬度转换为APRS格式 (ddmm.mmN/S)"""
        direction = 'N' if decimal >= 0 else 'S'
        decimal = abs(decimal)
        degrees = int(decimal)
        minutes = (decimal - degrees) * 60
        return f"{degrees:02d}{minutes:05.2f}{direction}"
    
    def decimal_to_aprs_lon(self, decimal):
        """将十进制经度转换为APRS格式 (dddmm.mmE/W)"""
        direction = 'E' if decimal >= 0 else 'W'
        decimal = abs(decimal)
        degrees = int(decimal)
        minutes = (decimal - degrees) * 60
        return f"{degrees:03d}{minutes:05.2f}{direction}"
    
    def get_current_location(self):
        """获取当前位置（模拟）"""
        # 在实际应用中，这里应该使用地理定位API
        # 这里使用杭州的坐标作为示例
        lat, lon = 30.2741, 120.1551
        
        # 设置地图位置
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(12)
        
        # 添加标记
        if self.marker:
            self.map_widget.delete(self.marker)
        self.marker = self.map_widget.set_marker(lat, lon, text="当前位置")
        
        # 转换为APRS格式
        aprs_lat = self.decimal_to_aprs_lat(lat)
        aprs_lon = self.decimal_to_aprs_lon(lon)
        
        # 更新输入框
        self.latitude_entry.delete(0, tk.END)
        self.latitude_entry.insert(0, aprs_lat)
        
        self.longitude_entry.delete(0, tk.END)
        self.longitude_entry.insert(0, aprs_lon)
        
        # 显示消息
        self.log_message(f"当前位置已设置为: 纬度 {aprs_lat}, 经度 {aprs_lon}")
    
    def set_current_location(self):
        """将地图当前位置设置为输入框的值"""
        if not self.marker:
            messagebox.showwarning("警告", "请先在地图上点击选择一个位置")
            return
        
        position = self.marker.position
        lat, lon = position
        
        # 转换为APRS格式
        aprs_lat = self.decimal_to_aprs_lat(lat)
        aprs_lon = self.decimal_to_aprs_lon(lon)
        
        # 更新输入框
        self.latitude_entry.delete(0, tk.END)
        self.latitude_entry.insert(0, aprs_lat)
        
        self.longitude_entry.delete(0, tk.END)
        self.longitude_entry.insert(0, aprs_lon)
        
        # 显示消息
        self.log_message(f"已设置当前位置: 纬度 {aprs_lat}, 经度 {aprs_lon}")
    
    def show_map_help(self):
        """显示地图帮助信息"""
        help_text = """
        地图使用说明:
        1. 使用鼠标中键（滚轮按钮）在地图上点击设置坐标
        2. 使用鼠标滚轮缩放地图
        3. 点击"获取当前位置"按钮加载示例位置
        4. 点击"设置为当前位置"按钮应用地图上的位置
        
        APRS地图使用说明:
        1. 在"跟踪呼号"输入框中输入呼号（如BG5FNL-7）
        2. 留空可查看全局APRS地图
        3. 设置缩放级别（6-18）和地图类型
        4. 点击"加载地图"在浏览器中查看
        
        注意: 
        - 实际定位功能需要网络连接
        - APRS地图加载可能需要几秒钟时间
        """
        messagebox.showinfo("地图帮助", help_text)
    
    def set_default_values(self):
        """设置默认值"""
        self.callsign_entry.insert(0, "BG5FNL-7")  # 使用用户呼号
        self.path_entry.insert(0, "APRSTV,TCPIP*,qAC,BG2LBF")  # 完整路径
        self.latitude_entry.insert(0, "2947.76N")
        self.longitude_entry.insert(0, "11941.12E")
        self.symbol_table_var.set('/')
        self.symbol_code_var.set('L')
        self.comment_entry.insert(0, "TEST APRS.TV")
        
        # 设备信息
        self.device_info_entry.insert(0, "imei:*418 rssi:-56 sat:20/33 temp:42°C vol:4.2V mileage:1990.5km")
        
        # 软件信息
        self.software_info_entry.insert(0, "APRS TOOL 1.0")
        
        # 更新默认状态消息
        self.status_entry.insert(0, "iGate 144.640MHz 1200bps")
    
    def log_message(self, message):
        """添加消息到日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)  # 滚动到最新消息
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("日志已清空")
    
    def calculate_code(self):
        """计算并显示验证码"""
        callsign = self.callsign_entry.get()
        if not callsign:
            messagebox.showerror("错误", "请输入呼号！")
            return
        
        try:
            # 提取基本呼号（不带标识）
            base_callsign = callsign.split('-')[0] if '-' in callsign else callsign
            code = calculate_aprs_verification_code(base_callsign)
            self.code_label.config(text=f"验证码: {code}")
            self.log_message(f"计算验证码: {base_callsign} -> {code}")
        except Exception as e:
            self.log_message(f"验证码计算错误: {str(e)}")
    
    def get_user_inputs(self):
        """获取用户输入"""
        return {
            "callsign": self.callsign_entry.get(),
            "path": self.path_entry.get(),
            "latitude": self.latitude_entry.get(),
            "longitude": self.longitude_entry.get(),
            "symbol_table": self.symbol_table_var.get(),
            "symbol_code": self.symbol_code_var.get(),
            "comment": self.comment_entry.get(),
            "speed": self.speed_entry.get(),
            "course": self.course_entry.get(),
            "altitude": self.altitude_entry.get(),
            "status": self.status_entry.get(),
            "power": self.power_entry.get(),
            "antenna_height": self.antenna_height_entry.get(),
            "gain": self.gain_entry.get(),
            "device_info": self.device_info_entry.get(),
            "software_info": self.software_info_entry.get()
        }
    
    def send_packet(self):
        """发送APRS数据包（包含扩展信息）"""
        inputs = self.get_user_inputs()
        
        # 验证必填字段
        if not all([inputs["callsign"], inputs["latitude"], inputs["longitude"]]):
            messagebox.showerror("错误", "呼号、纬度和经度是必填字段！")
            return
        
        # 验证呼号格式
        if '-' not in inputs["callsign"]:
            messagebox.showwarning("警告", "呼号应包含标识（如N0CALL-1）")
        
        self.log_message("正在发送APRS数据包...")
        
        # 组合消息内容
        full_comment = inputs["comment"]
        
        # 添加状态信息
        if inputs["status"]:
            full_comment += " " + inputs["status"]
        
        # 在后台线程中发送，避免阻塞GUI
        threading.Thread(
            target=self._send_packet_thread, 
            args=(inputs, full_comment), 
            daemon=True
        ).start()
    
    def _send_packet_thread(self, inputs, full_comment):
        """发送数据包的线程函数"""
        try:
            # 发送数据包
            result = send_aprs_packet(
                callsign=inputs["callsign"],
                path=inputs["path"],
                latitude=inputs["latitude"],
                longitude=inputs["longitude"],
                symbol_table=inputs["symbol_table"],
                symbol_code=inputs["symbol_code"],
                comment=full_comment,
                speed=inputs["speed"] if inputs["speed"] else None,
                course=inputs["course"] if inputs["course"] else None,
                altitude=inputs["altitude"] if inputs["altitude"] else None,
                power=inputs["power"] if inputs["power"] else None,
                antenna_height=inputs["antenna_height"] if inputs["antenna_height"] else None,
                gain=inputs["gain"] if inputs["gain"] else None,
                device_info=inputs["device_info"] if inputs["device_info"] else None,
                software_info=inputs["software_info"] if inputs["software_info"] else None
            )
            
            # 在GUI线程中更新日志
            self.root.after(0, lambda: self._handle_send_result(result))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"发送错误: {str(e)}"))
    
    def _handle_send_result(self, result):
        """处理发送结果"""
        # 显示构建的数据包内容
        self.log_message(f"构建的数据包内容: {result.get('aprs_data', '无')}")
        
        # 根据rs字段判断发送结果
        if result.get("rs") == "ok":
            self.log_message("发送成功! 状态: ok")
            self.log_message(f"消息: {result.get('msg', '无')}")
            self.log_message(f"使用的验证码: {result.get('aprs_word', '未知')}")
        else:
            self.log_message("发送失败! 状态: err")
            error_msg = result.get("message", result.get("msg", "未知错误"))
            self.log_message(f"错误信息: {error_msg}")
            self.log_message(f"使用的验证码: {result.get('aprs_word', '未知')}")
            
            # 显示完整响应（如果有）
            if "raw_response" in result:
                self.log_message(f"原始响应内容: {result['raw_response'][:500]}...")
        
        # 如果开启了JSON显示，打印完整JSON响应
        if self.show_json_var.get():
            try:
                formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
                self.log_message("完整响应JSON:")
                self.log_message(formatted_json)
            except:
                self.log_message("原始响应内容:")
                self.log_message(str(result)[:500] + "...")
    
    def toggle_schedule(self):
        """切换定时发送状态"""
        if self.scheduled_enabled:
            # 停止定时发送
            self.scheduled_enabled = False
            self.schedule_button.config(text="启动定时发送")
            self.status_label.config(text="状态: 已停止")
            self.log_message("定时发送已停止")
        else:
            # 启动定时发送
            try:
                # 获取时间间隔
                interval = self.interval_var.get()
                
                if interval <= 0:
                    raise ValueError("时间间隔必须大于0")
                
                self.scheduled_enabled = True
                self.schedule_button.config(text="停止定时发送")
                self.status_label.config(text=f"状态: 已启动 - 每 {interval} 分钟")
                self.log_message(f"定时发送已启动，每 {interval} 分钟发送一次")
                
                # 启动定时线程
                self.schedule_thread = threading.Thread(target=self.schedule_loop, daemon=True)
                self.schedule_thread.start()
            except ValueError as e:
                messagebox.showerror("错误", f"无效的时间间隔: {str(e)}")
    
    def schedule_loop(self):
        """定时发送循环"""
        interval = self.interval_var.get() * 60  # 转换为秒
        
        while self.scheduled_enabled:
            # 发送数据包
            self.root.after(0, self.send_packet)
            
            # 等待指定间隔
            time_module.sleep(interval)
            
            # 检查是否继续定时发送
            if not self.scheduled_enabled:
                break

# 启动GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = APRSApp(root)
    root.mainloop()
