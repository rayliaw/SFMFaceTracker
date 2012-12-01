import vs
import sfmUtils

from win32gui import MessageBox
from win32con import MB_ICONINFORMATION, MB_ICONEXCLAMATION, MB_ICONERROR

# This is not really correct, but it works.
sys.argv = "Some Text" 




try:
    from tkinter import *
    from tkinter import ttk
except ImportError:
    print "importError"
    import FileDialog
    from Tkinter import *
    from Tkinter import Tk as ttk
   
import os
import json

#Let's let you select a file to load from
root = Tk()
root.withdraw()
fd = FileDialog.LoadFileDialog(root)
inputFilePath = fd.go()
inputFile = open(inputFilePath)
inputData = json.load(inputFile)
#Close that mofo!
inputFile.close()

print inputData['A1']

happyBigTimes = []
happyBigValues = []

for element in inputData['A1']:
  print element
  happyBigTimes.append(element["time"])
  happyBigValues.append(element["value"])


#dm = vs.g_pDataModel
#mdlCache = vs.g_pMDLCache

#trying to see what elements we can get ahold of
print 'Trying to get some elements...'
animSet = sfm.GetCurrentAnimationSet()
rootGroup = animSet.GetRootControlGroup()

happyBig = rootGroup.FindControlByName( 'happybig', True )
# print rootGroup
# print rootGroup.name
# print happyBig
# print happyBig.name
# print happyBig.channel.toElement.flexWeight
# print happyBig.value
# if happyBig.value < .5:
	# happyBig.value = .75
	# happyBig.channel.toElement.flexWeight = .75
# else:
	# happyBig.value = .25
	# happyBig.channel.toElement.flexWeight = .25
# print 'Did we change anything?'
# print happyBig.value
# print happyBig.channel.toElement.flexWeight

#print "Getting some info about the channel's log history"
#print happyBig.channel.log.layers
#print happyBig.channel.log.layers.float_log
#print happyBig.channel.log.layers[0].values[0]
#happyBig.channel.log.layers[0].values[0] = .5
#print happyBig.channel.log.layers[0].values[0]
#print happyBig.channel.log.layers[0].times[0]
#print "Trying to set times[0]"
#happyBig.channel.log.layers[0].times[0] = 0
#happyBig.channel.log.layers[0].times[1] = 2
#print happyBig.channel.log.layers[0].times[0]


# let's get 20 points in our timeline over 10 seconds.
# Set up some variables so we can extend the array, since I don't know how to set up aribtrary
#  time_array type objects
#tempTime = happyBig.channel.log.layers[0].times[0]
#tempValue = happyBig.channel.log.layers[0].values[0]
#i = 0
#print type(tempTime)


def replaceControlAnimation(controlName, timePoints, valuePoints):
  # First, let's get our channel
  animSet = sfm.GetCurrentAnimationSet()
  rootGroup = animSet.GetRootControlGroup()
  control = rootGroup.FindControlByName( controlName, True )
  print control
  
  #TODO: Add sanity checking on input lengths
  inputLength = len(timePoints)
  
  #Next, we're going to convert our times into 
  dmeTimePoints = []
  print "converting time points"
  for time in timePoints:
    print time
    dmeTimePoints.append(vs.DmeTime_t(time))
  
  # First, let's delete any old data that our animation will overwrite
  #  We always have at least one element as a sanity check, at time = 0, value = 0
  print type(control.channel.log.layers[0].times)
  print "length is: "
  print len(control.channel.log.layers[0].times)
 
  
  insertionPoint = -1
  for i in range(1, len(control.channel.log.layers[0].times)):
    # If we hit a point that's past all of our time points, let's note that that's where
    #  we should be inserting points
    if (i < len(control.channel.log.layers[0].times)) and \
       (control.channel.log.layers[0].times[i] >= dmeTimePoints[-1]) and \
       (insertionPoint == -1):
      insertionPoint = i
      
    # If our new data overlaps with old data, we need to get rid of that old data,
    #  so we'll keep deleting data at the point where we find the issue until we don't 
    #  have any more points that overlap
    while (i < len(control.channel.log.layers[0].times)) and \
          (control.channel.log.layers[0].times[i] >= dmeTimePoints[0]) and \
          (control.channel.log.layers[0].times[i] <= dmeTimePoints[-1]) :
      print "deleting..."
      # Keep deleting elements at this point - this deletion will stop until 
      del control.channel.log.layers[0].times[i]
      del control.channel.log.layers[0].values[i]
      # Note where this overlapped data started - that way, we know where to put
      #  the data in next
      insertionPoint = i
   
  # If the insertion point was never changed, tell us to insert at the end
  if insertionPoint == -1:
    len(control.channel.log.layers[0].times)
  #And make sure we reset our zero element to zero.
  control.channel.log.layers[0].times[0] = vs.DmeTime_t(0)
  control.channel.log.layers[0].values[0] = 0
  
  # Note! We're just appending data, so we'll always keep
  #  a starting point at time = 0, value = 0
  print "insertionPoint is: "
  print insertionPoint
  for i in range(0, inputLength):
    # Add in values for the time and value
    control.channel.log.layers[0].times.insert(insertionPoint + i, dmeTimePoints[i])
    control.channel.log.layers[0].values.insert(insertionPoint + i,valuePoints[i])


newTimes = [5000, 10000, 20000, 30000]
newValues = [0.5, 1, 0, 0.5]

#We got happyBigTimes and Values from way up where we imported our JSON object
replaceControlAnimation("happybig", happyBigTimes, happyBigValues)
#Select some time block
sfm.TimeSelectFrames( 0, 10, 20, 30, interpIn="EaseIn", interpOut="EaseOut" )


#happyBig.channel.log.layers[0].times.append(60)
#happyBig.channel.log.layers[0].values.append(.5)

# This code adds a control channel, which alters nothing, and for whatever reason, doesn't push its value
#  to the channel value's fromElement, but it does update the timeline and the channel log
# print "Trying to add a control channel..."
# shot = sfm.GetCurrentShot()
# animSet = sfm.GetCurrentAnimationSet()
# rootGroup = animSet.GetRootControlGroup()
# testControl = sfmUtils.CreateControlAndChannel( "Test Control", vs.AT_FLOAT, 0, animSet, shot )
# rootGroup.AddControl(testControl)


class MyException(Exception):
    def __init__(self, param):
        super(MyException, self).__init__(param)
		
print "We're done!"
print '\n'

def calculate(*args):
    try:
        value = slider_entry.get()
        feet.set(slider_entry.get())
        meters.set((0.3048 * value * 10000.0 + 0.5)/10000.0)
    except ValueError:
        pass
        
# Create the window and give it a title
#root = Tk()
root.title("Animate some controls!")

# Set up a frame inside the root window
mainframe = Frame(root, padx=3, pady =12)
# That resizes nicely
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

# Create some widgets 
feet = StringVar()
meters = StringVar()

# A widget for the text entry box
feet_entry = Entry(mainframe, width=7, textvariable=feet)
# and where it goes
feet_entry.grid(column=2, row=1, sticky=(W, E))

#A widget for a slider
slider_entry = Scale(mainframe, from_ = 0, to = 100, command = calculate, orient = "horizontal")
slider_entry.grid(column = 1, row = 1, sticky = (W, E))

# Label and button widgets and where they go
Label(mainframe, textvariable=meters).grid(column=2, row=2, sticky=(W, E))
Button(mainframe, text="Calculate", command=calculate).grid(column=3, row=3, sticky=W)

Button(mainframe, text="Do Nothing").grid(column=1, row=3, sticky=E)

# Label and output widgets and where they go
Label(mainframe, text="feet").grid(column=3, row=1, sticky=W)
Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=E)
Label(mainframe, text="meters").grid(column=3, row=2, sticky=W)

# Add some padding around all the widgets so they don't get in each others' faces
for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

# Grab focus of the input box, and bind the enter key to calculate for the 
#  entire window (bind to root, as opposed to something else - who
feet_entry.focus()
root.bind('<Return>', calculate)
#feet_entry.bind('<Return>', calculate)

# Aaaand run Tkinter's main loop, so everything updates
#root.mainloop()