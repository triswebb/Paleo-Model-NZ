from numpy import *
import scipy as sp
from pandas import *
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
import pandas.rpy.common as com
import random
from rpy2 import robjects
import pandas as pd

# import output from single model run
paly_data = pd.read_csv('graphs/single_model_runs/model_run_no_dist_01_raw.csv')

# UPDATE CODE SO THIS LINE NOT NECCESSARY!
paly_data = paly_data.rename(columns = {'Unnamed: 0':'Depth'})


# extract pollen count and depth data from dataframe [row, col]
species = paly_data.iloc[:,1:6]
depth = paly_data['Depth']

# export variables into R
spec = com.convert_to_r_dataframe(species)
depth = robjects.IntVector(depth)

# import R device for producing graphics
grdevices = importr('grDevices')

# simple R function to produce pollen diagram
f = robjects.r('''
build_pollen_diagram<-function(depth, spec){
    library(rioja)
    library(plyr)
    par(mfrow = c(1, 1), oma=c(5,5,5,5))
    colnames(spec)[colnames(spec)=="Old.Forest"] <- "Old Forest"
    colnames(spec)[colnames(spec)=="Young.Forest"] <- "Young Forest"
    strat.plot(spec, yvar = depth, y.rev=TRUE, scale.percent=TRUE, ylabel="Depth (cm)",mplot.poly=TRUE, col.poly=000000, col.poly.line=0)
}''')

# get r function so it can be accessed in python
r_build_pollen_diagram = robjects.r['build_pollen_diagram']
# create png fil for output
grdevices.png(height=15, width=18, filename="great-barrier.png", res=300,units = "cm")
p_diagram = r_build_pollen_diagram(depth, spec)
grdevices.dev_off()



