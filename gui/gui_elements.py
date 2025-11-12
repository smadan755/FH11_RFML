# this file holds classes used in the Gui tool
from waveform_functions import *
import numpy as np
import json
from dotenv import load_dotenv
import os
import glob as gb

load_dotenv()

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

    # function to convert Waveform configurations to JSON
    def to_json(self, rootpath='', datapath='gui/waveform_data'):
        config_name = f"{self.modulation}-M{self.M}-fs{int(self.fs)}-fc{int(self.fc)}-Tsymb{self.Tsymb}"
        config_name = config_name.replace('.', '_')

        config = {
            "modulation": self.modulation,
            "fs": self.fs,
            "Tsymb": self.Tsymb,
            "fc": self.fc,
            "M": self.M,
            "var": self.var,
            "sps": self.sps,
            "Nysmb": self.Nysmb,
            "output_len": self.output_len
        }
        print(config_name)

        data_folder = os.path.join(rootpath, datapath, config_name)
        os.makedirs(data_folder, exist_ok=True)

        config_file = os.path.join(data_folder, "config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

        # Check if data exists
        if not hasattr(self, 'data') or self.data is None:
            print("No data to save. Call generate_data() first.")
            print(f"Config saved to: {config_file}")
            return

        # Find existing data files and get next index
        existing_files = gb.glob(os.path.join(data_folder, "data_*.npy"))
        if existing_files:
            # Extract indices from filenames like "data_0.npy", "data_1.npy"
            indices = [int(os.path.basename(f).split('_')[1].split('.')[0]) for f in existing_files]
            next_index = max(indices) + 1
        else:
            next_index = 0

        data_file = os.path.join(data_folder, f"data_{next_index}.npy")
        np.save(data_file, self.data)

        print(f"Config saved to: {config_file}")
        print(f"Data saved to: {data_file}")

        return config
