import numpy, yaml, itertools, h5py, math
# import pysweep.utils.validate as validate
# import pysweep
import matplotlib 
if 0:
    matplotlib.rcParams.update({'text.color' : "white",
                     'axes.labelcolor' : "white","axes.edgecolor":"white","xtick.color":"white","ytick.color":"white","grid.color":"white","savefig.facecolor":"#333333","savefig.edgecolor":"#333333","axes.facecolor":"#333333"})
    for k in matplotlib.rcParams:
        if "color" in k:
            print(k)
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib import cm
from matplotlib import tri
from mpl_toolkits import mplot3d
from matplotlib.colors import Normalize

#Global data
standardSizes = numpy.asarray([160, 320, 480, 640, 800, 960, 1120])
blockSizes = numpy.asarray([8,12,16,20,24,32])
best = []
worst = []
shares = numpy.arange(0,1.1,0.1)
combos = []
cutoffs = [0,]

def printArray(a):
    for row in a:
        for item in row:
            print("{:8.3f}".format(col), end=" ")
        print("")

def calcNumberOfPts():
    npts = 0
    global combos, cutoffs
    for ss in standardSizes:
        for bs in blockSizes:
            nblks = numpy.ceil(ss/bs)
            shareset = set()
            for sh in shares:
                numerator = float('%.5f'%(sh*nblks))
                tempShare = numpy.ceil(numerator)/nblks
                # print(tempShare,nblks,sh*nblks)
                # input()
                shareset.add(tempShare)
            shareset = list(shareset)
            shareset.sort()
            for sh in shareset:
                combos.append([ss,bs,sh])
            npts+=len(shareset)
        cutoffs.append(npts)
    return npts

# print(shares.shape,blockSizes.shape,standardSizes.shape)

def validateHeat():
    #Plotting
    elev=45
    azim=25
    fig =  plt.figure()
    nrows = 2
    ncols = 3
    axes = [fig.add_subplot(nrows, ncols, i+1) for i in range(nrows*ncols)]
    fig.subplots_adjust(wspace=0.75,hspace=0.8,right=0.8)
    #Physical Colorbar
    cbounds=numpy.linspace(0.4,1,6)
    # cbar_ax = fig.add_axes([0.89, 0.39, 0.05, 0.51]) #left bottom width height
    cbar_ax = fig.add_axes([0.89, 0.11, 0.05, 0.76]) #left bottom width height
    ibounds = numpy.linspace(cbounds[0],cbounds[-1],100)
    cbar = fig.colorbar(cm.ScalarMappable(cmap=cm.inferno),cax=cbar_ax,boundaries=ibounds)
    cbar.ax.set_yticklabels([["{:0.1f}".format(i) for i in cbounds]])
    tick_locator = ticker.MaxNLocator(nbins=len(cbounds))
    cbar.locator = tick_locator
    cbar.update_ticks()
    cbar_ax.set_title('$T(x,y,t)$',y=1.01)
    with h5py.File("./data/heatOutput.hdf5","r") as f:
        data = f['data']
        times = [0,] #Times to plot
        times.append(numpy.shape(data)[0]//2)
        times.append(numpy.shape(data)[0]-1)
        #Numerical stuff
        d = 0.1
        dx = 1/(numpy.shape(data)[2]-1)
        alpha = 1
        dt = float(d*dx**2/alpha)
        for i,ax in enumerate(axes[3:6]):
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.yaxis.labelpad=-1
            ax.set_title('N:$t={:0.2e}$'.format(times[i]*dt))
            validate.heatContourAx(ax,data[times[i],0],1,1)
        #Analytical
        npx = numpy.shape(data)[2]
        for i,ax in enumerate(axes[:3]):
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.yaxis.labelpad=-1
            ax.set_title('A:$t={:0.2e}$'.format(times[i]*dt))
            adata = numpy.zeros((1,1,npx,npx))
            adata[0,:,:,:],x,y = pysweep.equations.heat.analytical(npx,npx,t=(times[i])*dt,alpha=alpha)
            validate.heatContourAx(ax,adata[0,0],1,1)
    plt.savefig("./plots/heatValidate.pdf")
    plt.close('all')

def validateEuler(): 
    #Plotting
    elev=45
    azim=25
    fig =  plt.figure()
    nrows = 2
    ncols = 3
    axes = [fig.add_subplot(nrows, ncols, i+1) for i in range(nrows*ncols)]
    fig.subplots_adjust(wspace=0.75,hspace=0.8,right=0.8)
    #Physical Colorbar
    cbounds=numpy.linspace(0.4,1,6)
    # cbar_ax = fig.add_axes([0.89, 0.39, 0.05, 0.51]) #left bottom width height
    cbar_ax = fig.add_axes([0.89, 0.11, 0.05, 0.76]) #left bottom width height
    ibounds = numpy.linspace(cbounds[0],cbounds[-1],100)
    cbar = fig.colorbar(cm.ScalarMappable(cmap=cm.inferno),cax=cbar_ax,boundaries=ibounds)
    cbar.ax.set_yticklabels([["{:0.1f}".format(i) for i in cbounds]])
    tick_locator = ticker.MaxNLocator(nbins=len(cbounds))
    cbar.locator = tick_locator
    cbar.update_ticks()
    cbar_ax.set_title('$\\rho(x,y,t)$',y=1.01)
    with h5py.File("./data/eulerOutput.hdf5","r") as f:
        data = f['data']
        times = [0,] #Times to plot
        times.append(numpy.shape(data)[0]//2)
        times.append(numpy.shape(data)[0]-1)
        #Euler stuff
        d = 0.1
        gamma = 1.4
        dx = 10/(640-1)
        dt = d*dx
        #Numerical
        for i,ax in enumerate(axes[3:6]):
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.yaxis.labelpad=-1
            ax.set_title('N:$t={:0.2e}$'.format(times[i]*dt))
            validate.eulerContourAx(ax,data[times[i],0],1,1)
        #Analytical
        npx = numpy.shape(data)[2]
        for i,ax in enumerate(axes[:3]):
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.yaxis.labelpad=-1
            ax.set_title('A:$t={:0.2e}$'.format(times[i]*dt))
            adata = numpy.zeros((1,4,npx,npx))
            adata[0,:,:,:] = pysweep.equations.euler.getAnalyticalArray(npx,npx,t=(times[i])*dt)
            validate.eulerContourAx(ax,adata[0,0],1,1)
    plt.savefig("./plots/eulerValidate.pdf")
    plt.close('all')
        
def generateArraySizes():
    """Use this function to generate array sizes based on block sizes."""
    blocksizes = [8, 12, 16, 20, 24, 32] #blocksizes with most options
    arraystart = 0
    divisible =[False,False]
    arraysizes = []
    for i in range(7):
        arraystart += 32*20
        while not numpy.all(divisible):
            arraystart+=blocksizes[-1]
            divisible =[arraystart%bs==0 for bs in blocksizes]
        arraysizes.append(arraystart)
    return arraysizes

def getYamlData(file,equation):
    document = open(file,'r')
    yamlFile = yaml.load(document,Loader=yaml.FullLoader)
    data = []
    for key in yamlFile:
        if equation in yamlFile[key]['cpu']:
            swept = 1 if yamlFile[key]['swept'] else 0
            data.append([float(swept),float(yamlFile[key]['array_shape'][2]),float(yamlFile[key]['blocksize']),float(yamlFile[key]['share']),float(yamlFile[key]['runtime']),float(yamlFile[key]['time_per_step'])])
    i = 0
    while i < len(data):
        j = i+1
        while j < len(data):
            if data[i][:4] == data[j][:4]: 
                data.pop(j)
            j+=1
        i+=1

    data = numpy.array(data,)
    indexes = numpy.lexsort((data[:,3],data[:,2],data[:,1],data[:,0]))
    sortedData = numpy.zeros(data.shape)
    for i,idx in enumerate(indexes):
        sortedData[i,:] = data[idx,:] 
    return sortedData,standardSizes

def checkForAllPts(sortedData):
    ct = 0
    for j in range(len(sortedData)):

        if list(sortedData[j,1:4])!=combos[(j+ct)%452]:
            print("{:n}, {:n}, {:n}, {:.4f}".format(*sortedData[j,:4]))
            print("{:n}, {:n}, {:.4f}".format(*combos[(j+ct)%452]))
            ct+=1
            input()

def getContourData(data,arraysize,uBlocks,uShares):
    triang = tri.Triangulation(uBlocks, uShares)
    interpolator = tri.LinearTriInterpolator(triang, data)
    S,B = numpy.meshgrid(shares,blockSizes)
    Z = interpolator(B, S)
    return B,S,Z

def makeArrayContours(data,rBlocks,rShares,cbounds,cmap,cbt,fname,switch=False,printer=False,record=False):
    #Make speed up figure
    ai = lambda x: slice(int(data.shape[0]//len(standardSizes)*x),int(data.shape[0]//len(standardSizes)*(x+1)),1)
    fig, axes = plt.subplots(ncols=3,nrows=2)
    fig.subplots_adjust(wspace=0.55,hspace=0.4,right=0.75)
    axes = numpy.reshape(axes,(6,))
    cbar_ax = fig.add_axes([0.85, 0.11, 0.05, 0.77])
    ibounds = numpy.linspace(cbounds[0],cbounds[-1],100)
    cbar = fig.colorbar(cm.ScalarMappable(cmap=cmap),cax=cbar_ax,boundaries=ibounds)
    cbar.ax.set_yticklabels([["{:0.1f}".format(i) for i in cbounds]])
    tick_locator = ticker.MaxNLocator(nbins=len(cbounds))
    cbar.locator = tick_locator
    cbar.update_ticks()
    cbar_ax.set_title(cbt,y=1.01)

    if switch:
        mbc = ('k','w')
    else:
        mbc = ('w','k')
    for i in range(0,len(cutoffs)-2,1):
        lb = cutoffs[i+1]
        ub = cutoffs[i+2]
        xw= numpy.where(numpy.amax(data[lb:ub])==data[lb:ub])
        xb= numpy.where(numpy.amin(data[lb:ub])==data[lb:ub])
        #Contours
        axes[i].tricontour(rBlocks[lb:ub],rShares[lb:ub]*100,data[lb:ub],
                 colors=('k',),linestyles=('-',),linewidths=(0.25,),vmin=cbounds[0],vmax=cbounds[-1])
        axes[i].tricontourf(rBlocks[lb:ub],rShares[lb:ub]*100,data[lb:ub],cmap=cmap,vmin=cbounds[0],vmax=cbounds[-1])
        #Marking best and worst
        axes[i].plot(rBlocks[lb:ub][xb],rShares[lb:ub][xb]*100,linestyle=None,marker='o',markerfacecolor=mbc[0],markeredgecolor=mbc[1],markersize=6)
        axes[i].plot(rBlocks[lb:ub][xw],rShares[lb:ub][xw]*100,linestyle=None,marker='o',markerfacecolor=mbc[1],markeredgecolor=mbc[0],markersize=6)
        if record:
            worst.append((rBlocks[lb:ub][xb],rShares[lb:ub][xb]))
            best.append((rBlocks[lb:ub][xw],rShares[lb:ub][xw]))
        #Labels
        axes[i].set_title('Array Size: ${}$'.format(standardSizes[i+1]))
        axes[i].set_ylabel('Share [%]')
        axes[i].set_xlabel('Block Size')
        axes[i].grid(color='k', linewidth=1)
        axes[i].set_xticks([8,16,24,32])
        axes[i].set_yticks([0,25,50,75,100])
        axes[i].yaxis.labelpad = 0.5
        axes[i].xaxis.labelpad = 0.5
    plt.savefig(fname)
    plt.close('all')

def getContourYamlData(file,equation):
    data,standardSizes = getYamlData(file,equation)
    standarddata = data[:data.shape[0]//2,:]
    sweptdata = data[data.shape[0]//2:,:]
    speedup = standarddata[:,4]/sweptdata[:,4]
    return data,standarddata,sweptdata,standardSizes,speedup

def getDataLimits(data,npts=10):
    upperLimit = numpy.amax(data)
    lowerLimit = numpy.amin(data)
    upperLimit = math.ceil(upperLimit*10)/10
    lowerLimit = math.floor(lowerLimit*10)/10
    return numpy.linspace(lowerLimit,upperLimit,npts)
    

def getStudyContour(equation):
    #Get data
    newdata,newstandarddata,newsweptdata,newstandardSizes,newspeedup = getContourYamlData("./newHardware/log.yaml",equation)
    olddata,oldstandarddata,oldsweptdata,oldstandardSizes,oldspeedup = getContourYamlData("./oldHardware/log.yaml",equation)
    #Make contour
    #Speedup contours
    print("New Speed Up Average {}:{:0.2f}".format(equation,numpy.mean(newspeedup)))
    print("Old Speed Up Average {}:{:0.2f}".format(equation,numpy.mean(oldspeedup)))
    print("New Speed Up Min,Max {}:{:0.2f},{:0.2f}".format(equation,numpy.amin(newspeedup),numpy.amax(newspeedup)))
    print("Old Speed Up Min,Max {}:{:0.2f},{:0.2f}".format(equation,numpy.amin(oldspeedup),numpy.amax(oldspeedup)))
    speedLimits = getDataLimits([newspeedup,oldspeedup])
    makeArrayContours(oldspeedup,oldsweptdata[:,2],oldsweptdata[:,3],speedLimits,cm.inferno,'Speedup',"./plots/speedUp{}.pdf".format(equation+"Old"),switch=True,record=True)
    makeArrayContours(newspeedup,newsweptdata[:,2],newsweptdata[:,3],speedLimits,cm.inferno,'Speedup',"./plots/speedUp{}.pdf".format(equation+"New"),switch=True,record=True)
    #Time Contours
    timeLimits = getDataLimits([oldsweptdata[:,4],newsweptdata[:,4],oldstandarddata[:,4],newstandarddata[:,4]])
    makeArrayContours(oldsweptdata[:,4],oldsweptdata[:,2],oldsweptdata[:,3],timeLimits,cm.inferno_r,'Clocktime [s]',"./plots/clockTimeSwept{}.pdf".format(equation+"Old"))
    makeArrayContours(newsweptdata[:,4],newsweptdata[:,2],newsweptdata[:,3],timeLimits,cm.inferno_r,'Clocktime [s]',"./plots/clockTimeSwept{}.pdf".format(equation+"New"))
    makeArrayContours(oldstandarddata[:,4],oldstandarddata[:,2],oldstandarddata[:,3],timeLimits,cm.inferno_r,'Clocktime [s]',"./plots/clockTimeStandard{}.pdf".format(equation+"Old"))
    makeArrayContours(newstandarddata[:,4],newstandarddata[:,2],newstandarddata[:,3],timeLimits,cm.inferno_r,'Clocktime [s]',"./plots/clockTimeStandard{}.pdf".format(equation+"New"))

    #Time per timestep contours
    timePerStepLimits = getDataLimits([oldsweptdata[:,5],newsweptdata[:,5],oldstandarddata[:,5],newstandarddata[:,5]])
    makeArrayContours(oldsweptdata[:,5],oldsweptdata[:,2],oldsweptdata[:,3],timePerStepLimits,cm.inferno_r,'Time/Step [s]',"./plots/timePerStepSwept{}.pdf".format(equation+"Old"))
    makeArrayContours(newsweptdata[:,5],newsweptdata[:,2],newsweptdata[:,3],timePerStepLimits,cm.inferno_r,'Time/Step [s]',"./plots/timePerStepSwept{}.pdf".format(equation+"New"))
    makeArrayContours(oldstandarddata[:,5],oldstandarddata[:,2],oldstandarddata[:,3],timePerStepLimits,cm.inferno_r,'Time/Step [s]',"./plots/timePerStepStandard{}.pdf".format(equation+"Old"))
    makeArrayContours(newstandarddata[:,5],newstandarddata[:,2],newstandarddata[:,3],timePerStepLimits,cm.inferno_r,'Time/Step [s]',"./plots/timePerStepStandard{}.pdf".format(equation+"New"))

    #Hardware Speedup
    hardwareSpeedUp = oldsweptdata[:,5]/newsweptdata[:,5]
    print("Hardware Speed Up Average {}:{:0.2f}".format(equation,numpy.mean(hardwareSpeedUp)))
    print("Hardware Speed Up Min {}:{:0.2f}".format(equation,numpy.amin(hardwareSpeedUp)))
    print("Hardware Speed Up Max {}:{:0.2f}\n".format(equation,numpy.amax(hardwareSpeedUp)))
    speedLimits = getDataLimits([hardwareSpeedUp,])
    # if equation == "heat":
    #     speedLimits = numpy.linspace(1,2,11)
    makeArrayContours(hardwareSpeedUp,oldsweptdata[:,2],oldsweptdata[:,3],speedLimits,cm.inferno,'Speedup',"./plots/hardwareSpeedUp{}.pdf".format(equation),switch=True)
    
    # 3D plot
    ThreeDimPlot(oldsweptdata[:,2],100*oldsweptdata[:,3],oldspeedup,speedLimits)
    return oldsweptdata,newsweptdata


def ThreeDimPlot(x,y,z,lims):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_trisurf(x,y,z,cmap=cm.inferno)
    ax.set_xticks([8,16,24,32])
    ax.set_yticks([0,25,50,75,100])
    ax.set_zlim([lims[0],lims[-1]])
    ax.yaxis.labelpad = 0.5
    ax.xaxis.labelpad = 0.5  
    # plt.show()

def ScalabilityPlots():
    data,standardSizes = getYamlData("./scalability/scalability.yaml","euler")
    dl = len(data)
    eulersweptdata = data[dl//2:]
    eulerstandarddata = data[:dl//2]

    data,standardSizes = getYamlData("./scalability/scalability.yaml","heat")
    dl = len(data)
    heatsweptdata = data[dl//2:]
    heatstandarddata = data[:dl//2]

    fig, axes = plt.subplots(ncols=2,nrows=1)
    fig.subplots_adjust(wspace=0.55)
    #Euler
    ax=axes[0]
    ymax = numpy.ceil(numpy.amax([eulersweptdata,eulerstandarddata])+1000)
    ymin = numpy.floor(numpy.amin([eulersweptdata,eulerstandarddata]))
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim([0,ymax])
    ax.set_ylim([ymin,ymax])
    ax.set_ylabel("Clock time [s]")
    ax.set_xlabel("Array Size")
    ax.set_title("Compressible Euler Equations")
    # ax.set_title("Weak Scalability")
    l1 = ax.plot(eulersweptdata[:,1],eulersweptdata[:,4],marker="o",color='b')
    l2 = ax.plot(eulerstandarddata[:,1],eulerstandarddata[:,4],marker="o",color="r")
    leg = ax.legend(["Swept","Standard"])
    #Heat
    ax=axes[1]
    ymax = numpy.ceil(numpy.amax([heatsweptdata,heatstandarddata])+500)
    ymin = numpy.floor(numpy.amin([heatsweptdata,heatstandarddata])) 
    ax.set_ylabel("Clock time [s]")
    ax.set_xlabel("Array Size")
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim([0,ymax])
    ax.set_ylim([ymin,ymax])
    ax.set_title("Heat Diffusion Equation")
    # ax.set_title("Weak Scalability")
    l1 = ax.plot(heatsweptdata[:,1],heatsweptdata[:,4],marker="o",color='b')
    l2 = ax.plot(heatstandarddata[:,1],heatstandarddata[:,4],marker="o",color="r")
    leg = ax.legend(["Swept","Standard"])

    plt.savefig("./plots/weakScalability.pdf")
    plt.close('all')
    # plt.show()

def getOccurences(vals,targets):
    return [vals.count(i) for i in targets]

def modePlots():
    global best, worst
    best = [(i[0],round(j[0]*10,0)/10) for i, j in best]
    worst = [(i[0],round(j[0]*10,0)/10) for i, j in worst]
    bBlocks,bShares = zip(*best)
    wBlocks,wShares = zip(*worst)
    bestBlockOccurences = getOccurences(bBlocks,blockSizes) #[:len(bBlocks//2)]
    worstBlockOccurences = getOccurences(wBlocks,blockSizes)
    bestShareOccurences = getOccurences(bShares,shares)
    worstShareOccurences = getOccurences(wShares,shares)
    fig =  plt.figure()
    nrows = 1
    ncols = 2
    axes = [fig.add_subplot(nrows, ncols, i+1) for i in range(nrows*ncols)]
    fig.subplots_adjust(wspace=0.3)

    ax1,ax2 = axes

    ax1.set_ylabel("Occurences")
    ax1.set_xlabel("Block Size")
    ax1.plot(blockSizes,bestBlockOccurences,marker="o",color='b')
    ax1.plot(blockSizes,worstBlockOccurences,marker="o",color='r')
    leg = ax1.legend(["Best","Worst"])

    ax2.set_ylabel("Occurences")
    ax2.set_xlabel("Share")
    ax2.plot(shares,bestShareOccurences,marker="o",color='b')
    ax2.plot(shares,worstShareOccurences,marker="o",color='r')
    leg = ax2.legend(["Best","Worst"])
    plt.savefig("./plots/caseModes.pdf")



if __name__ == "__main__":
    calcNumberOfPts()
    
    # Produce contour plots
    sweptEuler = getStudyContour('heat')
    sweptEuler = getStudyContour('euler')
    print(cutoffs)
    # Scalability
    ScalabilityPlots()
    
    # #Produce physical plots
    # validateHeat()
    # validateEuler()
    #Other plots
    modePlots()