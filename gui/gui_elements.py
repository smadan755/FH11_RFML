# this file holds classes used in the Gui tool
from waveform_functions import *
import numpy as np



class Waveform():
    def __init__(self,fs = None, Tsymb = None,Nsymb = None,fc = None, M = None, modulation = None, var = None, eng= None, data = None):
        self.fs = fs
        self.Tsymb = Tsymb
        self.fc = fc
        self.M = M
        self.var = var
        self.sps = fs*Tsymb
        self.Nysmb = Nsymb
        self.output_len = self.sps*self.Nysmb
        self.eng = eng
        self.modulation = modulation
        
        
    def generate_data(self):
        
        match self.modulation:
            case "PAM":
                self.data = self.eng.pam_gui(self.output_len, self.fs, self.Tsymb, self.fc, self.M, self.var)
            case "QAM":
                self.data = self.eng.mqam_gui(self.output_len, self.fs, self.Tsymb, self.fc, self.M)
            case "FSK":
                self.data = self.eng.fsk_gui(self.output_len, self.fs, self.Tsymb, self.fc, self.M)
                
        self.data = np.array(self.data).flatten()
    
    def get_fs(self):
        return self.fs
    
    def get_fc(self):
        return self.fc
    
    def get_M(self):
        return self.M
    
    def get_modulation(self):
        return self.modulation
    
    def get_Nysmb(self):
        return self.Nysmb
    
    def get_Tsymb(self):
        return self.Tsymb
    
    def get_var(self):
        return self.var
    
    def get_data(self):
        return self.data
    
    def get_sps(self):
        return self.sps