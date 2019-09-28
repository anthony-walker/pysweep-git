#Programmer: Anthony Walker
#This is the main file for running and testing the swept solver
#Create arguments here for the solver and call them with pst.py
import os
import sys
import numpy as np
from notipy import NotiPy
cwd = os.getcwd()
sys.path.insert(1,cwd+"/src")
from sweep import *

class controller(object):
    def __init__(self):
        """Use this to create class that will execute all the appropriate cases."""
        self.np = 16
        self.ssm = "mpiexec -n "+str(self.np)+" python ~/pysweep/src/pst.py "
        self.swept = "swept_vortex"
        self.decomp = "standard_vortex"
        self.asize = int(3*4*8)
        self.affs = (1,)#np.arange(0.5,1.01,0.1)
        self.runs = list()
        self.block_sizes()
        self.sizes()
        self.mpi_arg_parse(self.swept)
        self.mpi_arg_parse(self.decomp)

    def __call__(self,args):
        """Use this to execute the cases"""
        for run in self.runs:
            print(run)
            try:
                os.system(run)
            except:
                pass

    def block_sizes(self):
        """Use this function to create blocksizes"""
        self.blocks = list()
        for i in range(8,33,2):
            if self.asize%i==0:
                self.blocks.append(i)

    def sizes(self):
        """Use this function to create a list of array sizes"""
        self.sizes = [self.asize]
        for i in range(2,6,1):
            self.sizes.append(i*self.asize)

    def mpi_arg_parse(self,mode):
        """Use this function to create runs list"""

        for i, affinity in enumerate(self.affs):
            for j, block in enumerate(self.blocks):
                for k, size in enumerate(self.sizes):
                    dx = 20/size
                    dt = dx/10
                    tf = dt*500
                    sstr = self.ssm + mode
                    sstr += " -nx "+str(size)+" -ny "+str(size)
                    sstr += " -X "+str(int(size/10))+" -Y "+str(int(size/10))
                    sstr += " -b " +str(block)+" -a "+str(affinity)
                    sstr += " --hdf5 ./results/"+mode+str(i)+str(j)+str(k)+" "
                    sstr += " -dt "+str(dt)+" -tf "+str(tf)
                    self.runs.append(sstr)

if __name__ == "__main__":
    # exe_cont = controller()
    # sm = "Hi,\nYour function run is complete.\n"
    # notifier = NotiPy(exe_cont,tuple(),sm,"asw42695@gmail.com",timeout=None)
    # notifier.run()
    nx = ny = 512
    bs = 8
    t0 = 0
    tf = 1
    dt = 0.1
    dx = dy = 0.1
    gamma = 1.4
    arr = np.ones((4,nx,ny))
    X = 1
    Y = 1
    tso = 2
    ops = 2
    aff = 0.5    #Dimensions and steps
    dx = X/nx
    dy = Y/ny
    #Changing arguments
    gargs = (t0,tf,dt,dx,dy,gamma)
    swargs = (tso,ops,bs,aff,"./src/equations/euler.h","./src/equations/euler.py")
    dsweep(arr,gargs,swargs,filename="test")
