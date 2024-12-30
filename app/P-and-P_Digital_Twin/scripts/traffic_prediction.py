import os 
import math
import argparse


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA

class TrafficPrediction():
    
    def read_from_csv(self, filename, sample_period):
        self.df = pd.read_csv(filename)
        # parse time from unix to pandas format
        self.df['frame.time_epoch'] = pd.to_datetime(self.df['frame.time_epoch'], unit='s')   
        
        # resample
        self.df.set_index('frame.time_epoch', inplace=True)  
        self.df = self.df.resample(sample_period).sum(numeric_only=True).fillna(0) 
        
        # convert from bytes to Mbps
        self.df['frame.len'] /= pd.Timedelta(sample_period).total_seconds()
        self.df['frame.len'] *= 8 
        self.df['frame.len'] /= 2**20
        
    
    def run_arima(self, order, training_split=.8):
        # percentage of the input data to be used as training, the rest will just be testing data           
        self.training_data = self.df.iloc[:int(training_split*len(self.df))] 
        
        model = ARIMA( self.training_data, order=order)
        fitted_model = model.fit()
        
        # print(fitted_model.summary())

        self.prediction = fitted_model.predict(start=self.df.index.min(),end=self.df.index.max())
            
    def plot(self, ax):
        ax.plot(self.prediction, label="prediction") 
        ax.plot(self.df, label="data", linestyle = 'dotted')
        ax.axvline(x=self.training_data.index.max(), color='red', linestyle='--', label='Training Split')  
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network traffic prediction script")
    parser.add_argument('--csv', type=str, default = "../data/last.csv", help="csv file to use as input")
    parser.add_argument('--png', type=str, default="../data/output.png", help="png file to store the plot")
    parser.add_argument('--training-split', type=float, default=.8, help="Percentage of data used for training")
    parser.add_argument('--sample-period', type=str, default="0.2S", help="Preiod over which to combine network data")
    
    args = parser.parse_args()
    
        
    #if not os.path.exists(args.store_plot):    #create folder for plots
    #    os.mkdir(args.store_plot)
    
    # calculate square to best fit all interfaces
    num_cols = 1 
    num_rows = 1
        
    fig, axs = plt.subplots(num_rows, num_cols, sharey=True, sharex=False, figsize=(12, 8))
        
    prediction = TrafficPrediction()
            
    # full_path = "../data/last.csv"
    full_path = args.csv
            
    print(f"Reading file {full_path}")
    prediction.read_from_csv(full_path, args.sample_period)
            
    print("Running ARIMA prediction...")
    prediction.run_arima(order=(30,0,0), training_split=args.training_split)
            
    prediction.plot(axs)
    axs.set_title(full_path[:-4]) # remove ".csv" from the plot name

    #fig.legend(axs.get_legend_handles_labels(),fancybox=True)
    #fig.suptitle(switch, fontsize=29)
        
    plt.tight_layout(pad=0.5)
    output_name = args.png
    plt.savefig(output_name)
    # plt.show()
