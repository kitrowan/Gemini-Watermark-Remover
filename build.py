import os
import tkinterdnd2
import PyInstaller.__main__

# 1. 获取 tkinterdnd2 的安装路径 (为了解决拖拽库找不到的问题)
dnd_path = os.path.dirname(tkinterdnd2.__file__)

# 2. 确认 assets 文件夹存在
if not os.path.exists("assets"):
    print("❌ 错误：找不到 assets 文件夹！无法打包。")
    exit()

print("🚀 开始打包... 请耐心等待，这可能需要 1-2 分钟。")
print(f"📦 包含拖拽库路径: {dnd_path}")

# 3. 运行 PyInstaller
# 格式: --add-data "源路径;目标路径" (Windows用分号隔开)
PyInstaller.__main__.run([
    'gui_app.py',                  # 你的主程序文件名
    '--name=GeminiRemover',        # 生成的 EXE 名字
    '--onefile',                   # 打包成单个文件
    '--noconsole',                 # 隐藏黑窗口 (静默运行)
    '--clean',                     # 清理缓存
    f'--add-data={dnd_path};tkinterdnd2',  # 强制打包 tkinterdnd2
    '--add-data=assets;assets',            # 强制打包遮罩图片
])

print("\n✅ 打包完成！")
print("请在 'dist' 文件夹中寻找你的 GeminiRemover.exe")