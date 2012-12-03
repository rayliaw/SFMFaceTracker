import vs
import sfmUtils
import os
import json

from win32gui import MessageBox
from win32con import MB_ICONINFORMATION, MB_ICONEXCLAMATION, MB_ICONERROR

try:
    import tkFileDialog
    from tkinter import *
    from tkinter import ttk
except ImportError:
    import tkFileDialog
    from Tkinter import *
    from Tkinter import Tk as ttk
   


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


#####################
#
# Now let's handle some GUI stuff
#
##########################

# Load up a file dialog and
def loadAndProcessFile():
  inputFilePath = tkFileDialog.askopenfilename()
  if inputFilePath != None:
    inputFile = open(inputFilePath)
    print "inputFile is: "
    print inputFile
    inputData = json.load(inputFile)
    #Close that mofo!
    inputFile.close()
    #And process the data
    processJSONData(inputData)


FACSmap = {"A1": "happybig", "A2": "painbig"}

def processJSONData(inputData):
  for AU in inputData:
    # If the absoluteTime flag is clear, we'll find the playhead and
    #  offset the times by that
    offset = 0
    if absoluteTime.get() == 0 and int(fps.get()) > 0 :
      currentFrame = sfm.GetCurrentFrame()
      offset = (currentFrame / int(fps.get())) * 10000
    auTimes = []
    auValues = []
    for element in inputData[AU]:
      auTimes.append(element["time"] + offset)
      auValues.append(element["value"])
    replaceControlAnimation(FACSmap[AU], auTimes, auValues)
    
sys.argv = ' '
# Create the window and give it a title
root = Tk()
root.title("Import Kinect Facial Animation Data")

# Set up a frame inside the root window
mainframe = Frame(root, padx=3, pady =12)
# That resizes nicely
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

# Create some widgets 
# Get a frames-per-second value, and set it to 24 as a default
fps = StringVar()
fps.set(24)

absoluteTime = IntVar()
Checkbutton(mainframe, text="Absolute Time?", variable = absoluteTime).grid(column = 1, row = 1)

# A widget for the text entry box
fpsEntry = Entry(mainframe, width=7, textvariable=fps)
# and where it goes
fpsEntry.grid(column=2, row=1, sticky=(W, E))

# Label and output widgets and where they go
Label(mainframe, text="frames per second").grid(column=3, row=1, sticky=W)

# Label and button widgets and where they go
Button(mainframe, text="Load File...", command=loadAndProcessFile).grid(column=3, row=3, sticky=W)



# Add some padding around all the widgets so they don't get in each others' faces
for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

print "Tkinter version"
print TkVersion

# Aaaand run Tkinter's main loop, so everything updates
root.mainloop()
