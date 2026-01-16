import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import queue
import time
import webbrowser
import subprocess
import re
import sys

# --- 引入 ttkbootstrap ---
import ttkbootstrap
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox, Querybox

# --- 尝试引入拖拽库 tkinterdnd2 ---
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    BaseClass = TkinterDnD.Tk
    DND_AVAILABLE = True
except ImportError:
    print("未检测到 tkinterdnd2，拖拽功能将禁用。请运行 pip install tkinterdnd2")
    BaseClass = tk.Tk
    DND_AVAILABLE = False

# 模拟导入功能模块
try:
    from utils.encrypt_epub import run as encrypt_run
    from utils.decrypt_epub import run as decrypt_run
    from utils.reformat_epub import run as reformat_run
    from utils.encrypt_font import run_epub_font_encrypt
    from utils.webp_to_img import run as run_webp_to_img
    from utils.img_to_webp import run as run_img_to_webp
    # 导入 PNG压缩 功能
    from utils.webp_to_img import run as run_epub_img_transfer
    from utils.font_subset import run_epub_font_subset
    from utils.chinese_convert import run_s2t, run_t2s
    from utils.regex_footnote import run as run_regex_footnote
except ImportError:

    def mock_run(filepath, outdir, *args):
        time.sleep(0.2)
        return 0

    encrypt_run = decrypt_run = reformat_run = run_epub_font_encrypt = (
        run_webp_to_img
    ) = run_img_to_webp = run_epub_img_transfer = run_epub_font_subset = run_s2t = run_t2s = run_regex_footnote = mock_run


class ModernEpubTool(BaseClass):

    def __init__(self):
        super().__init__()
        self.title("Epub Tool")
        self.geometry("980x700")

        # 手动应用主题 (litera 主题自带较明显的圆角，且风格清新)
        self.style = Style(theme="litera")

        # 窗口居中
        self.update_idletasks()
        width = 980
        height = 700

        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(width, height)
        self.file_map = {}
        self.output_dir = None
        self.msg_queue = queue.Queue()

        self.setup_ui()

        # 注册拖拽 (如果可用)
        if DND_AVAILABLE:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self.on_drop)

        self.after(100, self.process_queue)

    def setup_ui(self):
        # ================= 主布局 =================
        # 侧边栏容器
        sidebar_frame = ttk.Frame(self, bootstyle=SECONDARY, width=240)
        sidebar_frame.pack(side=LEFT, fill=Y)
        sidebar_frame.pack_propagate(False)

        # 主内容容器
        main_content_frame = ttk.Frame(self, padding=20)
        main_content_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # 初始化各部分
        self.setup_sidebar(sidebar_frame)
        self.setup_main_content(main_content_frame)

    def setup_sidebar(self, parent):
        # 1. 标题
        title_lbl = ttk.Label(
            parent,
            text="EPUB TOOL",
            font=("TkDefaultFont", 18, "bold"),
            bootstyle="inverse-secondary",
        )
        title_lbl.pack(pady=(25, 15), anchor=CENTER)

        # 2. 文件操作区 (添加/清空)
        file_ops_frame = ttk.Frame(parent, bootstyle=SECONDARY)
        file_ops_frame.pack(fill=X, padx=15, pady=5)

        self.create_sidebar_btn(file_ops_frame, "📄 添加文件", self.add_files, style="info-outline")
        self.create_sidebar_btn(file_ops_frame, "📂 添加文件夹", self.add_dir, style="info-outline")
        self.create_sidebar_btn(file_ops_frame, "🗑️ 清空列表", self.clear_files, style="danger-outline")

        ttk.Separator(parent, bootstyle="light").pack(fill=X, padx=15, pady=15)

        # 底部链接 (先 Pack，占据底部空间)
        link_lbl = ttk.Label(
            parent,
            text="Github Repository",
            font=("TkDefaultFont", 9, "underline"),
            cursor="hand2",
            bootstyle="inverse-secondary",
        )
        link_lbl.pack(side=BOTTOM, pady=15)
        link_lbl.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://github.com/cnwxi/epub_tool"),
        )

        # 3. 功能按钮区 (Scrollable)
        # 创建一个容器 frame 放置 canvas 和 scrollbar
        action_wrapper = ttk.Frame(parent, bootstyle=SECONDARY)
        action_wrapper.pack(fill=BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(action_wrapper, highlightthickness=0)
        scrollbar = ttk.Scrollbar(action_wrapper, orient="vertical", command=canvas.yview)
        
        # 实际放置按钮的 Frame
        action_container = ttk.Frame(canvas, bootstyle=SECONDARY)
        
        # 在 canvas 中创建窗口
        # width=200 保证宽度大致适配侧边栏
        canvas_window = canvas.create_window((0, 0), window=action_container, anchor="nw", width=210)

        # 配置滚动
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_window_size(event):
            # 调整内部 frame 宽度以适应 canvas
            canvas.itemconfig(canvas_window, width=event.width)

        action_container.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_window_size)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # packing scrollbar FIRST to ensure it reserves space
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            if sys.platform == "darwin":
                # macOS delta 通常较小，不应除以 120
                delta = int(-1 * event.delta)
            else:
                delta = int(-1 * (event.delta / 120))
            canvas.yview_scroll(delta, "units")
        
        # 绑定触发范围：当鼠标进入滚动区域整个容器时
        def _bind_mouse(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux 支持 Button-4/5
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _unbind_mouse(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        action_wrapper.bind("<Enter>", _bind_mouse)
        action_wrapper.bind("<Leave>", _unbind_mouse)


        # 定义分组
        groups = [
            ("常用", [("格式化", reformat_run, "格式化")]),
            ("安全", [
                ("文件解密", decrypt_run, "文件名解密"),
                ("文件加密", encrypt_run, "文件名加密"),
            ]),
            ("字体", [
                ("字体加密", run_epub_font_encrypt, "字体加密"),
                ("字体子集化", run_epub_font_subset, "字体子集化"),
            ]),
            ("图片", [
                ("图转WebP", run_img_to_webp, "图片转WebP"),
                ("WebP还原", run_webp_to_img, "WebP转图片"),
                ("PNG压缩", run_epub_img_transfer, "PNG压缩"),
            ]),
            ("文本", [
                ("简转繁", run_s2t, "简转繁"),
                ("繁转简", run_t2s, "繁转简"),
                ("正则注释", None, "正则注释"),
            ]),
        ]

        # 动态创建分组
        for group_name, actions in groups:
            lf = ttk.Labelframe(
                action_container, 
                text=group_name, 
                bootstyle="secondary",
                padding=5
            )
            lf.pack(fill=X, pady=5, padx=5)
            
            # 配置列权重，实现 2 列均分
            lf.columnconfigure(0, weight=1, uniform="group_btn")
            lf.columnconfigure(1, weight=1, uniform="group_btn")

            for i, (text, func, name) in enumerate(actions):
                if text == "正则注释":
                    cmd = self.start_regex_task
                else:
                    cmd = lambda f=func, n=name: self.start_task(f, n)
                
                # 移除固定 width，使用 sticky="ew" + uniform column 确保大小一致
                btn = ttk.Button(
                    lf,
                    text=text,
                    command=cmd,
                    bootstyle="primary-outline",
                )
                
                row = i // 2
                col = i % 2
                # ipady 增加按钮高度，使其看起来更饱满
                btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew", ipady=5)
        
        # 强制更新滚动区域
        action_container.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))



    def setup_main_content(self, parent):
        # 使用 PanedWindow
        main_pane = ttk.PanedWindow(parent, orient=VERTICAL)
        main_pane.pack(fill=BOTH, expand=True)

        # 上部：文件列表
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=3) # 权重更大
        self.setup_file_list_area(top_frame)

        # 下部：日志
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=2)
        self.setup_log_area(bottom_frame)

    def setup_file_list_area(self, parent):
        # 顶部标题栏 + 路径设置
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="待处理文件",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="primary",
        ).pack(side=LEFT, anchor=W)

        # 路径设置区 (右对齐)
        path_frame = ttk.Frame(header_frame)
        path_frame.pack(side=RIGHT)
        
        self.path_var = tk.StringVar(value="默认: 源文件同级目录") # Moved here from __init__
        path_entry = ttk.Entry(
            path_frame, textvariable=self.path_var, state="readonly", width=35, bootstyle="secondary"
        )
        path_entry.pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            path_frame,
            text="设置输出",
            command=self.select_output,
            bootstyle="outline-secondary",
            width=8
        ).pack(side=LEFT, padx=2)
        
        ttk.Button(
            path_frame,
            text="重置",
            command=self.reset_output,
            bootstyle="outline-secondary",
            width=6
        ).pack(side=LEFT)

        # 文件列表树形图
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True, pady=(0, 5))

        columns = ("index", "name", "size", "path")
        self.file_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", bootstyle="primary", selectmode="extended"
        )
        
        self.file_tree.heading("index", text="#", anchor=CENTER)
        self.file_tree.column("index", width=40, anchor=CENTER, stretch=False)
        
        self.file_tree.heading("name", text="文件名", anchor=W)
        self.file_tree.column("name", width=200, anchor=W, stretch=False)

        self.file_tree.heading("size", text="大小", anchor=CENTER) # 新增大小列
        self.file_tree.column("size", width=80, anchor=CENTER, stretch=False)

        self.file_tree.heading("path", text="完整路径", anchor=W)
        self.file_tree.column("path", anchor=W, stretch=True)

        # 滚动条
        tree_scroll = ttk.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.file_tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.pack(side=RIGHT, fill=Y)

        # 进度条 (放在文件列表下方, 更紧凑)
        self.progress = ttk.Progressbar(
            parent,
            bootstyle="success-striped",
            mode="determinate",
            orient=HORIZONTAL,
        )
        self.progress.pack(fill=X, pady=(5, 0))

        # 绑定事件
        if sys.platform.startswith("darwin"):
            self.file_tree.bind("<Button-2>", self.show_file_menu)
        else:
            self.file_tree.bind("<Button-3>", self.show_file_menu)

    def setup_log_area(self, parent):
        ttk.Label(
            parent,
            text="执行日志",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="info",
        ).pack(anchor=W, pady=(10, 5))

        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=BOTH, expand=True)

        self.log_tree = ttk.Treeview(
            log_frame,
            columns=("time", "status", "file", "msg", "output_path"), # 增加时间列
            show="headings",
            bootstyle="info",
            height=6
        )

        self.log_tree.heading("time", text="时间", anchor=W)
        self.log_tree.column("time", width=80, anchor=W, stretch=False)

        self.log_tree.heading("status", text="状态", anchor=CENTER)
        self.log_tree.column("status", width=60, anchor=CENTER, stretch=False)
        
        self.log_tree.heading("file", text="文件名", anchor=W)
        self.log_tree.column("file", width=150, anchor=W, stretch=False)
        
        self.log_tree.heading("msg", text="信息", anchor=W)
        self.log_tree.column("msg", stretch=True, anchor=W)
        
        self.log_tree.column("output_path", width=0, stretch=False) # 隐藏

        log_scroll = ttk.Scrollbar(
            log_frame, orient=VERTICAL, command=self.log_tree.yview
        )
        self.log_tree.configure(yscrollcommand=log_scroll.set)
        
        self.log_tree.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill=Y)

        self.log_tree.tag_configure("success", foreground="#198754")
        self.log_tree.tag_configure("error", foreground="#dc3545")
        self.log_tree.tag_configure("skip", foreground="#fd7e14")

        if sys.platform.startswith("darwin"):
            self.log_tree.bind("<Button-2>", self.show_log_menu)
        else:
            self.log_tree.bind("<Button-3>", self.show_log_menu)


    # --- 右键菜单逻辑 ---
    def create_context_menus(self):
        # 文件列表菜单
        self.file_menu = tk.Menu(self, tearoff=0)
        self.file_menu.add_command(
            label="打开所在文件夹", command=self.open_file_location
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(label="移除此项", command=self.remove_selected_file)

        # 日志列表菜单
        self.log_menu = tk.Menu(self, tearoff=0)
        self.log_menu.add_command(label="打开输出位置", command=self.open_log_location)
        self.log_menu.add_separator()
        self.log_menu.add_command(
            label="打开日志文件(log.txt)", command=self.open_log_file
        )
        self.log_menu.add_separator()
        self.log_menu.add_command(label="清空日志", command=self.clear_logs)

    def clear_logs(self):
        self.log_tree.delete(*self.log_tree.get_children())

    def show_file_menu(self, event):
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.file_menu.post(event.x_root, event.y_root)

    def show_log_menu(self, event):
        item = self.log_tree.identify_row(event.y)
        if item:
            self.log_tree.selection_set(item)
            self.log_menu.post(event.x_root, event.y_root)

    def open_file_location(self):
        selection = self.file_tree.selection()
        if not selection:
            return
        # path 列现在是 index 3
        path = self.file_tree.item(selection[0], "values")[3]
        self._open_path(os.path.dirname(path))

    def remove_selected_file(self):
        selection = self.file_tree.selection()
        if not selection:
            return
        path = self.file_tree.item(selection[0], "values")[3]
        if path in self.file_map:
            del self.file_map[path]
        self.file_tree.delete(selection[0])
        # 重新编号
        for idx, item in enumerate(self.file_tree.get_children()):
            self.file_tree.set(item, "index", idx + 1)
        
        # 更新进度条最大值? 只有在 start_task 时才设置最大值，所以这里不需要

    def open_log_location(self):
        selection = self.log_tree.selection()
        if not selection:
            return
        # 从隐藏的第5列(index 4)获取输出路径
        output_path = self.log_tree.item(selection[0], "values")[4]

        if output_path and os.path.exists(output_path):
            self._open_path(output_path)
        else:
            # 备选方案
            if self.output_dir and os.path.exists(self.output_dir):
                self._open_path(self.output_dir)
            else:
                Messagebox.show_warning("无法找到有效的输出路径记录", "提示", parent=self)

    def open_log_file(self):
        log_path = os.path.join(
            os.path.dirname(os.path.abspath(sys.argv[0])), "log.txt"
        )
        if os.path.exists(log_path):
            self._open_path(log_path)
        else:
            Messagebox.show_warning(f"未找到日志文件:\n{log_path}", "提示", parent=self)

    def _open_path(self, path):
        """通用打开文件/文件夹方法"""
        try:
            if sys.platform.startswith("darwin"):  # macOS
                subprocess.run(["open", path])
            elif os.name == "nt":  # Windows
                os.startfile(path)
            elif os.name == "posix":  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            Messagebox.show_error(f"无法打开路径:\n{e}", "错误", parent=self)

    # --- 拖拽逻辑 ---
    def on_drop(self, event):
        data = event.data
        files = self._parse_dnd_files(data)
        found_epubs = []
        for path in files:
            if os.path.isfile(path) and path.lower().endswith(".epub"):
                found_epubs.append(path)
            elif os.path.isdir(path):
                for root, _, filenames in os.walk(path):
                    for f in filenames:
                        if f.lower().endswith(".epub"):
                            found_epubs.append(os.path.join(root, f))
        if found_epubs:
            self._update_file_list(found_epubs)

    def _parse_dnd_files(self, data):
        if not data:
            return []
        pattern = r"\{.*?\}|\S+"
        matches = re.findall(pattern, data)
        cleaned_paths = []
        for match in matches:
            path = match.strip("{}")
            if os.path.exists(path):
                cleaned_paths.append(os.path.normpath(path))
        return cleaned_paths

    # --- 基础功能 ---
    def create_sidebar_btn(self, parent, text, command, style="primary"):
        btn = ttk.Button(parent, text=text, command=command, bootstyle=style)
        btn.pack(fill=X, pady=8, ipady=5)
        return btn

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="选择EPUB文件", filetypes=[("EPUB Files", "*.epub *.EPUB")]
        )
        self._update_file_list(files)

    def add_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            found = [
                os.path.join(r, f)
                for r, _, fs in os.walk(folder)
                for f in fs
                if f.lower().endswith(".epub")
            ]
            self._update_file_list(found)

    def _update_file_list(self, files):
        for f in files:
            norm = os.path.normpath(f)
            if norm not in self.file_map:
                self.file_map[norm] = True
                idx = len(self.file_tree.get_children()) + 1
                
                # 获取文件大小
                size_str = ""
                try:
                    size_bytes = os.path.getsize(norm)
                    if size_bytes < 1024:
                        size_str = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        size_str = f"{size_bytes/1024:.1f} KB"
                    else:
                        size_str = f"{size_bytes/(1024*1024):.1f} MB"
                except:
                    size_str = "Unknown"

                self.file_tree.insert(
                    "", "end", values=(idx, os.path.basename(norm), size_str, norm)
                )

    def clear_files(self):
        self.file_tree.delete(*self.file_tree.get_children())
        self.file_map.clear()

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir = os.path.normpath(path)
            self.path_var.set(f"输出路径: {path}")

    def reset_output(self):
        self.output_dir = None
        self.path_var.set("默认: 源文件同级目录")

    def ask_regex_and_run(self, filepath, outdir):
        # 弹窗输入正则
        regex_pattern = Querybox.get_string("请输入匹配正则表达式:", "正则输入", parent=self)
        if not regex_pattern:
            return "skip" # 用户取消或未输入
        
        # 调用实际功能，传入正则参数
        # 注意：start_task 的 _worker 调用时只传了 func, files, out_dir
        # 这里我们需要特殊的处理，或者让 _worker 支持变长参数
        # 但这里的架构是 func(filepath, outdir)
        # 我们可以用偏函数或者闭包，但 start_task 传入的是函数引用
        # 这里的 self.ask_regex_and_run 是被绑定到按钮的
        # 按钮调用的是 lambda: self.start_task(self.ask_regex_and_run, "正则注释")
        # _worker 会调用 self.ask_regex_and_run(f_path, out_dir)
        # 这会导致每次处理一个文件都弹窗！这不对。
        
        # 修正：应该先弹窗一次，获取正则，然后构造一个带参函数传给 start_task
        pass

    def start_regex_task(self):
        regex_pattern = Querybox.get_string("请输入匹配正则表达式:", "正则输入", parent=self)
        if not regex_pattern:
            return

        # 构造带参函数
        def run_with_regex(fp, od):
            return run_regex_footnote(fp, od, regex_pattern)

        self.start_task(run_with_regex, "正则注释")

    def start_task(self, func, task_name):
        items = self.file_tree.get_children()
        if not items:
            Messagebox.show_warning("请先添加文件！", "提示", parent=self)
            return

        self.progress["value"] = 1
        self.progress["maximum"] = len(items) + 1

        # 获取 path 列的数据 (index 3)
        file_data = [self.file_tree.item(i, "values")[3] for i in items]
        self.file_tree.delete(*items)
        self.file_map.clear()

        threading.Thread(
            target=self._worker, args=(func, file_data, self.output_dir), daemon=True
        ).start()

    def _worker(self, func, files, out_dir):
        for i, f_path in enumerate(files):
            f_name = os.path.basename(f_path)

            # 确定实际输出路径 (如果没有指定 out_dir，则默认为源文件目录)
            real_out_dir = out_dir if out_dir else os.path.dirname(f_path)

            try:
                ret = func(f_path, out_dir)
                if ret == 0:
                    tag, status = ("success", "成功")
                elif ret == "skip":
                    tag, status = ("skip", "跳过")
                else:
                    tag, status = ("error", f"失败: {ret}")

                msg = f"输出至: {real_out_dir}"
            except Exception as e:
                tag, status, msg = ("error", "异常", str(e))

            # 传递 real_out_dir 到队列
            timestamp = time.strftime("%H:%M:%S")
            self.msg_queue.put((timestamp, status, f_name, msg, real_out_dir, tag))
            self.msg_queue.put("step")

        self.msg_queue.put("done")

    def process_queue(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                if item == "step":
                    self.progress.step(1)
                elif item == "done":
                    self.progress["value"] = self.progress["maximum"]
                    Messagebox.show_info("所有任务处理完毕", "完成", parent=self)
                else:
                    # 解析包含 output_path 的数据包
                    timestamp, status, fname, info, out_path, tag = item
                    self.log_tree.insert(
                        "", 0, values=(timestamp, status, fname, info, out_path), tags=(tag,)
                    )
                self.msg_queue.task_done()
        except queue.Empty:
            pass
        self.after(100, self.process_queue)


if __name__ == "__main__":
    app = ModernEpubTool()
    app.mainloop()
