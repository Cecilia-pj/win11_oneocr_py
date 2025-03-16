import ctypes
import cv2
import sys
import os
import numpy as np
from ctypes import wintypes, Structure, byref, POINTER, c_ubyte

# 定义Img结构体
class Img(Structure):
    _fields_ = [
        ('t', ctypes.c_int32),
        ('col', ctypes.c_int32),
        ('row', ctypes.c_int32),
        ('_unk', ctypes.c_int32),
        ('step', ctypes.c_int64),
        ('data_ptr', ctypes.c_int64),
    ]

# 加载DLL
try:
    script_dir = os.path.abspath(os.path.dirname(__file__))
    os.environ["path"] = script_dir + os.pathsep + os.environ["path"]
    
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if hasattr(kernel32,"SetDllDirectoryW"):
        kernel32.SetDllDirectoryW(script_dir)
    
    oneocr_path = os.path.join(script_dir, "oneocr.dll")
    oneocr = ctypes.WinDLL(oneocr_path)
except OSError as e:
    print(f"Failed to load DLL: {e}")
    sys.exit(1)

# 定义函数原型
# CreateOcrInitOptions
oneocr.CreateOcrInitOptions.argtypes = [ctypes.POINTER(ctypes.c_int64)]
oneocr.CreateOcrInitOptions.restype = ctypes.c_int64

# OcrInitOptionsSetUseModelDelayLoad
oneocr.OcrInitOptionsSetUseModelDelayLoad.argtypes = [ctypes.c_int64, ctypes.c_char]
oneocr.OcrInitOptionsSetUseModelDelayLoad.restype = ctypes.c_int64

# CreateOcrPipeline
oneocr.CreateOcrPipeline.argtypes = [ctypes.c_int64, ctypes.c_int64, ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]
oneocr.CreateOcrPipeline.restype = ctypes.c_int64

# CreateOcrProcessOptions
oneocr.CreateOcrProcessOptions.argtypes = [ctypes.POINTER(ctypes.c_int64)]
oneocr.CreateOcrProcessOptions.restype = ctypes.c_int64

# OcrProcessOptionsSetMaxRecognitionLineCount
oneocr.OcrProcessOptionsSetMaxRecognitionLineCount.argtypes = [ctypes.c_int64, ctypes.c_int64]
oneocr.OcrProcessOptionsSetMaxRecognitionLineCount.restype = ctypes.c_int64

# RunOcrPipeline
oneocr.RunOcrPipeline.argtypes = [ctypes.c_int64, ctypes.POINTER(Img), ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]
oneocr.RunOcrPipeline.restype = ctypes.c_int64

# GetOcrLineCount
oneocr.GetOcrLineCount.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]
oneocr.GetOcrLineCount.restype = ctypes.c_int64

# GetOcrLine
oneocr.GetOcrLine.argtypes = [ctypes.c_int64, ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]
oneocr.GetOcrLine.restype = ctypes.c_int64

# GetOcrLineContent
oneocr.GetOcrLineContent.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]
oneocr.GetOcrLineContent.restype = ctypes.c_int64

def ocr_python(img):
    # 初始化变量
    ctx = ctypes.c_int64()
    pipeline = ctypes.c_int64()
    opt = ctypes.c_int64()
    instance = ctypes.c_int64()
    
    # 创建初始化选项
    res = oneocr.CreateOcrInitOptions(byref(ctx))
    assert res == 0, f"CreateOcrInitOptions failed with code {res}"
    
    # 设置延迟加载模型
    res = oneocr.OcrInitOptionsSetUseModelDelayLoad(ctx, 0)
    assert res == 0, f"OcrInitOptionsSetUseModelDelayLoad failed with code {res}"
    
    # 创建OCR管道
    model_bytes = b"oneocr.onemodel"
    key_bytes = b"kj)TGtrK>f]b[Piow.gU+nC@s\"\"\"\"\"\"4"
    
    # 创建字符串缓冲区
    model_buf = ctypes.create_string_buffer(model_bytes)
    key_buf = ctypes.create_string_buffer(key_bytes)
    
    # 调用CreateOcrPipeline
    res = oneocr.CreateOcrPipeline(
        ctypes.addressof(model_buf),
        ctypes.addressof(key_buf),
        ctx,
        byref(pipeline)
    )
    # res = oneocr.CreateOcrPipeline(ctypes.addressof(model_name), ctypes.addressof(key), ctx, byref(pipeline))
    assert res == 0, f"CreateOcrPipeline failed with code {res}"
    print("OCR model loaded...")
    
    # 创建处理选项
    res = oneocr.CreateOcrProcessOptions(byref(opt))
    assert res == 0, f"CreateOcrProcessOptions failed with code {res}"
    
    # 设置最大识别行数
    res = oneocr.OcrProcessOptionsSetMaxRecognitionLineCount(opt, 1000)
    assert res == 0, f"OcrProcessOptionsSetMaxRecognitionLineCount failed with code {res}"
    
    # 运行OCR管道
    res = oneocr.RunOcrPipeline(pipeline, byref(img), opt, byref(instance))
    assert res == 0, f"RunOcrPipeline failed with code {res}"
    print("Running OCR pipeline...")
    
    # 获取行数
    line_count = ctypes.c_int64()
    res = oneocr.GetOcrLineCount(instance, byref(line_count))
    assert res == 0, f"GetOcrLineCount failed with code {res}"
    print(f"Recognized {line_count.value} lines")
    
    # 遍历每一行
    for lci in range(line_count.value):
        line = ctypes.c_int64()
        res = oneocr.GetOcrLine(instance, lci, byref(line))
        if res != 0 or line.value == 0:
            continue
        
        # 获取行内容
        line_content = ctypes.c_int64()
        res = oneocr.GetOcrLineContent(line, byref(line_content))
        if res == 0 and line_content.value != 0:
            content = ctypes.c_char_p(line_content.value).value.decode('utf-8', errors='ignore')
            print(f"{lci:02d}: {content}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr.py <image_path>")
        sys.exit(1)
    
    # 读取图像
    img_path = sys.argv[1]
    # img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    with open(img_path, 'rb') as f:
        img_bytes = bytearray(f.read())
        
    nparr = np.asarray(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
    if img is None:
        print("Can't read image!")
        sys.exit(1)
    
    # 转换为RGBA
    if img.shape[2] == 3:
        img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    elif img.shape[2] == 4:
        img_rgba = img
    else:
        print("Unsupported image type")
        sys.exit(1)
    
    # 构造Img结构体
    rows, cols = img_rgba.shape[:2]
    channels = img_rgba.shape[2] if len(img_rgba.shape) > 2 else 1
    step = cols * channels
    data_ptr = img_rgba.ctypes.data
    
    img_struct = Img(
        t=3,
        col=cols,
        row=rows,
        _unk=0,
        step=step,
        data_ptr=ctypes.addressof(data_ptr) if isinstance(data_ptr, ctypes._SimpleCData) else data_ptr
    )
    
    # 运行OCR
    ocr_python(img_struct)