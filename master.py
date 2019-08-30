#Programmer: Anthony Walker
#This is the main file for running and testing the swept solver
from src.sweep.sweep import *
from src.analytical import *
from src.equations import *
from src.decomp import *
import multiprocessing as mp
from notipy.notipy import NotiPy

#MPI Info
comm = MPI.COMM_WORLD
master_rank = 0 #master rank
rank = comm.Get_rank()  #current rank


#Calling analytical solution
def analytical():
    """Use this funciton to solve the analytical euler vortex."""
    # create_vortex_data(cvics,X,Y,npx,npy,times=(0,0.1))
    pass

def create_block_sizes():
    """Use this function to create arguements for the two codes."""
    #Block_sizes
    bss = list()
    for i in range(3,6,1):
        cbs = (int(2**i),int(2**i),1)
        bss.append(cbs)
    return bss

def test(args):
    #Properties
    gamma = 1.4

    #Analytical properties
    cvics = vics()
    cvics.Shu(gamma)
    initial_args = cvics.get_args()
    X = cvics.L
    Y = cvics.L
    getDeviceAttrs(0,False)
    #Dimensions and steps
    opt_grid_size = int(4*5*6*7)
    npx = 16
    npy = 16
    dx = X/npx
    dy = Y/npy

    #Time testing arguments
    t0 = 0
    t_b = 1
    dt = 0.1
    targs = (t0,t_b,dt)

    # Creating initial vortex from analytical code
    initial_vortex = vortex(cvics,X,Y,npx,npy,times=(0,))
    flux_vortex = convert_to_flux(initial_vortex,gamma)[0]
    tarr = np.ones(flux_vortex.shape)
    #GPU Arguments
    gpu_source = "/home/walkanth/pysweep/src/equations/eqt.h"
    cpu_source = "/home/walkanth/pysweep/src/equations/eqt.py"
    ops = 2 #number of atomic operations
    tso = 2 #RK2
    #File args
    swept_name = "./results/swept"
    decomp_name = "./results/decomp"
    #Changing arguments
    affinities = np.linspace(1/2,1,mp.cpu_count()/2)
    block_sizes = create_block_sizes()
    block_size = 8
    affinity = 0.5
    if rank == master_rank:
        f =  open("./results/time_data.txt",'w')
    gargs = (t0,t_b,dt,dx,dy,gamma)
    swargs = (tso,ops,block_size,affinity,gpu_source,cpu_source)

    # #Swept results
    # for i,bs in enumerate(block_sizes):
    #     for j,aff in enumerate(affinities):
    #         fname = swept_name+"_"+str(i)+"_"+str(j)
    #         ct = sweep(initial_vortex,targs,dx,dy,ops,bs,gpu_source,cpu_source,affinity=aff,filename=fname)
    #         if rank == master_rank:
    #             f.write("Swept: "+str((ct,bs,aff))+"\n")
            # comm.Barrier()

    # for i,bs in enumerate(block_sizes[:1]):
    #     for j,aff in enumerate(affinities):
    #         fname = decomp_name+"_"+str(i)+"_"+str(j)
    #         ct = decomp(initial_vortex,targs,dx,dy,ops,bs,gpu_source,cpu_source,affinity=aff,filename=fname)
    #         if rank == master_rank:
    #             f.write("Decom: "+str((ct,bs,aff))+"\n")
    #         comm.Barrier()
    #For testing individual sweep
    cts = sweep(tarr,gargs,swargs,filename="./results/swept")
    ct = decomp(flux_vortex,gargs,swargs,filename="./results/decomp")
    return cts,ct

if __name__ == "__main__":
    args = tuple()
    sm = "Hi,\nYour function run is complete.\n"
    notifier = NotiPy(test,args,sm,"asw42695@gmail.com",rank=rank,timeout=None)
    notifier.run()
    # test(args)
