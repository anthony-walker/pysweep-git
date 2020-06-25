
import pysweep,numpy,sys,os,h5py

path = os.path.dirname(os.path.abspath(__file__))

def testExample(share=0.5,npx=24,npy=24):
    # filename = pysweep.equations.example.createInitialConditions(1,npx,npy)
    yfile = os.path.join(path,"inputs")
    yfile = os.path.join(yfile,"example.yaml")
    testSolver = pysweep.Solver("exampleConditions.hdf5",yfile)
    testSolver.share = share
    testSolver()

    # if testSolver.clusterMasterBool:
    #     with h5py.File(testSolver.output,"r") as f:
    #         data = f["data"]
    #         for i in range(testSolver.arrayShape[0]):
    #             print(data[i,0,:,:])
    #             input()

if __name__ == "__main__":
    pass
    # MPI.COMM_SELF.Spawn(sys.executable, args=["from pysweep.tests import testExample; testExample()"], maxprocs=2)
