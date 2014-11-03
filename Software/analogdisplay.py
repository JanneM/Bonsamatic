#!/usr/bin/python
#
# A script to figure out how to create a specific logarithmic scale on an
# analog voltage-controlled dial. It's more of an example than a finished
# application, as you may need to modify it to fit your hardware and desired
# scale.
#
# Copyright 2014 Jan Moren
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    import numpy as np 
    from pylab import * 
    from scipy.optimize import curve_fit
except:
    print("\nFATAL: can't find scipy. Aborting.\n")
    exit(-1)

# svgwrite is used for drawing the dial scale. It's not part of the standard
# python install. Either set "Draw_dial" to False below or install it. 
#
# install it with pip: sudo pip install svgwrite
# Or get svgwrite from here: https://pypi.python.org/pypi/svgwrite/1.1.6

Draw_dial = True

if Draw_dial:
    try:
        import svgwrite as sw
    except:
        print ("\nWARNING: could not import svgwrite.\n"+
        "Perhaps it's not installed? Proceeding without.\n")
        Draw_dial = False

# Initial measured voltage/degree relationship, 10k resistor. The voltages
# were measured at 5-degree intervals using a controllable power supply. It'd
# work fine to use the Arduino pwm output as well of course.

V = array([0, 0.28, 0.55, 0.76, 0.96, 1.15, 1.34, 1.54,
    1.78,2.11,2.45,2.81,3.25,3.85,4.57,5.26])

D = linspace(0,75,16)

### (1) Create estimate of the voltage-degree relationship for our dial.

# In this case we have two phases (estimated by eye, pretty much, in a graph
# like the one we plot below): 0-20 degrees is linear and 20-75 degrees is
# logarithmic. 
#
# I did try to fit a general 3 or 4-degree polynomial but this two-part
# estimation gave me better results. Your mileage will certainly vary
# depending on the dial you have.

# logarithmic estimation (using the least-squares estimation of scipy). Get
# the angles and the log of voltages beyond 20 degrees 

d = D[4:]
lv = log(V[4:])

# create a 2 by len(d) array with all ones in the second column
x = vstack([d, ones(len(d))]).T

# fit the (angle, log(voltage)) relationship
mlog,clog = lstsq(x, lv)[0]

# alternative way to do this with an explicit function:
#def flog(x,m,c):
#    return exp(m*x+c)
#logpars, rest = curve_fit(flog,d,v)
# mlog = logpars[0]
# clog = logpars[1]

# Convenience functions to return the voltage given angle, or angle given 
# voltage for the parameters we found, when angle is bayond 20 degrees:

def Vlog(deg, m, c):
    return exp(m*array(deg)+c)

def Dlog(v, m, c):
    return (log(array(v))-c)/m

# linear estimation of the 0-20 degree range: 
# assume line from (V(0),0)->(V(20), 20), so it 
# will always cross the y-axis at (0,0)

clin = 0.0
mlin = (Vlog(20,mlog,clog)-0)/(20.-0)

# our estimates as a single structure 
vpar = [mlog, clog, mlin]

# convenience functions to map angle and voltage to each other 
# within the (0,20) degree range
def Vlin(deg,m):
    return m*deg

def Dlin(v,m):
    return v/float(m)

# more general functions to map voltage and angle. 
def deg_volt(deg,ml,cl,m):
    """ give a single degree or range of degrees and get a list of 
    voltages in return"""
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
    """ give a single voltage or range of voltages and get a list of 
    degrees in return"""
    
    if not iterable(vlt): 
	vlt=[vlt]
    res=[]
    for v in vlt:
	if Dlin(v,m)>20.0:
	    res.append(Dlog(v,ml,cl))
	else:
	    res.append(Dlin(v,m))
    return res

# Print our parameters
print("Log:    m_log, c_log: \t[{:.4}, {:.4}]".format(mlog, clog))
print("Linear: m_lin, c_lin: \t[{:.4}, 0.0000]".format(mlin))

print ("maximum angle at 5V: \t{:.4}".format(volt_deg(5.0, mlog,clog,mlin)[0]))

# For verification, plot the measured voltage/angle points as crosses; the
# logarithmic estimation in red and the linear bit in blue hashes

print("\nClose the plot to continue.")

plot(D,V,'k+', ms=8, label="measured")
plot(d, exp(0.03061*d-0.6387),"-", color="#aa0000", label="log est.")
plot(D[0:5], 0.04869*D[0:5], "--", color="#0000aa", label="linear est.")
xlabel("Degrees")
ylabel("Volt")
legend(loc="upper left")
title("Measured and estimated voltage-angle dependency\n")
show()

### (2) create a general log-scale mapping between times and angles. Basically
### what we want our new dial scale to look like.

# We're looking for a log-like mapping between a set of time points and
# angles. Below we say that these three times (in hours) in "tp" should
# correspond to these three angles in "degp". And we want the function "tp" to
# fit these value pairs. The values below set 0 hours at the left end, 48
# hours (2 days) in the center and 240 hours (10 days) at the right end.

tp = array([0.0, 48.0, 240])
degp = array([0.0, 37.5, 73.44])	

# "tp" is a three-degree of freedom log function. "a" lets us scale the angle;
# "c" lets us scale the time, and "b" scales the log relationship itself. Why
# three degrees? I tried with one (only b) and two-degree (only a and b or
# only b and c) functions but they wouldn't fit properly. You often need to
# try different things like this.  

def tf(t,a,b,c):
    return a+b*log(t+c)

# use the general curve fit optimizer to fit "tf" to the parameters above.
# this call will return a warning for singular value in tf. Ignore that.
print("")
tpar, rest = curve_fit(tf,tp,degp)

print("\nlog dial params\n\n\ta: {}\n\tb: {}\n\tc: {}".format(*tpar))

# Convenience functions to map time to angle according to the parameters we
# found above.
def t_deg(t,a,b,c):
    deg = a+b*log(t+c)
    return deg

def deg_t(deg,a,b,c):
    t = exp((deg-a)/b)-c
    return t

### (3) We have a voltage-angle mapping for our dial and an angle-time mapping
### for our new scale. Put them together. 

# A twist here is that we have a restricted number of (8 bits worth or 256, to
# be precise) possible voltages. We need to base our mappings on those
# particular voltages since we can't generate any voltages in between. So we
# calculate tables that map each of those voltage indexes to the corresponding
# dial angle (from the voltage-angle mapping); to the corresponding time (from
# the angle-time mapping) and back.
# 
# We also need to decide on the time points we want to be able to select when
# setting the time. For each such time, choose the closest index in the table
# above.
#
# We print out a table showing the number of seconds left for each voltage. On
# the Arduino, we record the clock time when watering will happen, and compare
# it to the current time in a loop. Whenever that difference becomes smaller
# than the time for the next smaller voltage we drop to that smaller voltage
# and repeat until we reach zero.
#
# The benefit of this approach is that we always compare the current time to
# a fixed end time. That way we won't accumulate any errors over time the way
# we would if we just counted down a fixed amount for each step. The
# difference wouldn't matter in practice, of course, but this is neater.

# Our allowable voltages between 0 and 5 volts
tvolts = arange(256) * 5./255.

# Our desired time points when seting the time (in hours)
times = [6, 12, 18, 24, 36, 48, 60, 72, 96, 120, 144, 168, 192, 216, 240]

def find_nearest(arr,val):
    """ find the index of the nearest value in arr that is not 
    larger than the value in val."""
    if not iterable(val): 
	val = [val]
    res = []
    for v in val:
	res.append((abs(arr-v)).argmin())
    
    return array(res)


# volts to degrees to times:

vd = volt_deg(tvolts, *vpar)
vt = deg_t(vd, *tpar)

# cumlative time to goal in seconds. It's formatted to cut and paste
# into the arduino sketch code.

tleft = np.round(vt*60*60).astype(int)

print("\nTime indices for each voltage.\n") 
for i in range(32):
    print("{:>7},{:>7},{:>7},{:>7},{:>7},{:>7},{:>7},{:>7}"
            .format(*tleft[i*8:(i+1)*8]) + "{}"
            .format("," if i<31 else ""))
        

# We need to treat our set times a little differently. Most set times do not
# correspond directly to a possible voltage. So we create a smaller table with
# the total time to countdown, and the closest available voltage index. Also
# cut and paste into the sketch.

# convert to seconds and find the nearest voltage index
stimes = array(times)*60*60
nearest = find_nearest(tleft, stimes)

print("\nTotal countdown time and closest voltage index for each set time:\n")

print"const int n_times = {}\n".format(len(stimes)+1)

print("{{{:>6}, {:>3}}},\t // {:>3} hours".format(0,0,0))
for t,n,h in zip(stimes[:-1],nearest[:-1], times[:-1]):
    print ("{{{:>6}, {:>3}}},\t // {:>3} hours".format(t,n,h))

print ("{{{:>6}, {:>3}}}\t // {:>3} hours"
        .format(stimes[-1],nearest[-1],times[-1]))

if Draw_dial:

    # Draw the resulting display as an svg file.
    #
    # We make it for a 51.5x31.5mm screen. The needle center is 35mm from the
    # upper edge, with 7.5 mm circular clearance.

    cx = 51.5/2.0       # needle center
    cy = 35.0           # 
    dout = 28.0	        # outside diameter
    din_d = dout-4.0    # inside for day ticks
    din_h = dout-3.0    # inside for hour ticks
    din_s = dout-2.0    # ditto minor ticks

    # ticks for display 
    tdays = [24,48,72,96,120,144,168,192,216,240]
    thour = [6,12,18] +\
            [36,60]
    ticks = [1,2,3,4,5] +\
            [8,10,] +\
            [14,16] +\
            [20,22] +\
            [27,30,33] +\
            [39,42,45] +\
            [51,54,57] +\
            [63,66,69] +\
            [84,108,132,156, 180, 204,228]

    h_ang = volt_deg(tvolts[find_nearest(tleft, array(thour)*60*60)], *vpar)
    d_ang = volt_deg(tvolts[find_nearest(tleft, array(tdays)*60*60)], *vpar)
    t_ang = volt_deg(tvolts[find_nearest(tleft, array(ticks)*60*60)], *vpar)

    def to_mm(x,y):
        return (x*sw.mm, y*sw.mm)

    # Convert radius and angle to cartesian coordinates. Assume 0 deg is east,
    # going counterclockwise. Before conversion, multiply by dir and add adj. 

    def rt_xy(r, theta, center=(0,0), adj=0.0, adir=1, ydir=1):
        thadj = (theta*pi/180.0)*adir+(adj*pi/180.0)
        return ((center[0]+r*cos(thadj))*sw.mm,(center[1]+ydir*r*sin(thadj))*sw.mm)

    # min, max and center angles.

    amin = volt_deg(tvolts[0], *vpar)[0]
    amax = volt_deg(tvolts[-1], *vpar)[0]
    ac = (amax-amin)/2.0

    ppar=[(cx, cy), 90.0+ac, -1, -1]

    # Start a new svg drawing
    dial = sw.Drawing('dial.svg', size=(u'51.5mm', u'35mm'))

    days = dial.add(dial.g(id='days', stroke=sw.rgb(192,64,64), stroke_width=0.5))
    hours = dial.add(dial.g(id='hours', stroke=sw.rgb(0,0,0), stroke_width=0.5))
    other = dial.add(dial.g(id='small', stroke=sw.rgb(0,0,0), stroke_width=0.1))


    ## cutting marks
    dial.add(dial.rect(("0%","0%"), ("100%","100%"), 
        stroke="grey", fill="none", stroke_width=0.1))
    dial.add(dial.line(to_mm(0,31.5), to_mm(51.5,31.5), 
        stroke="grey", stroke_width=0.1))
    dial.add(dial.circle(center=(to_mm(51.5/2.0, 35.0)), r=7.0*sw.mm,
        stroke='grey', stroke_width=0.1, fill="none"))

    dial.add(dial.circle(center=(to_mm(51.5/2.0, 35.0)), r=29.0*sw.mm, 
        stroke='grey', stroke_width=0.1, fill="none"))

    # Zero line
    dial.add(dial.line(rt_xy(20, 0,*ppar), rt_xy(dout,0,*ppar),
        stroke='black', stroke_width=0.5))

    # day marks
    for a in d_ang:
        days.add(dial.line(rt_xy(din_d, a, *ppar),rt_xy(dout,a, *ppar)))
    # hour marks
    for a in h_ang:
        hours.add(dial.line(rt_xy(din_h, a, *ppar),rt_xy(dout,a, *ppar)))
    for a in t_ang:
        other.add(dial.line(rt_xy(din_s, a, *ppar),rt_xy(dout,a, *ppar)))

    dial.save()


