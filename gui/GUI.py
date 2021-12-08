import time
import tkinter as tk
from tkinter.constants import RAISED
from tkinter.filedialog import askdirectory
from PIL import ImageTk, Image
import scripts

class App(object):
    def __init__(self, root, microscope, positioner):
        ''' Initialize GUI
        
        '''
        # Title
        root.title("Tomo Controller for Quattro and Smaract positioner - version 0.1")
        # root.iconbitmap('PI.ico')

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
        root.resizable(width=False, height=False)

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

        self.lbl_smara2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Smaract Controller", justify='left')
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

        self.log = tk.StringVar(value="Hello\nWorld!")
        self.lbl_log = tk.Label(master=self.frm_log, width=48, height=38, bg='#2B2B2B', fg='white', textvariable=self.log, justify=tk.LEFT, anchor='nw')
        self.lbl_log.place(x=10, y=10)

        ### Image et Eucentrique
        self.frm_img = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height, bg='#202020')
        self.frm_img.place(x=width//4, y=0)

        image = Image.open('images/cell_15.tif')
        img_width = int(width//2-35)
        img_height = int((width//2-35)*1094/1536)
        image = image.resize((img_width, img_height), Image.ANTIALIAS)
        img_0 = ImageTk.PhotoImage(image)
        self.lbl_img = tk.Label(master=self.frm_img, width=img_width, height=img_height, image=img_0)
        self.lbl_img.photo = img_0
        self.lbl_img.place(x=10, y=height//2-img_height//2)

        self.btn_eucentric = tk.Button(master=self.frm_img, width=20, height=1, bg='#373737', fg='white', text="Set Eucentric", justify='left', command=self.eucentric)
        self.btn_eucentric.place(x=int(width//4-100), y=720)

        self.eucent = tk.StringVar(value='red')
        self.lbl_eucent = tk.Label(master=self.frm_img, width=1, height=1, bg=self.eucent.get())
        self.lbl_eucent.place(x=int(width//4-100)+160, y=720)

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
        self.btn_z_up.place(x=22, y=210)
        self.btn_z_down.place(x=22, y=320)
        self.btn_y_up.place(x=132, y=210)
        self.btn_y_down.place(x=132, y=320)
        self.btn_t_up.place(x=242, y=210)
        self.btn_t_down.place(x=242, y=320)

        self.lbl_z_pos = tk.Label(master=self.frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text="394 325 623" + " nm", justify='left')
        self.lbl_y_pos = tk.Label(master=self.frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text="394 345 623" + " nm", justify='left')
        self.lbl_t_pos = tk.Label(master=self.frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text="39.4°", justify='left')
        self.lbl_z_pos.place(x=20, y=250)
        self.lbl_y_pos.place(x=130, y=250)
        self.lbl_t_pos.place(x=240, y=250)

        self.ent_z_step = tk.Entry(master=self.frm_mov, width=15, bg='#2B2B2B', fg='white', text="394 325 623" + " nm", justify='left')
        self.ent_y_step = tk.Entry(master=self.frm_mov, width=15, bg='#2B2B2B', fg='white', text="394 324 623" + " nm", justify='left')
        self.ent_t_step = tk.Entry(master=self.frm_mov, width=15, bg='#2B2B2B', fg='white', text="39.4°", justify='left')
        self.ent_z_step.place(x=20, y=280)
        self.ent_y_step.place(x=130, y=280)
        self.ent_t_step.place(x=240, y=280)

        ### Acquisition
        self.frm_sav = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height//2, bg='#202020')
        self.frm_sav.place(x=3*width//4, y=height//2)

        self.lbl_tilt_step = tk.Label(master=self.frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Tilt step (°)", justify='left')
        #lbl_nb_imgs   = tk.Label(master=frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Number of images", justify='left')
        self.lbl_name      = tk.Label(master=self.frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Name of project", justify='left')

        self.ent_tilt_step = tk.Entry(master=self.frm_sav, width=20, bg='#2B2B2B', fg='white', text="5", justify='left')
        #ent_nb_imgs   = tk.Entry(master=frm_sav, width=20, bg='#2B2B2B', fg='white', text="100", justify='left')
        self.ent_name      = tk.Entry(master=self.frm_sav, width=20, bg='#2B2B2B', fg='white', text="Project_test", justify='left')

        self.lbl_tilt_step.place(x=20, y=20)
        #lbl_nb_imgs.place(x=20, y=60)
        self.lbl_name.place(x=20, y=100)

        self.ent_tilt_step.place(x=180, y=20)
        #ent_nb_imgs.place(x=180, y=60)
        self.ent_name.place(x=180, y=100)

        self.btn_acquisition = tk.Button(master=self.frm_sav, width=20, height=1, bg='#373737', fg='white', text="Start Acquisition", justify='left', command=self.acquisition)
        self.btn_acquisition.place(x=100, y=200)

        self.acquisition = tk.StringVar(value='red')
        self.lbl_acquisition = tk.Label(master=self.frm_sav, width=1, height=1, bg=self.acquisition.get())
        self.lbl_acquisition.place(x=100+160, y=200)


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
        
        set_eucentric_status = scripts.set_eucentric(self.microscope, self.positioner)
        
        if set_eucentric_status == 0:
            self.lbl_eucent.config(bg='green')
            self.lbl_eucent.update()
            return 0
        return 1
    
    def z_up(self):
        step = self.ent_z_step.get()
        return 0

    def y_up(self):
        step = self.ent_z_step.get()
        return 0

    def t_up(self):
        step = self.ent_y_step.get()
        return 0
    
    def z_down(self):
        step = self.ent_y_step.get()
        return 0
    
    def y_down(self):
        step = self.ent_t_step.get()
        return 0
    
    def t_down(self):
        step = self.ent_t_step.get()
        return 0

    def acquisition(self):
        self.lbl_acquisition.config(bg="orange")
        self.lbl_acquisition.update()
        
        self.lbl_acquisition.config(bg="red")
        self.lbl_acquisition.update()
        '''
        '''
        # set_tomo_status = scripts.tomo_acquisition(self.microscope.micro_settings, self.positioner.smaract_settings, drift_correction=False)
        # if set_tomo_status == 0:
        #     self.lbl_acquisition.config(bg='green')
        #     return 0
        return 1

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root, 0, 0)
    root.mainloop()
