"""LingoStep touchscreen UI. Dependency injection, no ML algorithms here."""
import math
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageTk
from ..domain.models import LETTERS

BG='#FCF9F2'; INK='#263347'; BLUE='#45A7F5'; RED='#FF7048'; GOLD='#FFC420'
def ft(n,b=False,ar=True):
    names=(['NotoSansArabic-Bold.ttf','arialbd.ttf','DejaVuSans-Bold.ttf'] if b else ['NotoSansArabic-Regular.ttf','arial.ttf','DejaVuSans.ttf']) if ar else (['DejaVuSans-Bold.ttf','arialbd.ttf'] if b else ['DejaVuSans.ttf','arial.ttf'])
    for directory in ('/usr/share/fonts/truetype/noto','/usr/share/fonts/truetype/dejavu','C:/Windows/Fonts'):
        for name in names:
            p=Path(directory)/name
            if p.exists():return ImageFont.truetype(str(p),n)
    return ImageFont.load_default()

class Painter:
    def __init__(self):
        self.im=Image.new('RGB',(1280,900),BG);self.d=ImageDraw.Draw(self.im);self.hits=[]
    def rect(self,b,c,r=0,outline=None):
        self.d.rounded_rectangle(tuple(map(int,b)),radius=r,fill=c,outline=outline,width=2)
    def text(self,x,y,s,n=27,c=INK,b=False,ar=True):
        self.d.text((x,y),s,font=ft(n,b,ar),fill=c,anchor='mm',direction='rtl' if ar else 'ltr')
    def star(self,x,y,r=16,c=GOLD):
        pts=[]
        for i in range(10):
            a=i*math.pi/5-math.pi/2; rr=r if i%2==0 else r*.42
            pts.append((x+rr*math.cos(a),y+rr*math.sin(a)))
        self.d.polygon(pts,fill=c)
    def decor(self):
        for x,y,r,c in [(55,65,12,GOLD),(206,148,21,'#F1D891'),(1040,133,15,'#BFE5F5'),(1170,800,13,'#F1B6D0'),(380,117,12,'#C3E4F6')]:self.star(x,y,r,c)
    def logo(self,x,y,k=1):
        word='LingoStep'; colors=['#55B3F6','#F77679','#FFD04C','#70D7A4','#B898EF','#F77276','#FACA3D','#6ED9C9','#AF86E9']
        f=ft(round(104*k),True,False); widths=[self.d.textlength(c,font=f) for c in word]
        left=x-sum(widths)/2
        for ch,w,c in zip(word,widths,colors):
            self.d.text((int(left),int(y)),ch,font=f,fill=c,stroke_width=max(1,round(2*k)),stroke_fill='white',anchor='lm');left+=w
        self.star(x-355*k,y-26*k,19*k);self.star(x+350*k,y+37*k,17*k)
    def button(self,action,label,b,color,shadow,fg='white',size=29):
        x1,y1,x2,y2=b
        self.rect((x1,y1+10,x2,y2+10),shadow,36);self.rect(b,color,36)
        self.rect((x1+18,y1+12,x2-18,y1+20),'#FFFFFF',10)
        self.text((x1+x2)/2,(y1+y2)/2+4,label,size,fg,True)
        self.hits.append((action,b))
    def header(self):
        self.rect((35,27,173,85),'#D8DEE5',29);self.rect((35,22,173,79),'white',29)
        self.text(104,52,'العودة',20,'#12628B',True);self.hits.append(('back',(35,22,173,79)))
        self.rect((1000,20,1245,89),'white',33);self.logo(1123,57,.26)
    def card(self,action,b,color,shadow,title,sub,symbol):
        x1,y1,x2,y2=b
        self.rect((x1,y1+12,x2,y2+12),shadow,40);self.rect(b,color,40)
        self.rect((x1+20,y1+14,x2-20,y1+24),'white',8)
        cx=(x1+x2)/2
        self.d.ellipse((cx-47,y1+47,cx+47,y1+141),fill='white')
        self.text(cx,y1+92,symbol,48,INK,True,False)
        self.text(cx,y1+189,title,28,'#37271F',True)
        self.text(cx,y1+236,sub,19,'#47382D')
        self.d.ellipse((cx-28,y2-85,cx+28,y2-29),fill='white')
        self.text(cx,y2-57,'›',28,INK,True,False)
        self.hits.append((action,b))
    def draw(self,page,letter='A',name='',stats=None,recent=None,status='',video=None):
        self.decor();stats=stats or dict(correct=0,total=0,try_again=0)
        if page=='welcome':
            self.logo(640,165,1)
            self.text(640,348,'أهلًا بيك!',41,INK,True)
            self.text(640,410,'اختار حسابك عشان نبدأ رحلة التعلم',25,'#697589')
            self.rect((135,468,1144,805),'#EAE6E1',39);self.rect((135,457,1140,792),'white',39)
            self.text(1035,523,'مين أنت؟',30,INK,True)
            self.text(1010,583,'اكتب اسم الطفل',23,'#5F6874',True)
            self.rect((170,606,1105,678),'#F6F4F0',19,'#E5E0DB')
            self.button('start','ابدأ التعلم',(170,701,1105,769),'#FF7C7B','#C9514B')
        elif page=='home':
            self.rect((1010,26,1250,87),'white',30)
            self.text(1128,57,'حساب: '+(name[:14] or 'الطفل'),20,'#156083',True)
            self.logo(640,237,.98)
            self.card('progress',(60,480,426,828),GOLD,'#91710A','الملاحظات والإنجازات','أوسمتك وهداياك الرائعة','★')
            self.card('revision',(458,480,824,828),RED,'#9E3B22','المراجعة','تثبيت الحروف','✓')
            self.card('learn',(855,480,1220,828),BLUE,'#17658D','التعليم الأساسي','ابدأ المغامرة','A')
        elif page=='learn':
            self.header();self.rect((555,136,725,176),'#FFF0BA',21)
            self.text(640,157,'المستوى ١',20,'#745414',True)
            self.rect((412,205,868,645),'#DEDCD7',43)
            self.rect((412,196,868,632),'white',43)
            self.text(461,239,'♥',32,'#FA6E90',True,False);self.star(822,242,19)
            self.text(640,410,letter,220,BLUE,True,False)
            self.text(640,584,'الحرف '+letter,25,'#64748B')
            self.button('speak','التدرب على النطق',(218,661,616,744),RED,'#A43B22')
            self.button('listen','استماع',(665,661,1063,744),BLUE,'#196996')
            self.button('prev','السابق',(218,776,616,858),'#FFE29A','#A98920',INK)
            self.button('next','التالي',(665,776,1063,858),GOLD,'#A17F1B',INK)
        elif page=='revision':
            self.header();self.rect((554,116,727,156),'#FFF0BA',21);self.text(641,137,'المراجعة  ★',21,'#745414',True)
            self.rect((223,191,1057,620),'#DAD8D2',35)
            self.rect((223,180,1057,609),'#F4F3EF',35,'#E3E1DD')
            if video is not None:
                im=video.copy();im.thumbnail((760,375))
                self.im.paste(im,(int(640-im.width/2),int(392-im.height/2)))
            else:
                self.text(640,347,'◎',120,'#188FC6',True,False)
                self.text(640,475,'افتح الكاميرا!',34,INK,True)
                self.text(640,527,'ارفع الكارت قدام الكاميرا',22,'#607084')
            self.rect((225,666,1055,752),'white',39,'#EFD6D2')
            self.text(716,711,'اسمع الحرف وارفع البطاقة المناسبة',26,INK,True)
            self.d.ellipse((250,677,324,746),fill=RED);self.text(287,712,'▶',27,'white',True,False)
            self.hits.append(('listen',(225,666,1055,752)))
            self.button('camera','فتح / إيقاف الكاميرا',(225,777,612,858),BLUE,'#18658F',size=25)
            self.button('next','التالي',(675,777,1060,858),GOLD,'#A88616',INK)
        elif page=='progress':
            self.header();self.logo(640,178,.75)
            self.text(640,318,'نجومك وإنجازاتك',43,INK,True)
            self.rect((140,380,1140,556),'white',35)
            self.text(946,471,str(stats['correct'])+'  ★',53,'#D09A00',True)
            self.text(628,471,str(stats['total'])+'  محاولة',37,'#2382C4',True)
            self.text(339,471,str(stats['try_again'])+'  إعادة',34,'#E46D51',True)
            self.text(1000,623,'آخر المحاولات',28,INK,True)
            if recent:
                for i,(_,mode,target,observed,result) in enumerate(recent[:3]):
                    self.text(640,675+i*57,target+' ← '+(observed or '-')+'    |    '+('صح' if result=='correct' else 'جرّب تاني'),25,'#506078',True)
            else:self.text(640,720,'لسه مفيش محاولات — يلا نبدأ!',27,'#728097')
            self.button('home','الرئيسية',(465,782,815,854),BLUE,'#1E6894')
        if status and page!='welcome':
            self.rect((365,859,915,899),'#FFF0CF',16)
            self.text(640,880,status[:60],18,'#7A501B',True)
        return self.im,self.hits

class LetterStarsUI:
    def __init__(self,lesson,camera,image_model):
        self.lesson,self.camera,self.image_model=lesson,camera,image_model
        self.root=tk.Tk();self.root.title('LingoStep | Salma STEM')
        self.root.geometry('1100x770');self.root.minsize(640,480)
        self.canvas=tk.Canvas(self.root,bg=BG,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda e:self.render())
        self.canvas.bind('<Button-1>',self.click)
        self.root.bind('<Escape>',lambda e:self.root.attributes('-fullscreen',False))
        self.root.bind('<F11>',lambda e:self.root.attributes('-fullscreen',not self.root.attributes('-fullscreen')))
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.page='welcome';self.name='';self.status='';self.live=False;self.video=None;self.entry=None
        self._photo=None;self._hits=[]
        self.root.attributes('-fullscreen',True);self.render()
    def render(self):
        w=max(self.canvas.winfo_width(),2);h=max(self.canvas.winfo_height(),2)
        k=min(w/1280,h/900);dw=max(1,round(1280*k));dh=max(1,round(900*k))
        ox=(w-dw)//2;oy=(h-dh)//2;self.layout=(k,ox,oy)
        stats=self.lesson.progress.summary() if self.page=='progress' else None
        recent=self.lesson.progress.recent(3) if self.page=='progress' else None
        im,self._hits=Painter().draw(self.page,self.lesson.target,self.name,stats,recent,self.status,self.video)
        self._photo=ImageTk.PhotoImage(im.resize((dw,dh),Image.Resampling.LANCZOS))
        self.canvas.delete('all');self.canvas.create_image(ox,oy,image=self._photo,anchor='nw')
        if self.page=='welcome':
            if self.entry is None:
                self.entry=tk.Entry(self.root,justify='center',font=('Arial',17),relief='flat')
                self.entry.insert(0,self.name)
            self.canvas.create_window(ox+640*k,oy+641*k,window=self.entry,width=max(120,860*k),height=max(25,54*k))
            self.entry.bind('<Return>',lambda e:self.action('start'))
    def navigate(self,page):
        if page!='revision':self.stop_camera()
        if self.entry is not None:self.entry.destroy();self.entry=None
        self.page=page;self.status='';self.video=None;self.render()
    def click(self,event):
        k,ox,oy=self.layout;x=(event.x-ox)/k;y=(event.y-oy)/k
        for name,(x1,y1,x2,y2) in reversed(self._hits):
            if x1<=x<=x2 and y1<=y<=y2:self.action(name);break
    def action(self,name):
        if name=='start':
            self.name=(self.entry.get().strip() if self.entry else '')[:32]
            if not self.name:self.status='اكتب اسم الطفل';messagebox.showinfo('اسم الطفل',self.status);return
            self.navigate('home')
        elif name in ('back','home'):self.navigate('home')
        elif name in ('learn','revision','progress'):self.navigate(name)
        elif name in ('next','prev'):
            i=LETTERS.index(self.lesson.target);self.lesson.select(LETTERS[(i+(1 if name=='next' else -1))%26])
            self.video=None;self.status='';self.render()
        elif name=='listen':
            try:self.lesson.speak();self.status='اسمع الحرف '+self.lesson.target
            except Exception as e:self.status='الصوت مش متاح: '+str(e)
            self.render()
        elif name=='speak':messagebox.showinfo('Speech AI','موديل التعرف على اسم الحرف لسه ما اتسلّمش. مش بنقيّم جودة النطق.')
        elif name=='camera':
            if self.live:self.stop_camera();self.status='تم إيقاف الكاميرا';self.render()
            else:self.start_camera()
    def start_camera(self):
        try:self.camera.open();import cv2
        except Exception as e:
            self.camera.close();self.status='الكاميرا غير متاحة: '+str(e);self.render();return
        self.live=True
        self.status='' if self.image_model.ready else 'عرض كاميرا فقط — AI غير متاح'
        self.frame_loop()
    def frame_loop(self):
        if not self.live or self.page!='revision':return
        try:
            import cv2
            frame=self.camera.read()
            if frame is None:raise RuntimeError('No camera frame')
            self.video=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            if self.image_model.ready:
                result,label,confidence=self.lesson.check_frame(frame)
                if result in ('correct','try_again') and self.lesson.save_image_result(result,label,confidence):
                    self.status='ممتاز! إجابة صح ★' if result=='correct' else 'جرّب تاني'
                    self.stop_camera()
                elif result=='not_recognized':self.status='ثبّت الكارت قدام الكاميرا'
            self.render()
        except Exception as e:
            self.stop_camera();self.status='خطأ في التحليل/الكاميرا: '+str(e);self.render()
        if self.live:self.root.after(150,self.frame_loop)
    def stop_camera(self):
        self.live=False
        try:self.camera.close()
        except Exception:pass
    def close(self):self.stop_camera();self.root.destroy()
    def run(self):self.root.mainloop()
