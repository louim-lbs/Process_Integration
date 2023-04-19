import logging
import time
import tkinter as tk
import tkinter.scrolledtext as ScrolledText
from tkinter.constants import RAISED
from tkinter.filedialog import askdirectory
from PIL import ImageTk, Image
#from com_functions import microscope
import scripts_2 as scripts
# import scripts_2_cython as scripts
import threading


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

class App(object):
    def __init__(self, root, microscope, positioner):
        ''' Initialize GUI
        
        '''
        self.rootix = root
        # Title
        root.title("Tomo Controller for Quattro and Smaract positioner - Alpha version")
        root.iconbitmap('gui/img/PI.ico')
        
        try:
            self.microscope = microscope
            self.positioner = positioner
        except:
            self.microscope = 0
            self.positioner = 0

        # Window size
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        width=screenwidth*(73.8/76.8)
        height=screenheight*(65.8/76.8)
        alignstr = '%dx%d+%d+%d' % (width, height, screenwidth/76.8, screenheight*3/76.8)
        root.geometry(alignstr)
        root.resizable(width=True, height=True)

        ### Init
        frm_ini = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//4, height=height//4, bg='#202020')
        frm_ini.place(x=0, y=0)

        try:
            if self.microscope.InitState_status == 0:
                micro1_value = 'green'
            else:
                micro1_value = 'red'
        except:
            micro1_value = 'red'

        self.micro1 = tk.StringVar(value=micro1_value)
        self.lbl_micro1 = tk.Label(master=frm_ini, width=1, height=1, bg=self.micro1.get())
        self.lbl_micro1.place(x=180, y=20)

        self.lbl_micro2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Microscope", justify='left')
        self.lbl_micro2.place(x=20, y=20)

        try:
            if self.positioner.InitState_status == 0:
                smara1_value = 'green'
            else:
                smara1_value = 'red'
        except:
            smara1_value = 'red'

        self.smara1 = tk.StringVar(value=smara1_value)
        self.lbl_smara1 = tk.Label(master=frm_ini, width=1, height=1, bg=self.smara1.get())
        self.lbl_smara1.place(x=180, y=60)

        self.lbl_smara2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Positioner", justify='left')
        self.lbl_smara2.place(x=20, y=60)

        self.lbl_folder1 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Folder", justify='left')
        self.lbl_folder1.place(x=20, y=100)

        path = './path'
        self.lbl_folder2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text=path, justify='right')
        self.lbl_folder2.place(x=180, y=100)

        self.btn_folder1 = tk.Button(master=frm_ini, width=20, height=1, bg='#373737', fg='white', text="Brownse", justify='left', command=self.brownse_path)
        self.btn_folder1.place(x=180, y=125)

        ### Log
        self.frm_log = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//4, height=3*height//4+1, bg='#202020')
        self.frm_log.place(x=0, y=height//4)

        self.lbl_log = ScrolledText.ScrolledText(master=self.frm_log, width=48, height=40, bg='#2B2B2B', fg='white')
        self.lbl_log.vbar.config(troughcolor = 'red', bg = 'blue')
        self.lbl_log.place(x=10, y=10)

        text_handler = TextHandler(self.lbl_log)
        logger = logging.getLogger()
        logger.addHandler(text_handler)

        ### Image et Eucentrique
        self.frm_img = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height, bg='#202020')
        self.frm_img.place(x=width//4, y=0)

        image = Image.open('images/PI_cov-1.tif')
        img_width, img_height = image.size
        image = image.resize((int(width/2-80), int(width/2-80)), Image.ANTIALIAS)
        self.img_0 = ImageTk.PhotoImage(image)
        self.lbl_img = tk.Label(master=self.frm_img, width=width//2-100, height=width//2-100, image=self.img_0, borderwidth=2, relief="groove")
        self.lbl_img.photo = self.img_0
        self.lbl_img.place(x=50, y=25)

        self.btn_eucentric = tk.Button(master=self.frm_img, width=20, height=1, bg='#373737', fg='white', text="Set Eucentric", justify='left', command=self.eucentric)
        self.btn_eucentric.place(x=int(width//4-100), rely=0.88)

        self.btn_zero_eucentric = tk.Button(master=self.frm_img, width=20, height=1, bg='#373737', fg='white', text="Set to Zero", justify='left', command=self.zero_eucentric)
        self.btn_zero_eucentric.place(x=int(width//4-100), rely=0.92)

        self.eucent = tk.StringVar(value='red')
        self.lbl_eucent = tk.Label(master=self.frm_img, width=1, height=1, bg=self.eucent.get())
        self.lbl_eucent.place(x=int(width//4-100)+160, rely=0.88)

        ### Controllers
        self.frm_mov = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height//2, bg='#202020')
        self.frm_mov.place(x=3*width//4, y=0)

        # Microsope
        #

        # Smaract
        self.btn_z_up   = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="↑", justify='left', command=self.z_up)
        self.btn_z_down = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="↓", justify='left', command=self.z_down)
        self.btn_y_up   = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="↑", justify='left', command=self.y_up)
        self.btn_y_down = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="↓", justify='left', command=self.y_down)
        self.btn_t_up   = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="↑", justify='left', command=self.t_up)
        self.btn_t_down = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="↓", justify='left', command=self.t_down)
        self.btn_t_zero = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="0", justify='left', command=self.t_zero)
        self.btn_t_angle = tk.Button(master=self.frm_mov, width=12, height=1, bg='#373737', fg='white', text="Go", justify='left', command=self.t_angle)
        self.btn_z_up.place(x=22, y=210)
        self.btn_z_down.place(x=22, y=320)
        self.btn_y_up.place(x=132, y=210)
        self.btn_y_down.place(x=132, y=320)
        self.btn_t_up.place(x=242, y=210)
        self.btn_t_down.place(x=242, y=320)
        self.btn_t_zero.place(x=242, y=360)
        self.btn_t_angle.place(x=352, y=320)

        positioner_pos   = self.positioner.current_position()
        self.lbl_z_pos   = tk.Label(master=self.frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text=scripts.number_format(positioner_pos[2]) + " m", justify='left')
        self.lbl_y_pos   = tk.Label(master=self.frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text=scripts.number_format(positioner_pos[1]) + " m", justify='left')
        self.lbl_t_pos   = tk.Label(master=self.frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text=scripts.number_format(positioner_pos[3]) + " °", justify='left')
        text1  = tk.StringVar(master=self.frm_mov, value='0')
        self.ent_t_angle = tk.Entry(master=self.frm_mov, width=13, bg='#2B2B2B', fg='white', textvariable=text1, justify='center')
        self.lbl_z_pos.place(x=20, y=250)
        self.lbl_y_pos.place(x=130, y=250)
        self.lbl_t_pos.place(x=240, y=250)
        self.ent_t_angle.place(x=350, y=280)

        ent_step_values1 = tuple(scripts.number_format(1e-9*10**i, 0) for i in range(10))
        ent_step_values2 = (1, 2, 5, 10, 20, 50)
        var1 = tk.StringVar(value='1e-6')
        var2 = tk.StringVar(value='1e-6')
        var3 = tk.StringVar(value='1')
        self.ent_z_step = tk.Spinbox(master=self.frm_mov, width=14, bg='#2B2B2B', readonlybackground='#2B2B2B', fg='white', values=ent_step_values1, justify='center', state='readonly', wrap=True)
        self.ent_y_step = tk.Spinbox(master=self.frm_mov, width=14, bg='#2B2B2B', readonlybackground='#2B2B2B', fg='white', values=ent_step_values1, justify='center', state='readonly', wrap=True)
        self.ent_t_step = tk.Spinbox(master=self.frm_mov, width=14, bg='#2B2B2B', readonlybackground='#2B2B2B', fg='white', values=ent_step_values2, justify='center', state='readonly', wrap=True)
        self.ent_z_step.config(textvariable=var1)
        self.ent_y_step.config(textvariable=var2)
        self.ent_t_step.config(textvariable=var3)

        self.ent_z_step.place(x=20, y=280)
        self.ent_y_step.place(x=130, y=280)
        self.ent_t_step.place(x=240, y=280)

        ### Acquisition
        self.frm_sav = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height//2, bg='#202020')
        self.frm_sav.place(x=3*width//4, y=height//2)

        self.lbl_tilt_step = tk.Label(master=self.frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Tilt step (°)", justify='left')
        self.lbl_end_tilt  = tk.Label(master=self.frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Final tilt (°)", justify='left')
        self.lbl_name      = tk.Label(master=self.frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Name of project", justify='left')
        self.lbl_param     = tk.Label(master=self.frm_sav, width=40, height=1, bg='#2B2B2B', fg='white', text="Other parameters from the microscope", justify='left')

        text1  = tk.StringVar(master=self.frm_sav, value='1')
        text2  = tk.StringVar(master=self.frm_sav, value='70')
        text3  = tk.StringVar(master=self.frm_sav, value='Acquisition')
        self.check1 = tk.BooleanVar(value=True)
        self.check2 = tk.BooleanVar(value=True)
        self.ent_tilt_step = tk.Entry(      master=self.frm_sav, width=20, bg='#2B2B2B', fg='white', textvariable=text1, justify='left')
        self.ent_end_tilt  = tk.Entry(      master=self.frm_sav, width=20, bg='#2B2B2B', fg='white', textvariable=text2, justify='left')
        self.ent_name      = tk.Entry(      master=self.frm_sav, width=20, bg='#2B2B2B', fg='white', textvariable=text3, justify='left')
        self.check_drift   = tk.Checkbutton(master=self.frm_sav, width=17, bg='#2B2B2B', fg='white', activebackground='#2B2B2B', activeforeground='white', selectcolor="#2B2B2B", variable=self.check1, onvalue=True, offvalue=False, text="  Drift correction")
        self.check_focus   = tk.Checkbutton(master=self.frm_sav, width=14, bg='#2B2B2B', fg='white', activebackground='#2B2B2B', activeforeground='white', selectcolor="#2B2B2B", variable=self.check2, onvalue=True, offvalue=False, text="  Auto focus (BC!)")

        self.lbl_tilt_step.place(x=20, y=20)
        self.lbl_end_tilt.place(x=20, y=60)
        self.lbl_name.place(x=20, y=100)
        self.lbl_param.place(x=20, y=180)

        self.ent_tilt_step.place(x=180, y=20)
        self.ent_end_tilt.place(x=180, y=60)
        self.ent_name.place(x=180, y=100)
        self.check_drift.place(x=20, y=140)
        self.check_focus.place(x=180, y=140)

        self.btn_acquisition = tk.Button(master=self.frm_sav, width=20, height=1, bg='#373737', fg='white', text="Start Acquisition", justify='left', command=self.acquisition)
        self.btn_acquisition.place(x=100, y=240)
        
        self.btn_record = tk.Button(master=self.frm_sav, width=20, height=1, bg='#373737', fg='white', text="Record", justify='left', command=self.record)
        self.btn_record.place(x=100, y=290)

        self.btn_stop = tk.Button(master=self.frm_sav, width=20, height=1, bg='#373737', fg='white', text="Stop", justify='center', command=self.stop)
        self.btn_stop.place(x=100, y=340)
        
        self.btn_pause = tk.Button(master=self.frm_sav, width=20, height=1, bg='#373737', fg='white', text="Pause", justify='center', command=self.pause)
        self.btn_pause.place(x=100, y=390)

        self.acquisition_col = tk.StringVar(value='red')
        self.lbl_acquisition = tk.Label(master=self.frm_sav, width=1, height=1, bg=self.acquisition_col.get())
        self.lbl_acquisition.place(x=100+160, y=240)
        
        self.record_col = tk.StringVar(value='red')
        self.lbl_record = tk.Label(master=self.frm_sav, width=1, height=1, bg=self.record_col.get())
        self.lbl_record.place(x=100+160, y=290)


    def brownse_path(self):
        ''' Select the work path       
        '''
        file_path = askdirectory()
        self.lbl_folder2.config(text="..."+file_path[-20:])
        return 0

    def eucentric(self):
        ''' Set the eucentric point
        '''
        self.lbl_eucent.config(bg='orange')
        self.lbl_eucent.update()

        if self.microscope.microscope_type == 'ESEM':
            # set_eucentric_status = scripts.set_eucentric_ESEM_2(self.microscope, self.positioner)
            self.eucentric_ESEM = threading.Thread(target=scripts.set_eucentric, args=(self.microscope, self.positioner))
            self.eucentric_ESEM.start()
        else:
            set_eucentric_status = scripts.set_eucentric(self.microscope, self.positioner)
        
        if set_eucentric_status == 0:
            self.lbl_eucent.config(bg='green')
            self.lbl_eucent.update()
        else:
            self.lbl_eucent.config(bg='red')
            self.lbl_eucent.update()
        return 0

    def zero_eucentric(self):
        ''' Reset eucentric point to zero
        '''
        x, y, z, a, b = self.positioner.current_position()
        if None in (y, z, a):
            return 1
        self.positioner.absolute_move(x, 0, 0, a, b)
        self.microscope.relative_move(0, -y, 0, 0, 0)
        self.microscope.focus(z, 'rel')
        self.lbl_eucent.config(bg='red')
        self.lbl_eucent.update()
        return 0

    def z_up(self):
        step = float(self.ent_z_step.get())
        status = self.positioner.relative_move(0, 0, step, 0, 0)
        if status != 0:
            return 1
        self.lbl_z_pos.config(text=scripts.number_format(self.positioner.current_position()[2]) + ' m')
        self.lbl_z_pos.update()
        return 0

    def y_up(self):
        step = float(self.ent_y_step.get())
        status = self.positioner.relative_move(0, step, 0, 0, 0)
        if status != 0:
            return 1
        self.lbl_y_pos.config(text=scripts.number_format(self.positioner.current_position()[1]) + ' m')
        self.lbl_y_pos.update()
        return 0

    def t_up(self):
        step = float(self.ent_t_step.get())
        status = self.positioner.relative_move(0, 0, 0, step, 0)
        if status != 0:
            return 1
        positioner_t_pos = self.positioner.current_position()[3]
        self.lbl_t_pos.config(text=scripts.number_format(positioner_t_pos) + ' °')
        self.lbl_t_pos.update()
        return 0
    
    def z_down(self):
        step = float(self.ent_z_step.get())
        status = self.positioner.relative_move(0, 0, -step, 0, 0)
        if status != 0:
            return 1
        self.lbl_z_pos.config(text=scripts.number_format(self.positioner.current_position()[2]) + ' m')
        self.lbl_z_pos.update()
        return 0
    
    def y_down(self):
        step = float(self.ent_y_step.get())
        status = self.positioner.relative_move(0, -step, 0, 0, 0)
        if status != 0:
            return 1
        self.lbl_y_pos.config(text=scripts.number_format(self.positioner.current_position()[1]) + ' m')
        self.lbl_y_pos.update()
        return 0
    
    def t_down(self):
        step = float(self.ent_t_step.get())
        status = self.positioner.relative_move(0, 0, 0, -step, 0)
        if status != 0:
            return 1
        positioner_t_pos = self.positioner.current_position()[3]
        self.lbl_t_pos.config(text=scripts.number_format(positioner_t_pos) + ' °')
        self.lbl_t_pos.update()
        return 0

    def t_zero(self):
        x, y, z, a, b = self.positioner.current_position()
        if None in (y, z, a):
            return 1
        self.positioner.absolute_move(x, y, z, -2, b)
        self.positioner.absolute_move(x, y, z, 0, b)
        positioner_t_pos = self.positioner.current_position()[3]
        self.lbl_t_pos.config(text=scripts.number_format(positioner_t_pos) + ' °')
        self.lbl_t_pos.update()
        return 0
    
    def t_angle(self):
        angle = float(self.ent_t_angle.get())
        x, y, z, a, b = self.positioner.current_position()
        if None in (y, z, a):
            return 1
        scripts.absolute_move_with_autocorrect(self.positioner, y, z, angle)
        positioner_t_pos = self.positioner.current_position()[3]
        self.lbl_t_pos.config(text=scripts.number_format(positioner_t_pos) + ' °')
        self.lbl_t_pos.update()
        return 0
  
    # def freeze_btn(self):
    #     self.btn_acquisition.config(state=tk.DISABLED)
    #     self.btn_record.config(state=tk.DISABLED)
    #     self.btn_eucentric.config(state=tk.DISABLED)
    #     self.btn_zero_eucentric.config(state=tk.DISABLED)
    #     self.btn_folder1.config(state=tk.DISABLED)
        
    # def defreeze_btn(self):
    #     self.btn_acquisition.config(state=tk.NORMAL)
    #     self.btn_record.config(state=tk.NORMAL)
    #     self.btn_eucentric.config(state=tk.NORMAL)
    #     self.btn_zero_eucentric.config(state=tk.NORMAL)
    #     self.btn_folder1.config(state=tk.NORMAL)
        
    def acquisition(self):
        self.lbl_acquisition.config(bg="green")
        self.lbl_acquisition.update()

        try:
            global imgID
            imgID = 0
            self.acqui = scripts.acquisition(self.microscope,
                                          self.positioner,
                                          work_folder      = 'data/tomo/',
                                          images_name      = self.ent_name.get(),
                                          resolution       = self.microscope.image_settings()[0],
                                          bit_depth        = 8,
                                          dwell_time       = self.microscope.image_settings()[1],
                                          tilt_increment   = float(self.ent_tilt_step.get()),
                                          tilt_end         = int(self.ent_end_tilt.get()),
                                          drift_correction = self.check1.get(),
                                          focus_correction = self.check2.get(),
                                          square_area      = True)

            self.thread_tomo = threading.Thread(target=self.acqui.tomo)
            self.thread_tomo.start()
            if self.check1.get() == True:
                self.thread_drift_correction = threading.Thread(target=self.acqui.f_drift_correction)
                self.thread_drift_correction.start()
            # if self.check2.get() == True:
            #     self.thread_focus_correction = threading.Thread(target=self.acqui.f_focus_correction, args=(self,))
            #     self.thread_focus_correction.start()
            # else:
            #     self.thread_image_fft = threading.Thread(target=self.acqui.f_image_fft, args=(self,))
            #     self.thread_image_fft.start()
            
        except Exception as e:
            logging.info(str(e))
            pass
        return 0
    
    def record(self):
        ''' Record a tiff movie
        '''
        self.lbl_record.config(bg='green')
        self.lbl_record.update()
        # try:
        self.acqui = scripts.acquisition(self.microscope,
                                    self.positioner,
                                    work_folder      = 'data/record/',
                                    images_name      = self.ent_name.get(),
                                    resolution       = self.microscope.image_settings()[0],
                                    bit_depth        = 8,
                                    dwell_time       = self.microscope.image_settings()[1],
                                    tilt_increment   = float(self.ent_tilt_step.get()),
                                    tilt_end         = int(self.ent_end_tilt.get()),
                                    drift_correction = self.check1.get(),
                                    focus_correction = self.check2.get(),
                                    square_area      = False)
        time.sleep(0.1)
        self.thread_acqui = threading.Thread(target=self.acqui.record)
        self.thread_acqui.start()
        if self.check1.get() == True:
            self.thread_drift_correction = threading.Thread(target=self.acqui.f_drift_correction)
            self.thread_drift_correction.start()
        # if self.check2.get() == True:
        #     self.thread_focus_correction = threading.Thread(target=self.acqui.f_focus_correction, args=(self,))
        #     self.thread_focus_correction.start()
        else:
            pass
            # self.thread_image_fft = threading.Thread(target=self.acqui.f_image_fft, args=(self,))
            # self.thread_image_fft.start()

        # except Exception as e:
        #     logging.info(str(e))
        #     pass
    
        return 0

    def stop(self):
        if hasattr(self, 'acqui') and self.acqui.flag == 0:
            self.acqui.flag = 1
            self.acqui.c.acquire()
            self.acqui.c.notify_all()
            self.acqui.c.release()
       
            try:
                self.thread_acqui.join()
                print('Acquisition thread joined')
            except:
                try:
                    self.thread_tomo.join()
                    print('Tomography thread joined')
                except:
                    print('No thread to join. No acquisition running')
        
            if self.check1.get() == True:
                try:
                    self.thread_drift_correction.join()
                    print('Drift correction thread joined')
                except:
                    pass
            else:
                print('No drift correction to join.')
            # if self.check2.get() == True:
            #     try:
            #         self.thread_focus_correction.join()
            #         print('Focus correction thread joined')
            #     except:
            #         pass
            # try:
            #     self.thread_image_fft.join()
            #     print('FFT thread joined')
            # except:
            #     pass

        self.lbl_eucent.config(bg='red')
        self.lbl_eucent.update()
        self.lbl_acquisition.config(bg="red")
        self.lbl_acquisition.update()
        self.lbl_record.config(bg='red')
        self.lbl_record.update()
        
        self.lbl_img.configure(image = self.img_0)
        self.lbl_img.photo = self.img_0
        self.lbl_img.update()

        self.microscope.tilt_correction(False)
        self.microscope.start_acquisition()
        return 0
    
    def pause(self):
        txt = self.btn_pause.cget('text')
        if txt == 'Pause':
            self.btn_pause.config(text='Resume')
            self.lbl_y_pos.update()
            if hasattr(self, 'acqui') and self.acqui.flag == 0:
                self.acqui.flag = 2
                print('Pause')
        else:
            self.btn_pause.config(text='Pause')
            self.lbl_y_pos.update()
            if hasattr(self, 'acqui') and self.acqui.flag == 2:
                self.acqui.flag = 0
                self.acqui.c.acquire()
                self.acqui.c.notify_all()
                self.acqui.c.release()
        return

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root, 0, 0)
    root.mainloop()