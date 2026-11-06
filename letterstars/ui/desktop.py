"""Touch-first UI only: all decisions and devices live in injected services."""
import tkinter as tk
from tkinter import messagebox
import threading
from ..domain.models import LETTERS

BG="#F6F8FF"; DARK="#23335A"; BLUE="#2563EB"; TEAL="#008C8C"; GOLD="#F59E0B"; PINK="#E74375"

class LetterStarsUI:
    def __init__(self,lesson,camera,image_model):
        self.lesson=lesson;self.camera=camera;self.image_model=image_model
        self.root=tk.Tk();self.root.title("LetterStars | Salma STEM")
        self.root.configure(bg=BG);self.root.geometry("900x700");self.root.minsize(600,500)
        self.root.bind("<Escape>",lambda _:self.set_fullscreen(False))
        self.root.bind("<F11>",lambda _:self.toggle_fullscreen())
        self.fullscreen=False;self.live=False;self.busy=False;self.capture_count=0
        self._screen=None;self.status=tk.StringVar(value="جاهز للتعلم ✨")
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.set_fullscreen(True)
        self.show_home()

    def set_fullscreen(self,enabled):
        self.fullscreen=enabled
        self.root.attributes("-fullscreen",enabled)

    def toggle_fullscreen(self): self.set_fullscreen(not self.fullscreen)
    def clear(self):
        self.stop_camera()
        for child in self.root.winfo_children():child.destroy()
        self._screen=tk.Frame(self.root,bg=BG)
        self._screen.pack(fill="both",expand=True)
        self._screen.grid_columnconfigure(0,weight=1)
        return self._screen

    def title(self,parent,heading,sub=""):
        bar=tk.Frame(parent,bg=BG);bar.pack(fill="x",padx=20,pady=(10,7))
        self.button(bar,"⌂ الرئيسية",self.show_home,bg="#E2E8F0",fg=DARK,small=True).pack(side="left")
        tk.Label(bar,text="★ LetterStars",font=("Arial",16,"bold"),bg=BG,fg=BLUE).pack(side="right")
        tk.Label(parent,text=heading,font=("Arial",26,"bold"),fg=DARK,bg=BG).pack(pady=(5,0))
        if sub:tk.Label(parent,text=sub,font=("Arial",13),fg="#52617F",bg=BG).pack(pady=(0,8))

    def button(self,parent,text,cmd,bg=BLUE,fg="white",small=False):
        return tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,activebackground=bg,
                         font=("Arial",13 if small else 18,"bold"),padx=12,
                         pady=7 if small else 14,relief="flat",cursor="hand2",bd=0,
                         highlightthickness=0,wraplength=230)

    def footer(self,parent):
        tk.Label(parent,textvariable=self.status,fg="#63708D",bg=BG,font=("Arial",11)).pack(side="bottom",pady=6)

    def show_home(self):
        p=self.clear();self.status.set("جاهز للتعلم ✨")
        tk.Label(p,text="🌟",font=("Arial",46),bg=BG).pack(pady=(20,0))
        tk.Label(p,text="LetterStars",font=("Arial",38,"bold"),fg=DARK,bg=BG).pack()
        tk.Label(p,text="حروف الإنجليزي بطريقة ممتعة",font=("Arial",19),fg="#52617F",bg=BG).pack(pady=(4,20))
        wrap=tk.Frame(p,bg=BG);wrap.pack(fill="both",expand=True,padx=32)
        self.button(wrap,"🔤  نتعلم الحروف",self.show_learn,bg=BLUE).pack(fill="x",pady=8)
        self.button(wrap,"📷  نراجع بالكروت",self.show_revision,bg=TEAL).pack(fill="x",pady=8)
        self.button(wrap,"⭐  نجومي وتقدمي",self.show_progress,bg=GOLD,fg=DARK).pack(fill="x",pady=8)
        tk.Label(wrap,text="26 حرف  •  بدون إنترنت للواجهة  •  لمس مباشر",bg=BG,fg="#70809D",font=("Arial",11)).pack(pady=8)
        self.footer(p)

    def choose_letter(self,parent,callback):
        outer=tk.Frame(parent,bg=BG);outer.pack(fill="x",padx=15,pady=5)
        for col in range(7):outer.grid_columnconfigure(col,weight=1)
        for i,letter in enumerate(LETTERS):
            b=tk.Button(outer,text=letter,command=lambda x=letter:callback(x),font=("Arial",15,"bold"),
                        bg="white",fg=DARK,activebackground="#DBEAFE",relief="solid",bd=1,
                        highlightthickness=0,pady=7)
            b.grid(row=i//7,column=i%7,padx=2,pady=2,sticky="nsew")

    def show_learn(self):
        p=self.clear();self.title(p,"🔤 نتعلم الحروف","اختار حرف، اسمعه، وحاول تنطقه")
        big=tk.Label(p,text=self.lesson.target,font=("Arial",110,"bold"),bg=BG,fg=BLUE)
        big.pack(pady=(0,0))
        self.choose_letter(p,lambda c:(self.lesson.select(c),big.configure(text=c),self.status.set(f"الحرف الحالي: {c}")))
        actions=tk.Frame(p,bg=BG);actions.pack(fill="x",padx=20,pady=8)
        self.button(actions,"🔊 اسمع الحرف",self._speak,bg=TEAL,small=True).pack(side="left",expand=True,fill="x",padx=4)
        self.button(actions,"🎤 أنطق الحرف",self._speech_unavailable,bg=PINK,small=True).pack(side="left",expand=True,fill="x",padx=4)
        tk.Label(p,text="التعرف على الصوت: منتظرين موديل الـAI الحقيقي",font=("Arial",12),bg=BG,fg="#667085").pack()
        self.footer(p)

    def _speak(self):
        try:self.lesson.speak();self.status.set(f"تشغيل نطق الحرف {self.lesson.target}")
        except Exception as exc:self.show_error("الصوت",str(exc))

    def _speech_unavailable(self):
        messagebox.showinfo("Speech AI","التعرف على اسم الحرف غير متصل حاليًا.\nده مش تقييم جودة النطق.")

    def show_revision(self):
        p=self.clear();self.title(p,"📷 نراجع بالكروت","اسمع الحرف، وارفع الكارت الصحيح للكاميرا")
        top=tk.Frame(p,bg=BG);top.pack(fill="x",padx=14,pady=3)
        tk.Label(top,text=f"الحرف المطلوب: {self.lesson.target}",font=("Arial",18,"bold"),fg=DARK,bg=BG).pack(side="left",padx=8)
        self.button(top,"🔊 اسمع",self._speak,bg=TEAL,small=True).pack(side="right")
        self.choose_letter(p,lambda c:(self.lesson.select(c),self.show_revision()))
        self.preview=tk.Label(p,text="📸\nهنا هتظهر صورة الكاميرا",font=("Arial",20,"bold"),bg="#E8EDF9",fg="#52617F",height=5)
        self.preview.pack(fill="both",expand=True,padx=24,pady=7)
        self.result=tk.Label(p,text="",font=("Arial",16,"bold"),bg=BG,fg=TEAL)
        self.result.pack()
        buttons=tk.Frame(p,bg=BG);buttons.pack(fill="x",padx=16,pady=8)
        self.button(buttons,"▶ شغّل الكاميرا",self.start_camera,bg=BLUE,small=True).pack(side="left",expand=True,fill="x",padx=4)
        self.button(buttons,"■ إيقاف",self.stop_camera,bg="#64748B",small=True).pack(side="left",expand=True,fill="x",padx=4)
        self.footer(p)
        if not self.image_model.ready:
            self.status.set("AI غير جاهز: "+self.image_model.error)
        else:self.status.set("AI حقيقي محمّل — شغّل الكاميرا")

    def start_camera(self):
        if self.live:return
        if not self.image_model.ready:
            self.status.set("الكاميرا للعرض فقط — موديل AI غير متاح")
        try:
            self.camera.open()
            import cv2
            from PIL import Image,ImageTk
        except Exception as exc:
            self.camera.close();self.show_error("الكاميرا",str(exc));return
        self.live=True;self.capture_count=0;self._frame_loop()

    def _frame_loop(self):
        if not self.live:return
        try:
            frame=self.camera.read()
            if frame is None:raise RuntimeError("Camera returned no frame")
            import cv2
            from PIL import Image,ImageTk
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            image=Image.fromarray(rgb);image.thumbnail((600,270))
            self._tk_image=ImageTk.PhotoImage(image)
            self.preview.configure(image=self._tk_image,text="")
            if self.image_model.ready:
                outcome,label,confidence=self.lesson.check_frame(frame)
            else:
                outcome,label,confidence="no_model",None,None
                self.result.configure(text="عرض كاميرا فقط — مستنيين موديل الـAI الحقيقي",fg=DARK)
            if outcome in ("correct","try_again"):
                if self.lesson.save_image_result(outcome,label,confidence):
                    self.result.configure(text=("🌟 ممتاز! إجابة صح" if outcome=="correct" else "💪 جرب تاني"),
                                          fg=(TEAL if outcome=="correct" else PINK))
                    self.status.set(f"توقع AI: {label} — ثقة {confidence:.0%} (تم حفظ المحاولة)")
                    # Stop rather than log duplicate attempts every camera frame.
                    self.stop_camera();return
            elif outcome == "not_recognized":
                self.result.configure(text="الكارت لسه مش واضح — ثبته قدام الكاميرا",fg=DARK)
        except Exception as exc:
            self.stop_camera();self.show_error("التحليل/الكاميرا",str(exc));return
        self.root.after(100,self._frame_loop)

    def stop_camera(self):
        self.live=False
        self.camera.close()

    def show_progress(self):
        p=self.clear();self.title(p,"⭐ نجومي وتقدمي","نتائج محفوظة على الجهاز نفسه")
        stats=self.lesson.progress.summary()
        tk.Label(p,text=f"🌟 {stats['correct']} نجمة",font=("Arial",34,"bold"),bg=BG,fg=GOLD).pack(pady=12)
        tk.Label(p,text=f"المحاولات: {stats['total']}    |    صح: {stats['correct']}    |    نجرب تاني: {stats['try_again']}",
                 font=("Arial",17,"bold"),bg=BG,fg=DARK).pack(pady=10)
        tk.Label(p,text="آخر المحاولات",font=("Arial",17,"bold"),fg=DARK,bg=BG).pack(pady=8)
        table=tk.Frame(p,bg=BG);table.pack(fill="both",expand=True,padx=16)
        rows=self.lesson.progress.recent(8)
        if not rows:tk.Label(table,text="لسه مفيش محاولات مسجلة",font=("Arial",16),bg=BG,fg="#667085").pack(pady=16)
        for row in rows:
            timestamp,mode,target,observed,result=row
            tk.Label(table,text=f"{timestamp[:16]}  |  {mode}  |  {target} → {observed}  |  {result}",
                     bg="white",fg=DARK,font=("Arial",11),pady=8,anchor="w").pack(fill="x",pady=2)
        self.footer(p)

    def show_error(self,part,details):
        self.status.set(f"مشكلة في {part}: {details}")
        messagebox.showerror(f"مشكلة في {part}",details)

    def close(self):
        self.stop_camera();self.root.destroy()
    def run(self):self.root.mainloop()
