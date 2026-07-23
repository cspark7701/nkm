import os
os.environ["PYTHONPATH"] = "/home/cspark/Work/simulation_codes-working/radia/env/radia_python" #:" + os.environ.get("PYTHONPATH", "")

import sys
sys.path.append(os.environ["PYTHONPATH"])

import radia as rd
import numpy as np
import matplotlib.pyplot as plt
from uti_plot import *
from jupyter_rs_radia import radia_viewer

print("Radia Version is", rd.UtiVer())

rd.UtiDelAll()

#*********************************Build the Geometry
def BuildGeometry():

    #Current Densities in A/mm^2
    Imax = -3000

    #Coil Presentation Parameters
    n1 = 3; n2 = 6; c2 = [1,0,0]; c1 = [0,1,1]; thcn = 0.001

    #Define parameters
    x1 = 5.3; y1 = 5.3; x2 = 10.250; y2 = 10.250; z1 = 262.5
    print ("x1 =", x1, ", x2 =", x2, ", y1 =", y1, ", y2 =", y2, ", z1 =", z1)

    p1 = [x1, z1, y1]; p2 = [x2, z1, y2]; p3 = [x2, -z1, y2]; p4 = [x1, -z1, y1]
    
    #Create a Coil
    Rt6 = rd.ObjFlmCur([p1, p2, p3, p4, p1], Imax)
    rd.ObjDrwAtr(Rt6, c2, thcn)
    Grp = rd.ObjCnt(Rt6)
    
    #Rt1 = rad.ObjRaceTrk([0.,0.,38.], [9.5,24.5], [120.,0.], 36, n1, j1)
    #rad.ObjDrwAtr(Rt1, c1, thcn)
    #Rt3 = rad.ObjRaceTrk([0.,0.,76.], [10.,25.], [90.,0.], 24, n1, j1)
    #rad.ObjDrwAtr(Rt3, c1, thcn)
    #Rt2 = rad.ObjRaceTrk([0.,0.,38.], [24.5,55.5], [120.,0.], 36, n1, j2)
    #rad.ObjDrwAtr(Rt2, c2, thcn)
    #Rt4 = rad.ObjRaceTrk([0.,0.,76.], [25.,55.], [90.,0.], 24, n1, j2)
    #rad.ObjDrwAtr(Rt4, c2, thcn)
    #Rt5 = rad.ObjRaceTrk([0.,0.,60.], [150.,166.3], [0.,0.], 39, n2, -j2)
    #rad.ObjDrwAtr(Rt5, c2, thcn)

    #Grp = rad.ObjCnt([Rt1, Rt2, Rt3, Rt4, Rt5])

    #Define Mirror Coils
    rd.TrfZerPara(Grp, [0, 0, 0], [0, 0, 1])
    rd.TrfZerPara(Grp, [0, 0, 0], [1, 0, 0])
    
    #rad.TrfZerPara(Grp, [0,0,0], [0,0,1])

    return Grp

#*********************************Calculate Magnetic Field and Field Integrals
def CalcField(g):

    #Vertical Magnetic Field vs Longitudinal Position
    yMin = 0.; yMax = 300.; ny = 301
    yStep = (yMax - yMin)/(ny - 1)
    xc = 0.; zc = 0.
    #y = yMin
    #Points = []
    #for i in range(ny):
    #    Points.append([xc,y,zc])
    #    y += yStep
    #BzVsY = rad.Fld(g, 'bz', Points)
    #More compact method to do the above: 
    BzVsY = rd.Fld(g, 'bz', [[xc,yMin+iy*yStep,zc] for iy in range(ny)])

    #Vertical Magnetic Field Integral (along Longitudinal Position) vs Horizontal Position
    xMin = 0.; xMax = 400.; nx = 201
    xStep = (xMax - xMin)/(nx - 1)
    zc = 0.
    #x = xMin
    #IBzVsX = []
    #for i in range(ny):
    #    IBzVsX.append(rad.FldInt(g, 'inf', 'ibz', [x,-300.,zc], [x,300.,zc]))
    #    x += xStep
    #More compact method to do the above: 
    IBzVsX = [rd.FldInt(g, 'inf', 'ibz', [xMin+ix*xStep,-300.,zc], [xMin+ix*xStep,300.,zc]) for ix in range(nx)]

    return BzVsY, [yMin, yMax, ny], IBzVsX, [xMin, xMax, nx]

#Build the Geometry
nkm = BuildGeometry()
print('NKM Geometry Index:', nkm)

#Calculate Magnetic Field
BzVsY, MeshY, IBzVsX, MeshX = CalcField(nkm)

print('Field in Center:', BzVsY[0], 'T')
print('Field Integral in Center:', IBzVsX[0], 'T.mm')

#Plot the Results
uti_plot1d(BzVsY, MeshY, ['Longitudinal Position [mm]', 'Bz [T]', 'Vertical Magnetic Field'])
uti_plot1d(IBzVsX, MeshX, ['Horizontal Position [mm]', 'Integral of Bz [T.mm]', 'Vertical Magnetic Field Integral'])
uti_plot_show() #show all graphs (and block further execution, if any)

