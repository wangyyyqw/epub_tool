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
        sidebar = ttk.Frame(self, bootstyle=SECONDARY, width=220)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)

        main_content = ttk.Frame(self, padding=25)
        main_content.pack(side=RIGHT, fill=BOTH, expand=True)

        # ================= 侧边栏 =================
        title_lbl = ttk.Label(
            sidebar,
            text="EPUB TOOL",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="inverse-secondary",
        )
        title_lbl.pack(pady=(30, 20), anchor=CENTER)

        btn_frame = ttk.Frame(sidebar, bootstyle=SECONDARY)
        btn_frame.pack(fill=X, padx=20)

        self.create_sidebar_btn(btn_frame, "添加文件", self.add_files, style="light")
        self.create_sidebar_btn(btn_frame, "添加文件夹", self.add_dir, style="light")

        ttk.Separator(sidebar, bootstyle="light").pack(fill=X, padx=20, pady=10)
        self.create_sidebar_btn(btn_frame, "清空列表", self.clear_files, style="danger")

        # ================= 功能按钮区 (移至侧边栏) =================
        action_label = ttk.Label(
            sidebar,
            text="功能列表",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="inverse-secondary",
        )
        action_label.pack(pady=(15, 10))

        action_container = ttk.Frame(sidebar, bootstyle=SECONDARY)
        action_container.pack(fill=X, padx=10)

        actions = [
            ("格式化", reformat_run, "格式化"),
            ("文件解密", decrypt_run, "文件名解密"),
            ("文件加密", encrypt_run, "文件名加密"),
            ("字体加密", run_epub_font_encrypt, "字体加密"),
            ("字体子集化", run_epub_font_subset, "字体子集化"),
            ("图片转WebP", run_img_to_webp, "图片转WebP"),
            ("WebP转图片", run_webp_to_img, "WebP转图片"),
            ("PNG压缩", run_epub_img_transfer, "PNG压缩"),
            ("简转繁", run_s2t, "简转繁"),
            ("繁转简", run_t2s, "繁转简"),
            ("正则注释", None, "正则注释"), # 特殊处理
        ]

        # 使用 Grid 布局实现双列
        for idx, (text, func, name) in enumerate(actions):
            row = idx // 2
            col = idx % 2
            
            if text == "正则注释":
                cmd = self.start_regex_task
            else:
                cmd = lambda f=func, n=name: self.start_task(f, n)

            btn = ttk.Button(
                action_container,
                text=text,
                command=cmd,
                bootstyle="light",  # 统一使用 light 风格
                width=8,
            )
            # 添加 padding
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # 配置列权重，使其均匀分布
        action_container.columnconfigure(0, weight=1)
        action_container.columnconfigure(1, weight=1)

        link_lbl = ttk.Label(
            sidebar,
            text="Github Repository",
            font=("TkDefaultFont", 9, "underline"),
            cursor="hand2",
            bootstyle="inverse-secondary",
        )
        link_lbl.pack(side=BOTTOM, pady=20)
        link_lbl.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://github.com/cnwxi/epub_tool"),
        )

        # ================= 主内容区 =================
        # 使用 PanedWindow 实现垂直分割
        main_pane = ttk.PanedWindow(main_content, orient=VERTICAL)
        main_pane.pack(fill=BOTH, expand=True)

        # --- 上半部分：文件列表 + 控制栏 ---
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=1)

        # 1. 文件列表
        list_label = ttk.Label(
            top_frame,
            text="待处理文件",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="primary",
        )
        list_label.pack(anchor=W, pady=(0, 10))

        tree_frame = ttk.Frame(top_frame)
        tree_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        columns = ("index", "name", "path")
        self.file_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=8, bootstyle="primary"
        )
        self.file_tree.heading("index", text="序号", anchor=CENTER)
        self.file_tree.column("index", width=60, anchor=CENTER, stretch=False)
        self.file_tree.heading("name", text="文件名", anchor=W)
        self.file_tree.column("name", width=200, anchor=W)
        self.file_tree.heading("path", text="完整路径", anchor=W)
        self.file_tree.column("path", anchor=W)

        tree_scroll = ttk.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        self.file_tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.pack(side=RIGHT, fill=Y)

        # 绑定右键菜单
        self.create_context_menus()

        if sys.platform.startswith("darwin"):
            self.file_tree.bind("<Button-2>", self.show_file_menu)

        else:
            self.file_tree.bind("<Button-3>", self.show_file_menu)

        # 2. 路径与操作
        ctrl_frame = ttk.Frame(top_frame)
        ctrl_frame.pack(fill=X, pady=(0, 10))
        self.path_var = tk.StringVar(value="默认: 源文件同级目录")
        path_entry = ttk.Entry(
            ctrl_frame, textvariable=self.path_var, state="readonly", width=40
        )
        path_entry.pack(side=LEFT, padx=(0, 10), fill=X, expand=True)
        ttk.Button(
            ctrl_frame,
            text="设置输出路径",
            command=self.select_output,
            bootstyle="outline-primary",
        ).pack(side=LEFT, padx=5)
        ttk.Button(
            ctrl_frame,
            text="重置路径",
            command=self.reset_output,
            bootstyle="outline-primary",
        ).pack(side=LEFT)

        # 4. 进度条
        self.progress = ttk.Progressbar(
            top_frame,
            bootstyle="success-striped",
            mode="determinate",
            orient=HORIZONTAL,
            length=100,
        )
        self.progress.pack(fill=X, pady=(0, 10))

        # --- 下半部分：日志区域 ---
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=1)

        # 5. 日志区域
        log_label = ttk.Label(
            bottom_frame,
            text="执行日志",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="primary",
        )
        log_label.pack(anchor=W, pady=(10, 10))

        log_frame = ttk.Frame(bottom_frame)
        log_frame.pack(fill=BOTH, expand=True)

        # 注意：增加了 output_path 列
        self.log_tree = ttk.Treeview(
            log_frame,
            columns=("status", "file", "msg", "output_path"),
            show="headings",
            height=5,
            bootstyle="primary",
        )

        self.log_tree.heading("status", text="状态")
        self.log_tree.column("status", width=80, anchor=CENTER, stretch=False)
        self.log_tree.heading("file", text="文件名", anchor=W)
        self.log_tree.column("file", width=200, anchor=W)
        self.log_tree.heading("msg", text="详情信息", anchor=W)
        self.log_tree.column("msg", stretch=True, anchor=W)
        # 隐藏 output_path 列
        self.log_tree.column("output_path", width=0, stretch=False)

        log_scroll = ttk.Scrollbar(
            log_frame, orient=VERTICAL, command=self.log_tree.yview
        )
        self.log_tree.configure(yscrollcommand=log_scroll.set)
        self.log_tree.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill=Y)

        self.log_tree.tag_configure("success", foreground="#198754")
        self.log_tree.tag_configure("error", foreground="#dc3545")
        self.log_tree.tag_configure("skip", foreground="#fd7e14")

        # 绑定日志右键
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
        path = self.file_tree.item(selection[0], "values")[2]
        self._open_path(os.path.dirname(path))

    def remove_selected_file(self):
        selection = self.file_tree.selection()
        if not selection:
            return
        path = self.file_tree.item(selection[0], "values")[2]
        if path in self.file_map:
            del self.file_map[path]
        self.file_tree.delete(selection[0])
        # 重新编号
        for idx, item in enumerate(self.file_tree.get_children()):
            self.file_tree.set(item, "index", idx + 1)

    def open_log_location(self):
        selection = self.log_tree.selection()
        if not selection:
            return
        # 从隐藏的第4列(index 3)获取输出路径
        output_path = self.log_tree.item(selection[0], "values")[3]

        if output_path and os.path.exists(output_path):
            self._open_path(output_path)
        else:
            # 备选方案
            if self.output_dir and os.path.exists(self.output_dir):
                self._open_path(self.output_dir)
            else:
                messagebox.showwarning("提示", "无法找到有效的输出路径记录")

    def open_log_file(self):
        log_path = os.path.join(
            os.path.dirname(os.path.abspath(sys.argv[0])), "log.txt"
        )
        if os.path.exists(log_path):
            self._open_path(log_path)
        else:
            messagebox.showwarning("提示", f"未找到日志文件:\n{log_path}")

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
            messagebox.showerror("错误", f"无法打开路径:\n{e}")

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
                self.file_tree.insert(
                    "", "end", values=(idx, os.path.basename(norm), norm)
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
        from tkinter import simpledialog
        regex_pattern = simpledialog.askstring("正则输入", "请输入匹配正则表达式:", parent=self)
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
        from tkinter import simpledialog
        regex_pattern = simpledialog.askstring("正则输入", "请输入匹配正则表达式:", parent=self)
        if not regex_pattern:
            return

        # 构造带参函数
        def run_with_regex(fp, od):
            return run_regex_footnote(fp, od, regex_pattern)

        self.start_task(run_with_regex, "正则注释")

    def start_task(self, func, task_name):
        items = self.file_tree.get_children()
        if not items:
            messagebox.showwarning("提示", "请先添加文件！")
            return

        self.progress["value"] = 1
        self.progress["maximum"] = len(items) + 1

        file_data = [self.file_tree.item(i, "values")[2] for i in items]
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
            self.msg_queue.put((status, f_name, msg, real_out_dir, tag))
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
                    messagebox.showinfo("完成", "所有任务处理完毕")
                else:
                    # 解析包含 output_path 的数据包
                    status, fname, info, out_path, tag = item
                    self.log_tree.insert(
                        "", 0, values=(status, fname, info, out_path), tags=(tag,)
                    )
                self.msg_queue.task_done()
        except queue.Empty:
            pass
        self.after(100, self.process_queue)


if __name__ == "__main__":
    app = ModernEpubTool()
    app.mainloop()
