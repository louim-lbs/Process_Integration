import ctypes
import logging
from typing import List
from smaract_folder.smaract_lib import smaract_lib_client64
import smaract_folder.connexion_smaract_64bits as connexion_smaract
import time

# logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=print)
smaract = connexion_smaract.smaract_class(calibrate=False)
print(smaract.getpos())