import vs
import sfmUtils
import os
import json

from win32gui import MessageBox
from win32con import MB_ICONINFORMATION, MB_ICONEXCLAMATION, MB_ICONERROR

#TODO: Sanity checking on inputs
#      Add in border frames to input
#         - if there's no frame within a certain distance of each end, then add in one

try:
    import tkFileDialog
    from tkinter import *
    from tkinter import ttk
except ImportError:
    import tkFileDialog
    from Tkinter import *
    from Tkinter import Tk as ttk
   

def replaceAnimationLog(animationLog, timePoints, valuePoints):
  #TODO: Add sanity checking on input lengths
  inputLength = len(timePoints)
  
  #Next, we're going to convert our times into 
  dmeTimePoints = []
  for time in timePoints:
    dmeTimePoints.append(vs.DmeTime_t(time))
  
  #TODO: allow us to overwrite the 0th point, since we don't just automatically trash all the data now
  
  # First, let's delete any old data that our animation will overwrite
  insertionPoint = -1
  for i in range(1, len(animationLog.times)):
    # If we hit a point that's past all of our time points, let's note that that's where
    #  we should be inserting points
    if (i < len(animationLog.times)) and \
       (animationLog.times[i] >= dmeTimePoints[-1]) and \
       (insertionPoint == -1):
      insertionPoint = i
      
    # If our new data overlaps with old data, we need to get rid of that old data,
    #  so we'll keep deleting data at the point where we find the issue until we don't 
    #  have any more points that overlap
    while (i < len(animationLog.times)) and \
          (animationLog.times[i] >= dmeTimePoints[0]) and \
          (animationLog.times[i] <= dmeTimePoints[-1]) :
      # Keep deleting elements at this point - this deletion will stop until 
      del animationLog.times[i]
      del animationLog.values[i]
      # Note where this overlapped data started - that way, we know where to put
      #  the data in next
      insertionPoint = i
   
  # If the insertion point was never changed, tell us to insert at the end
  if insertionPoint == -1:
    insertionPoint = len(animationLog.times)
    # And add in a keyframe to the start of our new data
    #  to provide a nice crisp transition for the data
    #  so long as there isn't already a data point too close
#    currentTimesLen = len(control.channel.log.layers[0].times)
#    if (dmeTimePoints[0] - control.channel.log.layers[0].times[currentTimesLen - 1]) > vs.DmeTime_t(2):
#      print("adding in buffer key")
#      dmeTimePoints.insert(0, dmeTimePoints[0] - vs.DmeTime_t(1))
#      currentValuesLen = len(control.channel.log.layers[0].values)
#      valuePoints.insert(0, control.channel.log.layers[0].values[currentValuesLen -1])
#    else:
#      print "Already a point was close - didn't add in buffer frame"
  #And make sure we reset our zero element to zero.
  #control.channel.log.layers[0].times[0] = vs.DmeTime_t(0)
  #control.channel.log.layers[0].values[0] = 0
  
  # Note! We're just appending data, so we'll always keep
  #  a starting point at time = 0, value = 0
  for i in range(0, inputLength):
    # Add in values for the time and value
    animationLog.times.insert(insertionPoint + i, dmeTimePoints[i])
    animationLog.values.insert(insertionPoint + i,valuePoints[i])
   
def replaceControlAnimation(controlName, timePoints, valuePoints, controlType="single"):
  # First, let's get our channel
  animSet = sfm.GetCurrentAnimationSet()
  rootGroup = animSet.GetRootControlGroup()
  control = rootGroup.FindControlByName( controlName, True )
  
  if controlType == "single":
    animationLog = control.channel.log.layers[0]
    replaceAnimationLog(animationLog, timePoints, valuePoints)
  elif controlType == "left":
    animationLog = control.leftvaluechannel.log.layers[0]
    replaceAnimationLog(animationLog, timePoints, valuePoints)
  elif controlType == "right":
    animationLog = control.rightvaluechannel.log.layers[0]
    replaceAnimationLog(animationLog, timePoints, valuePoints)
  elif controlType == "symmetric":
    animationLog = control.rightvaluechannel.log.layers[0]
    replaceAnimationLog(animationLog, timePoints, valuePoints)
    animationLog = control.leftvaluechannel.log.layers[0]
    replaceAnimationLog(animationLog, timePoints, valuePoints)
  else:
    print "You called replaceControlAnimation wrong, " + controlType + " isn't a valid parameter. You can use 'single', 'left', 'right', or 'symmetric'"


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


FACSmap = {"A26": {"control":"JawV", "controlType":"single"}, "A2": {"control":"JawV", "controlType":"single"}, "A1": {"control":"BrowOutV", "controlType":"symmetric"}}

def processJSONData(inputData):
  for AU in inputData:
    # If the absoluteTime flag is clear, we'll find the playhead and
    #  offset the times by that
    offset = 0
    if AU in FACSmap:
      print "current AU is:"
      print AU
      if absoluteTime.get() == 0 and int(fps.get()) > 0 :
        currentFrame = sfm.GetCurrentFrame()
        offset = (currentFrame / int(fps.get())) * 10000
      # Set up arrays to hold the time and value data
      auTimes = []
      auValues = []
      for element in inputData[AU]:
        auTimes.append(element["time"] + offset)
        auValues.append(element["value"])
      # Now push those arrays to the animation control
      replaceControlAnimation(FACSmap[AU]["control"], auTimes, auValues, FACSmap[AU]["controlType"])
    else:
      print "Wasn't in FACSmap:"
      print AU
    
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
