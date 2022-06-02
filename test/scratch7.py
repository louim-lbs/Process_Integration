import tkinter as tk
from concurrent import futures
import time
 
thread_pool_executor = futures.ThreadPoolExecutor(max_workers=1)
 
class App(tk.Frame):
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = tk.Label(self, text='not running')
        self.label.pack()
        self.listbox = tk.Listbox(self)
        self.listbox.pack()
        self.button = tk.Button(
            self, text='blocking task', command=self.acquisition)
        self.button.pack(pady=15)
        self.pack()
 
    def acquisition(self):
        print('acqui')
        thread_pool_executor.submit(self.testlol)
 
    def testlol(self):
        self.label['text'] = 'running'
 
        for number in range(5):
            self.listbox.insert(tk.END, number)
            print(number)
            time.sleep(1)
 
        self.set_label_text(' not running')
 
 
if __name__ == '__main__':
    app = tk.Tk()
    main_frame = App()
    app.mainloop()