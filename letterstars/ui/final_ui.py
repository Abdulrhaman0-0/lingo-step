"""Native touch-first LingoStep UI; 1280x900 reference scaled to Raspberry display."""
import math
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageTk, features
from ..domain.models import LETTERS
from ..services.feedback import AnswerFeedback

W, H = 1280, 900
HAS_RAQM = features.check_feature("raqm")
IVORY = "#FCFAF4"
INK = "#273348"
BLUE = "#45A6F2"
CORAL = "#FF7452"
GOLD = "#FFC524"
TEAL = "#0E6B9D"
PINK = "#FB7C85"
PALE = "#FFE39A"


def font(size, bold=False, arabic=True):
    # DejaVu covers Arabic, Latin and UI symbols in the same mixed text run.
    fonts = (["DejaVuSans-Bold.ttf", "NotoSansArabic-Bold.ttf"] if bold else
             ["DejaVuSans.ttf", "NotoSansArabic-Regular.ttf"]) if arabic else (
             ["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"])
    fonts += ["arialbd.ttf" if bold else "arial.ttf"]
    for name in fonts:
        for folder in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/noto",
                       "C:/Windows/Fonts"):
            p = Path(folder)/name
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


class ScreenPainter:
    def __init__(self):
        self.im = Image.new("RGB", (W, H), IVORY)
        self.draw_ctx = ImageDraw.Draw(self.im)
        self.targets = []

    def rect(self, b, fill, radius=0, outline=None, width=1):
        self.draw_ctx.rounded_rectangle(tuple(map(int, b)), radius=int(radius),
                                       fill=fill, outline=outline, width=width)

    def centered(self, x, y, value, size=28, color=INK, bold=False, arabic=True):
        text = str(value)
        options = {}
        if HAS_RAQM:
            options["direction"] = "rtl" if arabic else "ltr"
        elif arabic:
            import arabic_reshaper
            from bidi.algorithm import get_display
            text = get_display(arabic_reshaper.reshape(text))
        self.draw_ctx.text((int(x), int(y)), text,
                           font=font(size, bold, arabic), fill=color,
                           anchor="mm", **options)

    def star(self, x, y, radius, color):
        pts = []
        for k in range(10):
            angle = k*math.pi/5-math.pi/2
            r = radius if k % 2 == 0 else radius*.45
            pts.append((x+r*math.cos(angle), y+r*math.sin(angle)))
        self.draw_ctx.polygon(pts, fill=color)

    def decorate(self):
        for x, y, r, col in [
            (80,90,21,"#D1EBFA"),(230,120,19,"#FFE58D"),
            (1070,125,18,"#BFDFF7"),(1220,440,16,"#FFD7C6"),
            (80,458,21,"#F5EDC7"),(1120,850,15,"#F7DAE6"),
            (145,820,16,"#BFDDED"),(108,720,10,"#C8EEE2")]:
            self.star(x,y,r,col)

    def logo(self, x=640, y=154, k=1):
        word="LingoStep"
        cols=["#50B7EF","#FF7C83","#FFCC45","#55D9A4","#B881E3",
              "#F87572","#FFCA3F","#61D3C5","#B57AE2"]
        face = font(max(14,int(100*k)),True,False)
        widths=[self.draw_ctx.textlength(c,font=face) for c in word]
        left=x-sum(widths)/2
        for ch,w,color in zip(word,widths,cols):
            self.draw_ctx.text((left+1,y+7*k),ch,font=face,fill="#E3DADD",anchor="lm")
            self.draw_ctx.text((left,y),ch,font=face,fill=color,stroke_width=max(1,int(k*2)),
                               stroke_fill="#FFFDF7",anchor="lm")
            left+=w
        self.star(x-390*k,y-12*k,15*k,"#FFCF57")
        self.star(x+390*k,y+20*k,12*k,"#F39CC9")

    def button(self, action, text, b, color, shadow, fg=INK, size=26):
        x1,y1,x2,y2=b
        self.rect((x1,y1+9,x2,y2+9),shadow,37)
        self.rect(b,color,37)
        self.rect((x1+20,y1+12,x2-20,y1+20),"#FFFFFF",7)
        self.centered((x1+x2)/2,(y1+y2)/2,text,size,fg,True)
        if action:self.targets.append((action,b))

    def header(self, section=""):
        self.button("back","العودة",(34,24,186,86),"#FFFFFF","#CBD4DA",TEAL,19)
        self.rect((1005,26,1250,93),"#E5E5E2",35)
        self.rect((1005,19,1250,85),"#FFFFFF",35)
        self.logo(1128,55,.26)
        if section:
            self.rect((544,112,735,147),"#FFF0C5",18)
            self.centered(640,129,section,18,"#6B501A",True)

    def panel(self, b, fill="#FFFFFF", shadow="#E4E1DC", radius=38):
        x1,y1,x2,y2=b
        self.rect((x1,y1+11,x2,y2+11),shadow,radius)
        self.rect(b,fill,radius)

    def card(self,action,b,fill,shadow,headline,sub,symbol):
        x1,y1,x2,y2=b;mid=(x1+x2)/2
        self.panel(b,fill,shadow,40)
        self.rect((x1+24,y1+17,x2-24,y1+26),"#FFFFFF",8)
        self.draw_ctx.ellipse((mid-48,y1+45,mid+48,y1+141),fill="#FFFFFF9E")
        if symbol == "★":
            self.star(mid,y1+95,25,INK)
        elif symbol == "✓":
            self.draw_ctx.line([(mid-18,y1+95),(mid-4,y1+109),(mid+21,y1+78)],fill=INK,width=6)
        else:
            self.centered(mid,y1+95,symbol,49,INK,True,False)
        self.centered(mid,y1+200,headline,31,"#3F2D23",True)
        self.centered(mid,y1+248,sub,17,"#53483C")
        self.draw_ctx.ellipse((mid-31,y2-79,mid+31,y2-17),fill="#FFFFFF")
        self.draw_ctx.line([(mid-10,y2-47),(mid+10,y2-47)],fill=TEAL,width=3)
        self.draw_ctx.line([(mid+2,y2-55),(mid+10,y2-47),(mid+2,y2-39)],fill=TEAL,width=3)
        self.targets.append((action,b))

    def render(self,page,letter="A",name="",profiles=(),stats=None,recent=(),
               status="",camera=None,model_ready=False,pair_code=None,camera_live=False):
        self.decorate()
        stats=stats or dict(correct=0,total=0,try_again=0,learned=0,letters=[])
        if page=="welcome":
            self.logo(640,150,1.02)
            self.centered(640,324,"مرحبًا بك!",40,INK,True)
            self.centered(640,377,"اختر حساب طفلك لنبدأ رحلة التعلم",24,"#586B7F")
            self.panel((124,420,1156,866),"#FFFFFF","#ECE8E0",38)
            self.centered(1010,478,"من أنت؟",29,INK,True)
            self.rect((158,531,1125,638),"#F7F5F1",22)
            self.centered(1015,552,"إنشاء حساب الطفل",18,"#5F6676",True)
            self.rect((178,568,1104,621),"#FFFFFF",12,"#E2E3E5",2)
            self.button("create","إنشاء حساب وابدأ التعلم",
                        (160,664,1120,735),PINK,"#C7555A","#FFFFFF",27)
            # Existing children are rendered as independently selectable profiles.
            if len(profiles)>4:
                self.button("all_profiles","اختر من الحسابات المحفوظة",
                            (285,781,995,845),"#DDEEFF","#92B7D0",TEAL,19)
            elif profiles:
                self.centered(1026,765,"الحسابات المحفوظة",20,INK,True)
                for i,p in enumerate(profiles):
                    x1=160+(i%4)*240
                    b=(x1,795,x1+219,846)
                    self.rect(b,"#E6F4FF",16)
                    self.centered(x1+110,821,p["name"][:14],16,TEAL,True)
                    self.targets.append(("profile:"+p["id"],b))
            else:
                self.centered(640,802,"رحلتك تبدأ بحرف واحد",18,"#737B89")
        elif page=="home":
            self.button("logout","تسجيل خروج",(34,28,260,94),"#FFFFFF","#CBD4DA",TEAL,22)
            self.rect((995,30,1250,90),"#FFFFFF",30)
            self.centered(1120,60,"حساب: "+name[:15],19,TEAL,True)
            self.logo(640,205,1.0)
            self.card("progress",(68,465,438,818),GOLD,"#8D700B",
                      "الملاحظات والإنجازات","نجومك ومستوى تقدمك","★")
            self.card("revision",(455,465,825,818),CORAL,"#A34327",
                      "المراجعة","تثبيت الحروف","✓")
            self.card("learn",(842,465,1212,818),BLUE,"#1A6086",
                      "التعليم الأساسي","ابدأ المغامرة","A")
        elif page=="learn":
            self.header("المستوى ١")
            self.panel((402,190,880,614),"#FFFFFF","#E1DDD5",42)
            self.star(474,234,16,"#F66A89");self.star(824,237,15,GOLD)
            self.centered(640,414,letter,218,BLUE,True,False)
            self.centered(640,581,"الحرف "+letter,24,"#6B7789",True)
            self.button("speak","التدرب على النطق",(220,655,617,725),CORAL,"#B4472B","#FFFFFF",25)
            self.button("listen","استماع",(665,655,1062,725),BLUE,"#16648E","#FFFFFF",27)
            self.button("prev","السابق",(220,762,617,840),PALE,"#AE8D1A",INK,25)
            self.button("next","التالي",(665,762,1062,840),GOLD,"#AF8400",INK,27)
        elif page=="revision":
            self.header("المراجعة")
            self.panel((247,175,1034,516),"#F4F4EF","#E0DDD4",34)
            if camera is not None:
                im=camera.copy()
                im.thumbnail((750,310))
                self.im.paste(im,(640-im.width//2,345-im.height//2))
            else:
                # Draw the camera directly: emoji fonts vary across Pi OS builds.
                self.rect((568,304,712,396),BLUE,14)
                self.rect((594,287,638,310),BLUE,7)
                self.draw_ctx.ellipse((612,322,668,378),fill="#FFFFFF")
                self.draw_ctx.ellipse((622,332,658,368),fill=BLUE)
                self.centered(640,461,"الكاميرا متوقفة",30,INK,True)
            for x,y,angle in [(280,205,0),(1000,205,1),(280,487,2),(1000,487,3)]:
                self.draw_ctx.arc((x-24,y-24,x+24,y+24),angle*90,angle*90+90,
                                  fill="#95C8E6",width=5)
            self.button("camera","إيقاف الكاميرا" if camera_live else "تشغيل الكاميرا",
                        (430,536,850,602),CORAL if camera_live else BLUE,
                        "#B4472B" if camera_live else "#16648E","#FFFFFF",27)
            self.centered(640,632,"يوقف عرض البطاقة" if camera_live else
                          "يعرض البطاقة للتعرف على الحرف",20,"#586B7F")
            self.panel((247,656,1034,736),"#FFFFFF","#F7D3CB",42)
            self.centered(740,695,"الحرف "+letter+" - ارفع البطاقة المناسبة",23,INK,True)
            self.draw_ctx.ellipse((285,668,345,728),fill=CORAL)
            self.centered(315,697,"♪",28,"#FFFFFF",True,False)
            self.targets.append(("listen",(247,656,1034,736)))
            self.button("prev","السابق",(247,763,615,839),PALE,"#AE8D1A",INK,25)
            self.button("next","التالي",(667,763,1035,839),GOLD,"#AF8400",INK,27)
            if camera is not None and not model_ready:
                self.centered(640,496,"الكاميرا تعمل — موديل الصور غير مثبت",17,CORAL,True)
        elif page=="pairing":
            self.logo(640,115,.55)
            self.panel((170,215,1110,760))
            self.centered(640,280,"ربط حساب ولي الأمر",34,INK,True)
            self.centered(640,337,"أدخل الكود التالي في موقع ولي الأمر",25,INK)
            self.rect((235,382,1045,466),"#E6F4FF",18)
            self.centered(640,424,pair_code or "",30,TEAL,True,False)
            self.centered(640,530,"احتفظ بالكود في مكان خاص.",24,INK)
            self.centered(640,573,"لا تشاركه مع أشخاص غير موثوقين.",24,INK)
            self.button("copy","نسخ الكود",(245,635,615,710),BLUE,"#216A94","#FFFFFF",25)
            self.button("close","إغلاق",(665,635,1035,710),GOLD,"#A98319",INK,25)
        elif page=="progress":
            self.header("الملاحظات والإنجازات")
            self.panel((115,170,1150,823))
            self.centered(640,232,"نجومك وإنجازاتك",39,INK,True)
            self.rect((165,282,1110,434),"#FFE681",30)
            self.centered(470,330,str(stats["correct"]),48,"#8F6515",True,False)
            self.star(540,330,25,"#8F6515")
            self.centered(824,330,f'{stats["learned"]}/26 حرف',43,TEAL,True)
            self.centered(640,398,f'إجمالي المحاولات: {stats["total"]}  •  جرّب تاني: {stats["try_again"]}',21,INK,True)
            self.centered(640,483,"الحروف التي أتقنتها",26,INK,True)
            for i,c in enumerate(LETTERS):
                x=167+(i%13)*73;y=525+(i//13)*61
                mastered=c in stats["letters"]
                self.draw_ctx.ellipse((x,y,x+53,y+53),fill=TEAL if mastered else "#E9E9E6")
                self.centered(x+26,y+26,c,19,"#FFFFFF" if mastered else "#A3A6AD",True,False)
            self.button("pair","ربط حساب ولي الأمر",(175,686,614,764),BLUE,"#216A94","#FFFFFF",22)
            self.button("back","العودة للرحلة",(655,686,1100,764),GOLD,"#A98319",INK,22)
        if status:
            self.rect((300,844,980,894),"#FFF1CF",18)
            self.centered(640,869,status[:70],17,"#78501D",True)
        return self.im,self.targets


class LingoStepApp:
    def __init__(self,lesson,camera,image_model,progress,speech,cloud=None):
        self.lesson,self.camera,self.image_model,self.store,self.speech=(
            lesson,camera,image_model,progress,speech)
        self.cloud=cloud
        self.feedback = AnswerFeedback()
        self.root=tk.Tk()
        self.root.title("LingoStep | Capstone Project")
        self.root.geometry("1100x770")
        self.root.minsize(700,490)
        self.canvas=tk.Canvas(self.root,bg=IVORY,highlightthickness=0)
        self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Configure>",lambda _:self.render())
        self.canvas.bind("<Button-1>",self.on_click)
        self.root.bind("<Escape>",lambda _:self.root.attributes("-fullscreen",False))
        self.root.bind("<F11>",lambda _:self.root.attributes("-fullscreen",
                        not self.root.attributes("-fullscreen")))
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.page="welcome";self.name="";self.status="";self.video=None
        self.camera_live=False;self.mic_busy=False;self.name_entry=None
        self._photo=None;self._targets=[];self._thread_messages=queue.Queue()
        self.root.attributes("-fullscreen",True)
        self.render();self.root.after(150,self.poll_workers)
        self.root.after(30_000,self.periodic_sync)

    def render(self):
        width=max(2,self.canvas.winfo_width())
        height=max(2,self.canvas.winfo_height())
        scale=min(width/W,height/H)
        dw=max(1,int(W*scale));dh=max(1,int(H*scale))
        ox=(width-dw)//2;oy=(height-dh)//2
        self.layout=(scale,ox,oy)
        painter=ScreenPainter()
        stats=self.store.summary() if self.page=="progress" else None
        image,self._targets=painter.render(
            self.page,self.lesson.target,self.name,self.store.students(),stats,
            self.store.recent(5) if self.page=="progress" else [],self.status,
            self.video,self.image_model.ready,camera_live=self.camera_live)
        self._photo=ImageTk.PhotoImage(image.resize((dw,dh),Image.Resampling.BILINEAR))
        self.canvas.delete("all")
        self.canvas.create_image(ox,oy,image=self._photo,anchor="nw")
        if self.page=="welcome":
            if self.name_entry is None:
                self.name_entry=tk.Entry(self.root,justify="center",font=("Arial",18),
                                         relief="flat")
            self.canvas.create_window(ox+641*scale,oy+592*scale,window=self.name_entry,
                                      width=max(220,int(865*scale)),
                                      height=max(32,int(44*scale)))
            self.name_entry.bind("<Return>",lambda _:self.action("create"))

    def on_click(self,event):
        if self.mic_busy:
            return
        scale,ox,oy=self.layout
        px=(event.x-ox)/scale;py=(event.y-oy)/scale
        for action,b in reversed(self._targets):
            if b[0]<=px<=b[2] and b[1]<=py<=b[3]:
                self.action(action)
                break

    def select(self,student_id):
        record=self.store.select_student(student_id)
        self.name=record["name"]
        self.lesson.select("A")
        self.navigate("home")
        self._sync_in_background()

    def action(self,action):
        if action=="create":
            name=self.name_entry.get() if self.name_entry else ""
            try:
                self.select(self.store.create_student(name))
            except ValueError as exc:
                messagebox.showwarning("اسم الطفل",str(exc))
        elif action.startswith("profile:"):
            self.select(action.partition(":")[2])
        elif action=="all_profiles":
            self.profile_picker()
        elif action=="logout":
            self.logout()
        elif action in ("back","home"):
            self.navigate("home" if self.name else "welcome")
        elif action in ("learn","revision","progress"):
            if not self.name:
                self.navigate("welcome")
            else:
                self.navigate(action)
        elif action in ("prev","next"):
            index=LETTERS.index(self.lesson.target)
            self.lesson.select(LETTERS[(index+(1 if action=="next" else -1))%26])
            self.feedback.reset()
            self.status=""
            if self.page=="revision":
                self.stop_camera()
            self.render()
        elif action=="listen":
            try:
                self.lesson.speak()
                self.status="استمع للحرف ثم حاول مرة أخرى"
            except Exception as exc:
                self.status="مشكلة في السماعة: "+str(exc)[:35]
            self.render()
        elif action=="speak":
            self.start_mic()
        elif action=="camera":
            if self.camera_live:
                self.stop_camera()
                self.video=None
                self.status="تم إيقاف الكاميرا"
                self.render()
            else:
                self.start_camera()
        elif action=="pair":
            info=self.store.current_student()
            if info:
                self.pairing_dialog(info["pairing_code"])

    def logout(self):
        if self.mic_busy:
            return
        try:
            self.lesson.voice.stop()
        except Exception:
            pass
        self.store.deselect_student()
        self.name=""
        self.lesson.select("A")
        self.navigate("welcome")

    def pairing_dialog(self, code):
        window = tk.Toplevel(self.root)
        window.title("LingoStep | Parent Account Pairing")
        window.geometry("800x563")
        window.minsize(600, 422)
        window.transient(self.root)
        window.grab_set()
        canvas = tk.Canvas(window, bg=IVORY, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        state = {"copied": False}

        def draw(_=None):
            scale = min(max(1, canvas.winfo_width()) / W,
                        max(1, canvas.winfo_height()) / H)
            width, height = max(1, int(W*scale)), max(1, int(H*scale))
            ox = (canvas.winfo_width()-width)//2
            oy = (canvas.winfo_height()-height)//2
            painter = ScreenPainter()
            im, targets = painter.render("pairing", pair_code=code,
                status="تم نسخ الكود" if state["copied"] else "")
            state.update(scale=scale, ox=ox, oy=oy, targets=targets)
            state["photo"] = ImageTk.PhotoImage(im.resize((width,height),Image.Resampling.LANCZOS))
            canvas.delete("all")
            canvas.create_image(ox,oy,image=state["photo"],anchor="nw")

        def click(event):
            if "scale" not in state:
                return
            x=(event.x-state["ox"])/state["scale"]
            y=(event.y-state["oy"])/state["scale"]
            for action, bounds in state["targets"]:
                x1,y1,x2,y2=bounds
                if x1 <= x <= x2 and y1 <= y <= y2:
                    if action == "close":
                        window.destroy()
                    elif action == "copy":
                        self.root.clipboard_clear()
                        self.root.clipboard_append(code)
                        state["copied"] = True
                        draw()
                    break

        canvas.bind("<Configure>", draw)
        canvas.bind("<Button-1>", click)
        window.bind("<Escape>", lambda _: window.destroy())

    def profile_picker(self):
        profiles=self.store.students()
        window=tk.Toplevel(self.root)
        window.title("اختيار الطفل")
        window.geometry("520x450")
        window.transient(self.root)
        window.grab_set()
        tk.Label(window,text="اختار حساب الطفل",font=("Arial",22,"bold")).pack(pady=14)
        listing=tk.Listbox(window,font=("Arial",18),height=10,justify="right")
        for profile in profiles:
            listing.insert("end",profile["name"])
        listing.pack(fill="both",expand=True,padx=18)
        def choose(_=None):
            selected=listing.curselection()
            if selected:
                child_id=profiles[selected[0]]["id"]
                window.destroy()
                self.select(child_id)
        listing.bind("<Double-Button-1>",choose)
        tk.Button(window,text="متابعة",font=("Arial",19),command=choose).pack(pady=14)

    def navigate(self,page):
        self.stop_camera()
        self.feedback.reset()
        if self.name_entry is not None:
            self.name_entry.destroy()
            self.name_entry=None
        self.page=page;self.video=None;self.status=""
        self.render()

    def start_camera(self):
        try:
            self.camera.open()
        except Exception as exc:
            self.status="الكاميرا غير متاحة: "+str(exc)[:38]
            self.render()
            return
        self.camera_live=True
        self.status="ثبت البطاقة أمام الكاميرا" if self.image_model.ready else (
            "الكاميرا جاهزة — نموذج الصور ناقص")
        self.frame_loop()

    def frame_loop(self):
        if not self.camera_live or self.page!="revision":
            return
        try:
            import cv2
            frame=self.camera.read()
            if frame is None:
                raise RuntimeError("No camera frame")
            self.video=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            if self.image_model.ready:
                result,label,confidence=self.lesson.check_frame(frame)
                if result in ("correct","try_again"):
                    if self.lesson.save_image_result(result,label,confidence):
                        self.stop_camera()
                        self.answer_feedback(result)
                        self._sync_in_background()
                elif result=="unsupported_letter":
                    supported="–".join((self.image_model.labels[0],self.image_model.labels[-1]))
                    self.status="نموذج الكاميرا تجريبي للحروف "+supported+" فقط"
                elif result=="not_recognized":
                    self.status="ثبّت الكارت أمام الكاميرا"
            self.render()
        except Exception as exc:
            self.stop_camera()
            self.status="مشكلة في الكاميرا/التحليل: "+str(exc)[:45]
            self.render()
        if self.camera_live:
            self.root.after(170,self.frame_loop)

    def stop_camera(self):
        self.camera_live=False
        try:
            self.camera.close()
        except Exception:
            pass

    def start_mic(self):
        if self.mic_busy:
            return
        if not self.speech.ready:
            messagebox.showwarning("Vosk", "التعرف على الصوت غير متاح حاليًا:\n"+
                                   self.speech.error)
            return
        # Stop prompts before recording so the microphone hears the child.
        try:
            self.lesson.voice.stop()
        except Exception as exc:
            self.status="تعذر إيقاف الصوت: "+str(exc)[:40]
            self.render()
            return
        target=self.lesson.target
        self.mic_busy=True;self.status="انطق اسم الحرف بالإنجليزي الآن — التسجيل ٣ ثوانٍ"
        self.render()
        def work():
            try:
                result,pred=self.lesson.check_speech(None)
                self._thread_messages.put(("speech",target,result,pred,
                                           self.speech.last_transcript))
            except Exception as exc:
                self._thread_messages.put(("error",str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def poll_workers(self):
        try:
            while True:
                msg=self._thread_messages.get_nowait()
                self.mic_busy=False
                if msg[0]=="error":
                    self.status="تعذر تسجيل الصوت: "+msg[1][:45]
                else:
                    _,letter,result,pred,transcript=msg
                    if result=="correct":
                        self.answer_feedback(result)
                        self._sync_in_background()
                    elif result=="try_again":
                        self.answer_feedback(result)
                        self._sync_in_background()
                    elif self.speech.last_issue == "quiet":
                        self.status="صوت الميكروفون ضعيف جدًا — قرّب الميكروفون وتأكد من اختياره"
                    elif transcript:
                        self.status="سمعنا: "+transcript[:24]+" — انطق اسم حرف واحد بالإنجليزي"
                    else:
                        self.status="وصل صوت لكن لم نتعرف على حرف — حاول مرة أخرى"
                self.render()
        except queue.Empty:
            pass
        self.root.after(150,self.poll_workers)

    def answer_feedback(self, result):
        feedback = self.feedback.answer(result)
        if feedback is None:
            return
        key, self.status = feedback
        try:
            self.lesson.voice.say_feedback(key)
        except Exception as exc:
            self.status += " — تعذر تشغيل الصوت: " + str(exc)[:35]

    def _sync_in_background(self):
        if self.cloud and self.cloud.enabled:
            threading.Thread(target=self.cloud.sync_once,daemon=True).start()

    def periodic_sync(self):
        # Retry unsynced events even when no new lesson occurs after reconnect.
        self._sync_in_background()
        self.root.after(30_000,self.periodic_sync)

    def close(self):
        self.stop_camera()
        self.lesson.voice.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
