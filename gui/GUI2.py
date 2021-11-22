import tkinter as tk
from tkinter.constants import RAISED
from tkinter.filedialog import askdirectory
from PIL import ImageTk, Image
# from smaract.connexion_smaract import smaract_class

class App:
    def __init__(self, root, positioner):
        ''' Initialize GUI
        
        '''

        def brownse_path():
            ''' Select the work path        
            '''
            file_path = askdirectory()
            lbl_folder2.config(text="..."+file_path[-20:])
            return 0

        def eucentric(positioner):
            ''' Set the eucentric point
            '''
            lbl_eucent.config(bg='orange')
            '''
            
            '''
            positioner.getpos()
            lbl_eucent.config(bg='green')
            return 0
        
        def z_up():
            step = ent_z_step.get()
            return 0

        def y_up():
            step = ent_z_step.get()
            return 0

        def t_up():
            step = ent_y_step.get()
            return 0
        
        def z_down():
            step = ent_y_step.get()
            return 0
        
        def y_down():
            step = ent_t_step.get()
            return 0
        
        def t_down():
            step = ent_t_step.get()
            return 0

        def acquisition():
            lbl_acquisition.config(bg="orange")
            '''
            '''
            lbl_acquisition.config(bg="green")
            return 0




        # Title
        root.title("Tomo Controller for Quattro and Smaract device - Alpha version")
        # root.iconbitmap('PI.ico')
        
        # Window size
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        width=screenwidth*(73.8/76.8)
        height=screenheight*(65.8/76.8)
        alignstr = '%dx%d+%d+%d' % (width, height, screenwidth/76.8, screenheight*3/76.8)
        root.geometry(alignstr)
        root.resizable(width=False, height=False)
        # 1536x1094

        ### Init
        frm_ini = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//4, height=height//4, bg='#202020')
        frm_ini.place(x=0, y=0)

        self.micro1 = tk.StringVar(value='red')
        lbl_micro1 = tk.Label(master=frm_ini, width=1, height=1, bg=self.micro1.get())
        lbl_micro1.place(x=180, y=20)

        lbl_micro2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Microscope", justify='left')
        lbl_micro2.place(x=20, y=20)

        self.smara1 = tk.StringVar(value='red')
        lbl_smara1 = tk.Label(master=frm_ini, width=1, height=1, bg=self.smara1.get())
        lbl_smara1.place(x=180, y=60)

        lbl_smara2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Smaract Controller", justify='left')
        lbl_smara2.place(x=20, y=60)

        lbl_folder1 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text="Folder", justify='left')
        lbl_folder1.place(x=20, y=100)

        path = './path'
        lbl_folder2 = tk.Label(master=frm_ini, width=20, height=1, bg='#2B2B2B', fg='white', text=path, justify='right')
        lbl_folder2.place(x=180, y=100)

        btn_folder1 = tk.Button(master=frm_ini, width=20, height=1, bg='#373737', fg='white', text="Brownse", justify='left', command=brownse_path)
        btn_folder1.place(x=180, y=125)

        ### Log
        frm_log = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//4, height=3*height//4+1, bg='#202020')
        frm_log.place(x=0, y=height//4)

        self.log = tk.StringVar(value="Hello\nWorld!")
        lbl_log = tk.Label(master=frm_log, width=48, height=38, bg='#2B2B2B', fg='white', textvariable=self.log, justify=tk.LEFT, anchor='nw')
        lbl_log.place(x=10, y=10)

        ### Image et Eucentrique
        frm_img = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height, bg='#202020')
        frm_img.place(x=width//4, y=0)

        image = Image.open('images/cell_15.tif')
        img_width = int(width//2-35)
        img_height = int((width//2-35)*1094/1536)
        image = image.resize((img_width, img_height), Image.ANTIALIAS)
        img_0 = ImageTk.PhotoImage(image)
        lbl_img = tk.Label(master=frm_img, width=img_width, height=img_height, image=img_0)
        lbl_img.photo = img_0
        lbl_img.place(x=10, y=height//2-img_height//2)

        btn_eucentric = tk.Button(master=frm_img, width=20, height=1, bg='#373737', fg='white', text="Set Eucentric", justify='left', command=eucentric)
        btn_eucentric.place(x=int(width//4-100), y=720)

        self.eucent = tk.StringVar(value='red')
        lbl_eucent = tk.Label(master=frm_img, width=1, height=1, bg=self.eucent.get())
        lbl_eucent.place(x=int(width//4-100)+160, y=720)

        ### Controllers
        frm_mov = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height//2, bg='#202020')
        frm_mov.place(x=3*width//4, y=0)

        # Microsope
        #

        # Smaract
        btn_z_up   = tk.Button(master=frm_mov, width=12, height=1, bg='#373737', fg='white', text="↑", justify='left', command=z_up)
        btn_z_down = tk.Button(master=frm_mov, width=12, height=1, bg='#373737', fg='white', text="↓", justify='left', command=z_down)
        btn_y_up   = tk.Button(master=frm_mov, width=12, height=1, bg='#373737', fg='white', text="↑", justify='left', command=y_up)
        btn_y_down = tk.Button(master=frm_mov, width=12, height=1, bg='#373737', fg='white', text="↓", justify='left', command=y_down)
        btn_t_up   = tk.Button(master=frm_mov, width=12, height=1, bg='#373737', fg='white', text="↑", justify='left', command=t_up)
        btn_t_down = tk.Button(master=frm_mov, width=12, height=1, bg='#373737', fg='white', text="↓", justify='left', command=t_down)
        btn_z_up.place(x=22, y=210)
        btn_z_down.place(x=22, y=320)
        btn_y_up.place(x=132, y=210)
        btn_y_down.place(x=132, y=320)
        btn_t_up.place(x=242, y=210)
        btn_t_down.place(x=242, y=320)

        lbl_z_pos = tk.Label(master=frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text="394 325 623" + " nm", justify='left')
        lbl_y_pos = tk.Label(master=frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text="394 345 623" + " nm", justify='left')
        lbl_t_pos = tk.Label(master=frm_mov, width=13, height=1, bg='#2B2B2B', fg='white', text="39.4°", justify='left')
        lbl_z_pos.place(x=20, y=250)
        lbl_y_pos.place(x=130, y=250)
        lbl_t_pos.place(x=240, y=250)

        ent_z_step = tk.Entry(master=frm_mov, width=15, bg='#2B2B2B', fg='white', text="394 325 623" + " nm", justify='left')
        ent_y_step = tk.Entry(master=frm_mov, width=15, bg='#2B2B2B', fg='white', text="394 324 623" + " nm", justify='left')
        ent_t_step = tk.Entry(master=frm_mov, width=15, bg='#2B2B2B', fg='white', text="39.4°", justify='left')
        ent_z_step.place(x=20, y=280)
        ent_y_step.place(x=130, y=280)
        ent_t_step.place(x=240, y=280)

        ### Acquisition
        frm_sav = tk.Frame(master=root, relief=RAISED, borderwidth=4, width=width//2, height=height//2, bg='#202020')
        frm_sav.place(x=3*width//4, y=height//2)

        lbl_tilt_step = tk.Label(master=frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Tilt step (°)", justify='left')
        #lbl_nb_imgs   = tk.Label(master=frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Number of images", justify='left')
        lbl_name      = tk.Label(master=frm_sav, width=20, height=1, bg='#2B2B2B', fg='white', text="Name of project", justify='left')

        ent_tilt_step = tk.Entry(master=frm_sav, width=20, bg='#2B2B2B', fg='white', text="5", justify='left')
        #ent_nb_imgs   = tk.Entry(master=frm_sav, width=20, bg='#2B2B2B', fg='white', text="100", justify='left')
        ent_name      = tk.Entry(master=frm_sav, width=20, bg='#2B2B2B', fg='white', text="Project_test", justify='left')

        lbl_tilt_step.place(x=20, y=20)
        #lbl_nb_imgs.place(x=20, y=60)
        lbl_name.place(x=20, y=100)

        ent_tilt_step.place(x=180, y=20)
        #ent_nb_imgs.place(x=180, y=60)
        ent_name.place(x=180, y=100)

        btn_acquisition = tk.Button(master=frm_sav, width=20, height=1, bg='#373737', fg='white', text="Start Acquisition", justify='left', command=acquisition)
        btn_acquisition.place(x=100, y=200)

        self.acquisition = tk.StringVar(value='red')
        lbl_acquisition = tk.Label(master=frm_sav, width=1, height=1, bg=self.acquisition.get())
        lbl_acquisition.place(x=100+160, y=200)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
