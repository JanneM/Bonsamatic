#!/usr/bin/python
from pylab import *
from scipy.optimize import curve_fit

# initial estimated Voltage/degree relationship, 10k resistor

V=array([0, 0.28, 0.55, 0.76, 0.96, 1.15, 1.34,1.54, 1.78,2.11,2.45,2.81,3.25,3.85,4.57,5.26])
D=linspace(0,75,16)

# two phases: 0-20 deg linear; 20-75 deg logarithmic
# log estimation:

d=D[4:]
lv=log(V[4:])

x=vstack([d, ones(len(d))]).T
mlog,clog=lstsq(x, lv)[0]

# alternative:
#def flog(x,m,c):
#    return exp(m*x+c)
#logpars, rest = curve_fit(flog,d,v)
# mlog = logpars[0]
# clog = logpars[1]

# mlog = 0.030608073895719921
# clog = -0.63868866219381337

def Vlog(deg, m, c):
    return exp(m*deg+c)

def Dlog(v, m, c):
    return (log(v)-c)/m

# linear estimation:

# assume line from (V0,0)->(V(20), 20)

clin = 0.0
mlin = (Vlog(20,mlog,clog)-0)/(20.-0)

#mlin = 0.048691078541901502

def Vlin(deg,m):
    return m*deg

def Dlin(v,m):
    return v/float(m)

def deg_volt(deg,ml,cl,m):
    if deg>20.0:
	return Vlog(deg,ml,cl)
    else:
	return Vlin(deg,m)

def volt_deg(v,ml,cl,m):
    if Dlin(v,m)>20.0:
	return Dlog(v,ml,cl)
    else:
	return Dlin(v,m)

print "mlog, clog, mlin: ", mlog, clog, mlin
# 73.44 or about 73 deg
print "max angle:", volt_deg(5.0, mlog,clog,mlin)


plot(D,V,'-.', d, exp(0.03061*d-0.6387), D[0:5], 0.04869*D[0:5])
show()

# create nice log-like scale distribution
# 
# General function forms

def tf(t,a,b,c):
    return a+b*log(t+c)

# Fit through the following points:

tp=array([0.0, 48.0, 240])
degp=array([0.0, 37.5, 73.44])	# the not-quite max angle above

# will return a warning for singular value in tf
par, rest = curve_fit(tf,tp,degp)

#par = [a, b, c]
a,b,c = par

# a = -66.347194822630726
# b = 25.165693379835989
# c = 13.963046955699566

print a,b,c
def t_deg(t,a,b,c):
    deg = a+b*log(t+c)
    return deg

def deg_t(deg,a,b,c):
    t = exp((deg-a)/b)-c
    return t


