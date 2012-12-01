import vs
import sfmUtils

from win32gui import MessageBox
from win32con import MB_ICONINFORMATION, MB_ICONEXCLAMATION, MB_ICONERROR

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

