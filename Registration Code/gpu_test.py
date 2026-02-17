import glfw

if not glfw.init():
    raise SystemExit("glfw.init failed")

glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
win = glfw.create_window(64, 64, "test", None, None)
print("window:", "ok" if win else "failed")

if win:
    glfw.make_context_current(win)
    print("context current ok")
    glfw.destroy_window(win)

glfw.terminate()


'''
import ctypes
import os

# Check which GPU is being used
try:
    nvidia_smi = os.popen("nvidia-smi --query-gpu=gpu_name --format=csv,noheader").read().strip()
    print(f"GPU in use: {nvidia_smi}")
except:
    print("Could not query GPU")

# Try to detect OpenGL support via ctypes
try:
    opengl = ctypes.windll.opengl32
    print("OpenGL32.dll found and loaded")
except Exception as e:
    print(f"OpenGL32.dll error: {e}")

# Check environment variables
print(f"DISPLAY: {os.environ.get('DISPLAY', 'not set')}")
print(f"PATH: {os.environ.get('PATH', '')[:100]}...")
'''