
import subprocess
import fcntl
import os
import time
import threading


def refresh_network():
    # تفعيل وضع الطيران
    os.system("settings put global airplane_mode_on 1 >/dev/null 2>&1")
    os.system("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true >/dev/null 2>&1")
    
    # الانتظار لثانية واحدة حتى يفصل المودم
    #time.sleep(0.5)
    
    # إغلاق وضع الطيران للبحث عن الشبكة بالإعداد الجديد
    os.system("settings put global airplane_mode_on 0 >/dev/null 2>&1")
    os.system("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false >/dev/null 2>&1")


# ثوابت النظام
EVIOCGRAB = 1074021776
TOUCH_DEV = "/dev/input/event2"
STATE_FILE = "/data/adb/touch_state.txt"

# قائمة التطبيقات المراد إخفاؤها
HIDDEN_APPS = [
    "bin.mt.plus.canary",
    "com.touchtype.swiftkey",
    "com.horizons.tut",
    "io.github.virresh.matvt",
    "com.facebook.katana",
    "com.google.android.apps.bard",
    "com.google.android.googlequicksearchbox",
    "com.termux",
    "com.topjohnwu.magisk",
    "com.whatsapp",
    "com.zhiliaoapp.musically.go",
    "app.morphe.android.youtube",
    "com.android.chrome",
    "com.android.vending",
    "com.google.android.gm.lite",
    #"com.google.android.youtube",
    "org.telegram.gold",
    "app.revanced.android.gms",
    "app.revanced.android.youtube",
    "com.android.settings",
    "com.google.android.inputmethod.latin"
    
]


# متغير عالمي للاحتفاظ بقفل التاتش
touch_fd = None
CAMERA_PKG = "com.mediatek.camera"

def apply_state(state):
    global touch_fd
    try:
        if state == "OFF":
            # 1. إيقاف التاتش فوراً (أول شيء يحدث في أجزاء من الثانية)
            if touch_fd is None:
                touch_fd = open(TOUCH_DEV, "rb")
            fcntl.ioctl(touch_fd, EVIOCGRAB, 1)
            
            # 2. تجهيز سلة أوامر لتنفيذها دفعة واحدة (تجميع الأوامر)
            cmds = [
                "svc data disable",
                "settings put global preferred_network_mode1 1",
                "settings put global preferred_network_mode2 1",
                "chmod 000 /dev/kd_camera_hw /dev/camera-isp /dev/CAM_CAL_DRV",
                "mv /data/media/0/Android /data/media/0/.Zd",
                "mkdir -p /data/media/0/.fake_media",
                "mount -o bind /data/media/0/.fake_media /data/media/0/.Zd/media",
                "mount -o bind /data/media/0/.fake_media /data/media/0/.Zd/data"

            ]
            
            # إضافة أوامر التطبيقات للسلة
            for app in HIDDEN_APPS:
                cmds.append(f"pm disable {app}")
                cmds.append(f"pm hide {app}")
                
            # دمج جميع الأوامر برمز "&" لتنفيذها معاً في نفس اللحظة (Parallel)
            full_cmd = " & ".join(cmds)
            subprocess.Popen(f"({full_cmd}) >/dev/null 2>&1", shell=True)

            # 3. تشغيل ريفريش الشبكة في مسار جانبي (Thread) لكي لا يوقف السكريبت
            threading.Thread(target=refresh_network).start()
            
            print("[+] MILITARY MODE ACTIVE: Instant execution triggered.")
               
        else:
            # 1. تشغيل التاتش فوراً
            if touch_fd is not None:
                fcntl.ioctl(touch_fd, EVIOCGRAB, 0)
                touch_fd.close()
                touch_fd = None

            # 2. تجهيز سلة أوامر الإظهار
            cmds = [
                "settings put global preferred_network_mode1 9",
                "settings put global preferred_network_mode2 9",
                
                "umount /data/media/0/.Zd/media",
                "umount /data/media/0/.Zd/data",                
                "rm -rf /data/media/0/Android",
                "mv /data/media/0/.Zd /data/media/0/Android"
            


            ]
            
            for app in HIDDEN_APPS:
                cmds.append(f"pm enable {app}")
                cmds.append(f"pm unhide {app}")
                
            full_cmd = " & ".join(cmds)
            subprocess.Popen(f"({full_cmd}) >/dev/null 2>&1", shell=True)
            
            # 3. تشغيل ريفريش الشبكة في مسار جانبي
            threading.Thread(target=refresh_network).start()
                
            print("[+] CIVILIAN MODE ACTIVE: Instant execution triggered.")
            
    except Exception as e:
        print(f"Error: {e}")


# التأكد من وجود ملف الذاكرة لضمان الاستدامة
if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, "w") as f:
        f.write("ON")

with open(STATE_FILE, "r") as f:
    current_state = f.read().strip()

# تطبيق الحالة المحفوظة بمجرد تشغيل السكريبت
apply_state(current_state)

print("[-] Stealth Daemon is running... Listening for codes.")

# تشغيل getevent كمراقب خلفي بدون استهلاك بطارية
process = subprocess.Popen(['getevent', '-l', '/dev/input/event1'], stdout=subprocess.PIPE, text=True)

# ---------------------------------------------------------
# منطقة الشفرات السرية المفصولة
# 1. شفرة التفعيل السريعة (0 ثم 0 ثم *) لإيقاف التاتش
ACTIVATION_CODE = ["KEY_0", "KEY_0", "KEY_SWITCHVIDEOMODE"]

# 2. شفرة الفتح المعقدة (سهم لأسفل ثم 2 ثم 00* ثم 00#) لإعادة التاتش
# ملاحظة: تأكد من اسم زر السهم لأسفل من getevent، غالبا يكون KEY_DOWN أو KEY_DPAD_DOWN
DEACTIVATION_CODE = [
    "KEY_DOWN", 
    "KEY_2", 
    "KEY_0", 
    "KEY_0", 
    "KEY_SWITCHVIDEOMODE", 
    "KEY_0", 
    "KEY_0", 
    "KEY_NUMERIC_POUND"
]


TERMUX_CODE = ["KEY_8", "KEY_3", "KEY_7", "KEY_6", "KEY_8", "KEY_9"]

# ---------------------------------------------------------


# متغيرات التوقيت والطابور
# متغيرات التوقيت والطابور
key_press_times = {}
key_buffer = []
LONG_PRESS_DURATION = 2  

for line in iter(process.stdout.readline, ''):
    parts = line.split()
    if not parts:
        continue
        
    # استخراج اسم الزر من السطر
    pressed_key = None
    for word in parts:
        if word.startswith("KEY_"):
            pressed_key = word
            break
            
    if not pressed_key:
        continue

    # استخراج حالة الزر الحقيقية (دائماً تكون الكلمة الأخيرة في مخرجات getevent)
    action = parts[-1]

    # 1. لحظة الضغط (DOWN)
    if action == "DOWN":
        key_press_times[pressed_key] = time.time()

    # 2. لحظة رفع الإصبع (UP)
    elif action == "UP":
        if pressed_key in key_press_times:
            # حساب الفارق الزمني
            press_duration = time.time() - key_press_times[pressed_key]
            del key_press_times[pressed_key] # تنظيف الذاكرة للزر
            
            # تحديد نوع الضغطة (عادية أم مطولة)
            if press_duration >= LONG_PRESS_DURATION:
                final_key_action = f"{pressed_key}_LONG"
            else:
                final_key_action = pressed_key
                
            # إدخال الزر بالصيغة النهائية في الطابور
            key_buffer.append(final_key_action)
            
            # ---------------------------------------------------------
            # [المكان الصحيح لفحص شفرة استدعاء Termux الاحتياطية]
            current_termux_buffer = key_buffer[-len(TERMUX_CODE):]
            if current_termux_buffer == TERMUX_CODE:
                os.system("pm unhide com.termux >/dev/null 2>&1")
                os.system("pm enable com.termux >/dev/null 2>&1")
                # إطلاق الواجهة الرسومية للتطبيق
                os.system("am start -n com.termux/com.termux.app.TermuxActivity >/dev/null 2>&1")
                key_buffer = [] # تفريغ الطابور
                continue # العودة للمراقبة فوراً
            # ---------------------------------------------------------

            # تحديد الشفرة المطلوبة بناءً على حالة الهاتف الحالية
            if current_state == "ON":
                target_code = ACTIVATION_CODE
                target_state = "OFF"
            else:
                target_code = DEACTIVATION_CODE
                target_state = "ON"
            
            # قص الطابور ليكون بنفس طول الشفرة المطلوبة حالياً
            current_buffer = key_buffer[-len(target_code):]
            
            # مقارنة الطابور بالشفرة المطلوبة
            if current_buffer == target_code:
                current_state = target_state
                with open(STATE_FILE, "w") as f:
                    f.write(current_state)
                apply_state(current_state)
                
                # تفريغ الطابور تماماً بعد نجاح الشفرة
                key_buffer = []
