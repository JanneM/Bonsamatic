#!/usr/bin/python
import numpy as np
from pylab import *
from scipy.optimize import curve_fit
#for the dial drawing
import svgwrite as sw

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
    return exp(m*array(deg)+c)

def Dlog(v, m, c):
    return (log(array(v))-c)/m

# linear estimation:

# assume line from (V0,0)->(V(20), 20)

clin = 0.0
mlin = (Vlog(20,mlog,clog)-0)/(20.-0)

#mlin = 0.048691078541901502

vpar = [mlog, clog, mlin]

def Vlin(deg,m):
    return m*deg

def Dlin(v,m):
    return v/float(m)

def deg_volt(deg,ml,cl,m):
    
    if not iterable(deg):
	deg=[deg]
    res=[]
    for d in deg:
	
	if d>20.0:
	    res.append(Vlog(d,ml,cl))
	else:
	    res.append(Vlin(d,m))
    return array(res)

def volt_deg(vlt,ml,cl,m):
    
    if not iterable(vlt): 
	vlt=[vlt]
    res=[]
    for v in vlt:
	if Dlin(v,m)>20.0:
	    res.append(Dlog(v,ml,cl))
	else:
	    res.append(Dlin(v,m))
    return res


print "mlog, clog, mlin: ", mlog, clog, mlin
# 73.44 or about 73 deg
print "max angle:", volt_deg(5.0, mlog,clog,mlin)


#plot(D,V,'-.', d, exp(0.03061*d-0.6387), D[0:5], 0.04869*D[0:5])
#show()

# create nice log-like scale distribution
# 
# General function forms

def tf(t,a,b,c):
    return a+b*log(t+c)

# Fit through the following points:

tp=array([0.0, 48.0, 240])
degp=array([0.0, 37.5, 73.44])	# the not-quite max angle above

# will return a warning for singular value in tf
tpar, rest = curve_fit(tf,tp,degp)

# tpar = [a, b, c]

# a = -66.347194822630726
# b = 25.165693379835989
# c = 13.963046955699566

print tpar
def t_deg(t,a,b,c):
    deg = a+b*log(t+c)
    return deg

def deg_t(deg,a,b,c):
    t = exp((deg-a)/b)-c
    return t

# We've got 8 bits worth of voltage division. calc tables mapping these
# voltage indexes to angle, index to time and back.

# also decide on divisions for the time setting. for each time, choose the
# closest index.

# when running, given a particular index, the current time, and the time to
# end, how long should we wait to tick down to the next index?

# for each index, hold the accumulated time left when you reach the next in
# line. So, index #1 will have 0, #2 will have time between #0 and #1 and so
# on.

# setting times
times = [6,12,18, 24,36, 48,60, 72, 96, 120, 144, 168, 192, 216, 240]
tvolts = arange(256)*5./255.


def find_nearest(arr,val):
    if not iterable(val): 
	val=[val]
    res=[]
    for v in val:
	res.append((abs(arr-v)).argmin())
    
    return array(res)


# volts to degrees to times:

vd = volt_deg(tvolts, *vpar)
vt = deg_t(vd, *tpar)

# cumlative time to goal in seconds. secdiff[n] tells us how many seconds to wait to reach
# n from n+1.
tleft=np.round(vt*60*60).astype(int)

#secdiff=diff(secs)

# desired 
stimes = array(times)*60*60

nearest = find_nearest(tleft, stimes)

for t,n,h in zip(stimes,nearest, times):
    print "{{{0}, {1}}},\t // {2} hours".format(t,n,h)


# Plot the resulting display.
#
# We make it for 51.5x31.5mm screen. The needle center is 35mm from the upper
# edge, with 7.5 mm circular clearance needed.

def to_mm(xy):
    return ("{0}mm".format(xy[0]), "{0}mm".format(xy[1]))

# Assume 0 deg is east, going counterclockwise. Before conversion, multiply by dir and
# add adj. 
def rt_xy(r, theta, center=(0,0), adj=0.0, adir=1, ydir=1):
    thadj = (theta*pi/180.0)*adir+(adj*pi/180.0)
    return to_mm((center[0]+r*cos(thadj),center[1]+ydir*r*sin(thadj)))


cx = 51.5/2.0
cy = 35.0
dout = 26.0	    #outside diameter
din_l = dout-10.0   # inside for major ticks
din_s = dout-7.0    # ditto minor ticks

#angles. May need manual adjustment

amin = volt_deg(tvolts[0], *vpar)[0]
amax = volt_deg(tvolts[-1], *vpar)[0]
ac = (amax-amin)/2.0

ppar=[(cx, cy), 90.0+ac, -1, -1]

dial = sw.Drawing('dial.svg', size=(u'51.5mm',u'35mm'), profile="tiny")

dial.add(dial.rect(("0%","0%"), ("100%","100%"), stroke="grey",
fill="none"))
dial.add(dial.line(to_mm((0,31.5)), to_mm((51.5,31.5)), stroke="grey"))
# angles for the explicit steps
st_ang = volt_deg(tvolts[nearest], *vpar)

dial.add(dial.line(rt_xy(10, 0,*ppar), rt_xy(dout,0,*ppar),
    stroke=sw.rgb(0,0,0)))

for a in st_ang:
    dial.add(dial.line(rt_xy(din_l, a, *ppar),rt_xy(dout,a, *ppar), stroke=sw.rgb(0,0,0)))

dial.save()

