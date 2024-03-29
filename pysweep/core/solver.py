import sys, os, yaml, numpy, warnings, time, h5py, importlib.util
import GPUtil
import pysweep.core.io as io
import pysweep.core.process as process
import pysweep.core.functions as functions
import pysweep.core.block as block
from itertools import cycle

class Solver(object):
    """docstring for Solver."""
    def __init__(self, initialConditions=None, yamlFileName=None,sendWarning=True):
        super(Solver, self).__init__()
        self.moments = [time.time(),]
        process.setupCommunicators(self) #This function creates necessary variables for MPI to use
        self.assignInitialConditions(initialConditions,sendWarning=sendWarning)

        if yamlFileName is not None:
            self.yamlFileName = yamlFileName
            #Managing inputs
            io.yamlManager(self)
        else:
            if sendWarning:
                warnings.warn('yaml not specified, requires manual input.')

    def __call__(self,start=0,stop=-1,libname=None,recompile=False):
        """Use this function to spawn processes."""
        #Grabbing start of call time
        self.moments.append(time.time())
        io.verbosePrint(self,"-----------------------------PySweep-------------------------\n")
        #set up MPI
        io.verbosePrint(self,"Setting up processes...\n")
        process.setupProcesses(self)
        self.moments.append(time.time())
        
        #Creating time step data
        io.verbosePrint(self,'Creating time step data...\n')
        self.createTimeStepData()
        self.moments.append(time.time())

        # #Creating simulatneous input and output file
        # io.verbosePrint(self,'Creating output file...\n')
        # io.createOutputFile(self)
        # self.moments.append(time.time())
        
        # Creating shared array
        io.verbosePrint(self,'Creating shared memory arrays and process functions...\n')
        if self.simulation:
            block.sweptBlock(self)
        else:
            block.standardBlock(self)
        self.moments.append(time.time())
        
        #Cleaning up unneeded variables
        io.verbosePrint(self,'Cleaning up solver...\n')
        self.solverCleanUp()
        self.moments.append(time.time())

        #Running simulation
        io.verbosePrint(self,'Running simulation...')
        io.verbosePrint(self,io.getSolverPrint(self))
        if self.simulation:
            self.sweptSolve()
        else:
            self.standardSolve()
        self.moments.append(time.time())
        #Process cleanup
        io.verbosePrint(self,'Cleaning up processes...\n')
        process.cleanupProcesses(self,self.moments[start],self.moments[stop])
        io.verbosePrint(self,'Done in {} seconds...\n'.format(self.moments[-1]-self.moments[0]))
        io.verbosePrint(self,"---------------------------------------------------------------\n")
        
    def __str__(self):
        """Use this function to print the object."""
        return io.getSolverPrint(self)

    def compactPrint(self):
        """Use this function to print a compact version of the simulation details."""
        shortPrint = "swept: " if self.simulation else "standard: "
        moment = self.moments[-1] - self.moments[0] if self.moments else None
        shortPrint += "{}, {}, {}, {}, {}, {}".format(self.blocksize[0],self.share,self.intermediate,self.operating,self.timeSteps, moment)
        print(shortPrint)

    def loadCPUModule(self):
        """Use this function to set the cpu module externally."""
        spec = importlib.util.spec_from_file_location("module.step", self.cpu)
        self.cpu  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.cpu)    

    def assignInitialConditions(self,initialConditions,sendWarning=True):
        """Use this function to optionally assign initial conditions as an hdf5 file, array, or throw warning."""
        if type(initialConditions) == str:
            hf =  h5py.File(initialConditions,"r", driver='mpio', comm=self.comm)
            self.initialConditions = hf.get('data')
            self.arrayShape = hf.get('data').shape
            self.hf = hf
        elif initialConditions is not None:
            self.initialConditions = initialConditions
            self.arrayShape = numpy.shape(initialConditions)
        else:
            if sendWarning:
                warnings.warn('Initial condition not provided, requires manual assignment with assignInitialConditionsFunction.')

    def setGPU(self,gpu):
        """Use this function to set GPU variable."""
        self.gpu = gpu
        self.gpuStr = gpu

    def setCPU(self,cpu):
        """Use this function to set CPU variable."""
        self.cpu = cpu
        self.cpuStr = cpu

    def createTimeStepData(self):
        """Use this function to create timestep data."""
        self.timeSteps = int((self.globals[1]-self.globals[0])/self.globals[2])  #Number of time steps
        if self.simulation:
            self.splitx = self.blocksize[0]//2
            self.splity = self.blocksize[1]//2
            self.maxPyramidSize = self.blocksize[0]//(2*self.operating)-1 #This will need to be adjusted for differing x and y block lengths
            self.maxGlobalSweptStep = int(self.intermediate*self.timeSteps/self.maxPyramidSize-1) #minus 1 because the last pyramid will be outside this loop
            self.timeSteps = int(self.maxPyramidSize*(self.maxGlobalSweptStep+1)/self.intermediate+1) #Plus 1 for initial conditions
            self.maxOctSize = 2*self.maxPyramidSize
            self.subtraction = 1 if self.maxPyramidSize%2!=0 and self.intermediate%2==0 else 0 
            self.sharedShape = (self.maxOctSize+self.intermediate,)+self.sharedShape
            self.arrayShape = (self.timeSteps,)+self.arrayShape
        else:
            self.sharedShape = (self.intermediate+1,)+self.sharedShape
            self.arrayShape = (self.timeSteps+1,)+self.arrayShape

    def solverCleanUp(self):
        """Use this function to remove unvariables not needed for computation."""
        #Try to delete unnecessary left over variables
        try:
            del self.gpuRank
            del self.initialConditions
            del self.yamlFileName
            del self.yamlFile
        except Exception as e:
            pass
        #Close ICS if it is a file.
        try:
            self.hf.close()
        except Exception as e:
            pass

    def debugSimulations(self,arr=None):
        """Use this function to help debug"""
        if self.clusterMasterBool: 
            ci = 0
            while ci != -1:
                if arr is None:
                    print(self.sharedArray[ci,0,:,:])
                else:
                    print(arr[ci,0,:,:])
                ci = int(input())
        self.comm.Barrier()

    def sweptSolve(self):
        """Use this function to begin the simulation."""
        # -------------------------------SWEPT RULE---------------------------------------------#
        #setting global time step to zero
        self.globalTimeStep=1 #Has to be int32 for GPU
        # -------------------------------FIRST PRISM AND COMMUNICATION-------------------------------------------#
        functions.FirstPrism(self)
        functions.firstForward(self)
        #Loop variables
        cwt = 1 #Current write time
        del self.Up #Deleting Up object after FirstPrism
        #-------------------------------SWEPT LOOP--------------------------------------------#
        step = cycle([functions.sendBackward,functions.sendForward])
        for i in range(self.maxGlobalSweptStep):
            functions.UpPrism(self)
            cwt = next(step)(cwt,self)
        #Do LastPrism Here then Write all of the remaining data
        functions.LastPrism(self)
        next(step)(cwt,self)

    def standardSolve(self):
        # -------------------------------Standard Decomposition---------------------------------------------#
        #setting global time step to zero
        self.globalTimeStep=1
        #Send Boundary points
        functions.sendEdges(self)
        cwt = 0 #Starts at zero compared too swept because of the write algorithm
        for i in range(self.intermediate*(self.timeSteps+1)):
            functions.StandardFunction(self)
            cwt = io.standardWrite(cwt,self)
            #Communicate
            functions.sendEdges(self)
