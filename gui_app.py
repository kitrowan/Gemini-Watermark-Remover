import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, scrolledtext, Menu
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk

# ==========================================
# 第一部分：多语言配置 (Translation Pack)
# ==========================================
LANG_PACK = {
    'cn': {
        'window_title': "Gemini 去水印工具",
        'frame_title': "操作区域",
        'drop_text': "📂\n\n请将图片拖拽到这里\n\n自动保存 PNG + JPG\n(文件名包含精确时间)",
        'log_ready': "✅ 程序就绪。输出格式：原名_日期_时间",
        'log_ignore': "⚠️ 跳过非图片文件: ",
        'log_cancel': "⛔ 用户取消保存",
        'log_start': "⏳ 开始处理: ",
        'log_done': "✨ 队列完成。等待下一个...",
        'save_title': "确认保存位置 (自动生成双格式)",
        'menu_lang': "语言 (Language)",
        'switch_msg': "🌐 语言已切换为中文"
    },
    'en': {
        'window_title': "Gemini Watermark Remover",
        'frame_title': "Drop Zone",
        'drop_text': "📂\n\nDrag & Drop Images Here\n\nAuto Save PNG + JPG\n(With Timestamp)",
        'log_ready': "✅ Ready. Output: name_date_time",
        'log_ignore': "⚠️ Ignored non-image: ",
        'log_cancel': "⛔ Save cancelled by user",
        'log_start': "⏳ Processing: ",
        'log_done': "✨ Queue finished. Waiting for next...",
        'save_title': "Save As (Auto Dual Format)",
        'menu_lang': "Language",
        'switch_msg': "🌐 Language switched to English"
    }
}

# ==========================================
# 第二部分：核心算法 (纯 Pillow 版)
# ==========================================
ALPHA_THRESHOLD = 0.002
MAX_ALPHA = 0.99
LOGO_VALUE = 255

def get_watermark_config(width, height):
    if width > 1024 and height > 1024:
        return 96, 64, 64
    return 48, 32, 32

def load_alpha_map(mask_path, size):
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Missing mask: {mask_path}")
    with Image.open(mask_path) as img:
        img = img.convert("RGB")
        if img.width != size or img.height != size:
            img = img.resize((size, size))
        pixels = list(img.getdata())
    alpha_map = []
    for r, g, b in pixels:
        max_val = max(r, g, b)
        alpha_map.append(max_val / 255.0)
    return alpha_map

def core_process_and_save_dual(input_path, output_base_path, log_func):
    try:
        if not os.path.exists(input_path):
            return False
        with Image.open(input_path) as img:
            img = img.convert("RGBA")
            width, height = img.size
            logo_size, margin_right, margin_bottom = get_watermark_config(width, height)
            
            # 兼容打包路径
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            mask_path = os.path.join(base_path, "assets", f"mask_{logo_size}.png")
            
            log_func(f"⚡ Processing... ({width}x{height})")
            
            alpha_map = load_alpha_map(mask_path, logo_size)
            start_x = width - margin_right - logo_size
            start_y = height - margin_bottom - logo_size
            pixels = img.load()

            for row in range(logo_size):
                y = start_y + row
                if y < 0 or y >= height: continue
                alpha_row_offset = row * logo_size
                for col in range(logo_size):
                    x = start_x + col
                    if x < 0 or x >= width: continue
                    alpha = alpha_map[alpha_row_offset + col]
                    if alpha < ALPHA_THRESHOLD: continue
                    if alpha > MAX_ALPHA: alpha = MAX_ALPHA
                    one_minus_alpha = 1.0 - alpha
                    r, g, b, a = pixels[x, y]
                    r_out = int(round((r - alpha * LOGO_VALUE) / one_minus_alpha))
                    g_out = int(round((g - alpha * LOGO_VALUE) / one_minus_alpha))
                    b_out = int(round((b - alpha * LOGO_VALUE) / one_minus_alpha))
                    pixels[x, y] = (max(0, min(255, r_out)), max(0, min(255, g_out)), max(0, min(255, b_out)), a)
            
            # Save PNG
            png_path = output_base_path + ".png"
            img.save(png_path)
            log_func(f"💾 Saved PNG: {os.path.basename(png_path)}")
            
            # Save JPG
            jpg_path = output_base_path + ".jpg"
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3]) 
            bg.save(jpg_path, quality=95)
            log_func(f"💾 Saved JPG: {os.path.basename(jpg_path)}")
            return True
    except Exception as e:
        log_func(f"❌ Error: {str(e)}")
        return False

# ==========================================
# 第三部分：GUI 界面逻辑 (带语言切换)
# ==========================================

class WatermarkApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.current_lang = 'cn' # 默认中文
        self.configure(bg="#f5f5f5")
        self.geometry("600x480")
        
        # --- 1. 创建菜单栏 ---
        self.menubar = Menu(self)
        self.config(menu=self.menubar)
        
        self.lang_menu = Menu(self.menubar, tearoff=0)
        self.lang_menu.add_command(label="简体中文", command=lambda: self.switch_language('cn'))
        self.lang_menu.add_command(label="English", command=lambda: self.switch_language('en'))
        self.menubar.add_cascade(label="Language/语言", menu=self.lang_menu)

        # --- 2. 界面组件 ---
        self.label_frame = tk.LabelFrame(self, bg="#f5f5f5", font=("微软雅黑", 10))
        self.label_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.drop_label = tk.Label(
            self.label_frame, 
            font=("微软雅黑", 12),
            bg="#ffffff", fg="#555555",
            relief="groove", bd=2
        )
        self.drop_label.pack(fill="both", expand=True, padx=10, pady=10)

        # 绑定拖拽
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.drop_handler)
        self.drop_label.dnd_bind('<<DragEnter>>', lambda e: self.drop_label.config(bg="#e3f2fd"))
        self.drop_label.dnd_bind('<<DragLeave>>', lambda e: self.drop_label.config(bg="#ffffff"))

        self.log_area = scrolledtext.ScrolledText(self, height=10, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill="x", side="bottom", padx=15, pady=10)

        # --- 3. 初始化文本 ---
        self.update_ui_text()
        self.log(self.get_text('log_ready'))

    # --- 辅助方法：获取当前语言文本 ---
    def get_text(self, key):
        return LANG_PACK[self.current_lang].get(key, key)

    # --- 核心：切换语言 ---
    def switch_language(self, lang):
        self.current_lang = lang
        self.update_ui_text()
        self.log(self.get_text('switch_msg'))

    # --- 刷新界面上的所有文字 ---
    def update_ui_text(self):
        self.title(self.get_text('window_title'))
        self.label_frame.config(text=self.get_text('frame_title'))
        self.drop_label.config(text=self.get_text('drop_text'))
        # 更新菜单标题
        self.menubar.entryconfig(1, label=self.get_text('menu_lang'))

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.update() 

    def drop_handler(self, event):
        files = event.data
        if files.startswith('{') and files.endswith('}'): files = files[1:-1]
        if " " in files and not os.path.exists(files):
             file_list = [f.strip('{}') for f in files.split('} {')]
        else:
            file_list = [files]

        for file_path in file_list:
            if not os.path.isfile(file_path): continue
            if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.log(self.get_text('log_ignore') + os.path.basename(file_path))
                continue
            self.process_single_file(file_path)

    def process_single_file(self, input_path):
        directory = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{name}_{timestamp}"
        
        # 使用当前语言的标题
        output_base_path = filedialog.asksaveasfilename(
            title=self.get_text('save_title'),
            initialdir=directory,
            initialfile=default_name,
            filetypes=[("Auto PNG+JPG", "*.*")] 
        )

        if not output_base_path:
            self.log(self.get_text('log_cancel'))
            return

        if output_base_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            output_base_path = os.path.splitext(output_base_path)[0]

        self.log(self.get_text('log_start') + filename + " ...")
        core_process_and_save_dual(input_path, output_base_path, self.log)
        self.log(self.get_text('log_done'))

if __name__ == "__main__":
    mask_check = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "assets", "mask_96.png")
    if not os.path.exists(mask_check):
        tk.messagebox.showerror("Error", "Assets Missing! Please run setup.py first.")
    else:
        app = WatermarkApp()
        app.mainloop()