import numpy as np
import scipy.constants as cst
import at
import matplotlib.pyplot as plt

class Kicker:
    def __init__(self, xpos, ypos, currents):
        self.xpos = xpos
        self.ypos = ypos
        self.currents = currents
       
    def get_field(self, x, y):
        by = 0.0
        bx = 0.0
        f = -cst.mu_0/(2*np.pi)
        for xc, yc, c in zip(self.xpos, self.ypos, self.currents):
            r2 = (x-xc)**2+(y-yc)**2
            by += f*c*(x-xc)/r2
            bx += f*c*(y-yc)/r2
        return bx, by
       
    def get_dfield(self, x, y):
        dby = 0.0
        dbx = 0.0
        f = -cst.mu_0/(2*np.pi)
        for xc, yc, c in zip(self.xpos, self.ypos, self.currents):
            r2 = (x-xc)**2+(y-yc)**2
            a = (y-yc)**2-(x-xc)**2
            b = 2*(x-xc)*(y-yc)
            dby += f*c*a/r2**2
            dbx += f*c*b/r2**2
        return dbx, dby
       
    def get_kick(self, x, y, brho, l):
        bx, by = self.get_field(x, y)
        return bx/brho*l, by/brho*l
       
    def get_dkick(self, x, y, brho, l):
        dbx, dby = self.get_dfield(x, y)
        return dbx/brho*l, dby/brho*l
   
    def get_polynoms(self, radius, npoints, norder):
        x = np.linspace(-radius, radius, npoints)
        zeros = np.zeros(npoints)
        _, byn = self.get_field(x, zeros)
        pn = np.polyfit(x, byn, norder)
        return np.flip(pn)
   
    def gen_at_elem(self, name, length, pn):
        pn *= -1.0
        if length == 0:
            return at.ThinMultipole(name, np.zeros(len(pn)), pn)
        else:
            return at.Multipole(name, length, np.zeros(len(pn)), pn)
       
    def plot_kick(self, x, brho, length, show=True):
        bx = np.zeros(len(x))
        by = np.zeros(len(x))
        dbx = np.zeros(len(x))
        dby = np.zeros(len(x))    
            
        for i, xi in enumerate(x):
            bx[i], by[i] = self.get_kick(xi, 0, brho, length)
            dbx[i], dby[i] = self.get_dkick(xi, 0, brho, length)
            
            
        fig, ax = plt.subplots()
        l0 = ax.plot(self.xpos, self.ypos, '.k', label='Coils')    
        l1 = ax.plot(x, by, 'r', label='Deflection')
        ax.set_ylabel(r'$\theta$ [rad], y[m]')
        ax.set_xlabel('x [m]')
        r = max(np.concatenate((abs(self.ypos), abs(by))))*1.1
        ax.set_ylim([-r, r])
        ax2 = ax.twinx()
        l2 = ax2.plot(x, dby, 'b', label='Gradient')
        ax2.hlines(0.0, x[0], x[-1], color='k', linestyle='dashed')
        ax2.set_ylabel(r'$k_1 L$')
        r = max(abs(dby))*1.1
        ax2.set_ylim([-r, r]) 
        ls = l0 + l1 + l2
        labs = [l.get_label() for l in ls]
        ax.legend(ls, labs, loc=0)
        fig.tight_layout()
        if show:
            plt.show()