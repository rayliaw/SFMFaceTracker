import vs
import sfmUtils
import os
import json
from vs import mathlib

from win32gui import MessageBox
from win32con import MB_ICONINFORMATION, MB_ICONEXCLAMATION, MB_ICONERROR


#Constants
headPitchOffset = 0

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
   

def replaceAnimationLog(animationLog, timePoints, originalValuePoints):
  
  #Next, we're going to convert our times into dmeTimePoints
  dmeTimePoints = []
  for time in timePoints:
    dmeTimePoints.append(vs.DmeTime_t(time))
    
  # And we want a local copy of our valuePoints array, so we don't mess it up
  #  for symmetric animation replacements that use the same input values
  valuePoints = list(originalValuePoints)
  
  #TODO: allow us to overwrite the 0th point, since we don't just automatically trash all the data now
  
  # First, let's delete any old data that our animation will overwrite
  insertionPoint = -1
  for i in range(0, len(animationLog.times)):
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
      # Keep deleting elements at this point, until the conditions of the while loop are broken
      del animationLog.times[i]
      del animationLog.values[i]
      # Note where this overlapped data started - that way, we know where to put
      #  the data in next
      insertionPoint = i
      
  
   
  # If the insertion point was never changed, tell us to insert at the end
  if insertionPoint == -1:
    insertionPoint = len(animationLog.times)
    
  # If there are points before our new data, we'll insert a new frame
  #  just before our animation in order to have a crisp transition
  if insertionPoint > 0:
    if (dmeTimePoints[0] - animationLog.times[insertionPoint - 1] > vs.DmeTime_t(20)):
      value = animationLog.values[insertionPoint - 1]
      dmeTimePoints.insert(0, dmeTimePoints[0] - vs.DmeTime_t(1))
      valuePoints.insert(0, value)
  
  if insertionPoint < len(animationLog.times):
    if (animationLog.times[insertionPoint] - dmeTimePoints[-1] > vs.DmeTime_t(20)):
      value = animationLog.values[insertionPoint]
      dmeTimePoints.append(dmeTimePoints[-1] + vs.DmeTime_t(1))
      valuePoints.append(value)
    # And add in a keyframe to the start of our new data
    #  to provide a nice crisp transition for the data
    #  so long as there isn't already a data point too close
  
  # Insert the data at the correct point
  for i in range(0, len(dmeTimePoints)):
    # Add in values for the time and value
    animationLog.times.insert(insertionPoint + i, dmeTimePoints[i])
    animationLog.values.insert(insertionPoint + i,valuePoints[i])
   
def replaceControlAnimation(controlName, timePoints, originalValuePoints,
                            controlType = "single", offset = 0, multiplier = 1):
  #First, sanity checking on input lengths
  if len(timePoints) != len(originalValuePoints):
    print "Lengths of time points and value points didn't match up,"
    print "so no animation was imported for the " + controlName + " control."
    return
    
  # Next, let's get our channel
  animSet = sfm.GetCurrentAnimationSet()
  rootGroup = animSet.GetRootControlGroup()
  control = rootGroup.FindControlByName( controlName, True )
  
  #Make a copy of the value points, since we want to only work on a local copy
  valuePoints = list(originalValuePoints)
  #Now adjust the value points
  for i, value in enumerate(valuePoints):
    value = (value * multiplier) + offset
    if value > 1:
      value = 1
    elif value < 0:
      value = 0
    valuePoints[i] = value
  
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

def replaceRotationAnimation(controlName, timePoints, originalValuePoints, addToDefault = True, additive=True):
  # Next, let's get our channel
  animSet = sfm.GetCurrentAnimationSet()
  rootGroup = animSet.GetRootControlGroup()
  control = rootGroup.FindControlByName( controlName, True )
  
  #Make a copy of the value points, since we want to only work on a local copy
  valuePoints = list(originalValuePoints)
  
  #Now, we'll make it so we're adding the rotation to the default
  if (addToDefault == True):
    defaultQuaternion = control.valueOrientation
  
  # I'm just glad this mathimagically works. 
  #  'Cause I sure don't understand quaternion math.
  for i, quaternion in enumerate(valuePoints):
    valuePoints[i] = quaternion * defaultQuaternion
  
  # Now replace the animation!
  animationLog = control.orientationChannel.log.layers[0]
  replaceAnimationLog(animationLog, timePoints, valuePoints)
  
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
    print inputFilePath
    inputData = json.load(inputFile)
    #Close that mofo!
    inputFile.close()
    #And process the data
    processJSONData(inputData)


FACSmap = {"A1": {"controlList": [{"name":"BrowOutV", "type":"symmetric", "offset": 0, "multiplier": 1}]},
           "A10": {"controlList": [{"name":"LipUpV", "type":"symmetric", "offset": 0.5, "multiplier": 0.5}]},
           "A26": {"controlList":[{"name":"JawV", "type":"single", "offset": 0, "multiplier": 1},
                                  {"name":"LipLoV", "type":"symmetric", "offset": 0.5, "multiplier": 0.45} ]},
           "AU26": {"controlList":[{"name":"JawV", "type":"single", "offset": 0, "multiplier": 1},
                                  {"name":"LipLoV", "type":"symmetric", "offset": 0.5, "multiplier": 0.45},
                                  {"name":"LipUpV", "type":"symmetric", "offset": 0.4, "multiplier": 0.35}]},
           "A20": {"controlList": [{"name":"PuckerLipUp", "type":"symmetric", "offset": 0, "multiplier": -2},
                                   {"name":"PuckerLipLo", "type":"symmetric", "offset": 0, "multiplier": -2},
                                   {"name":"Platysmus", "type":"symmetric", "offset": 0, "multiplier": 1}]},
           "A4": {"controlList": [{"name":"Frown", "type":"symmetric", "offset": 0, "multiplier": 1},
                                  {"name":"BrowInV", "type":"symmetric", "offset": 0.5, "multiplier": -0.5}]},
           "A13": {"controlList": [{"name":"Platysmus", "type":"symmetric", "offset": 0, "multiplier": 1},
                                   {"name":"Smile", "type":"symmetric", "offset": 0, "multiplier": -1}]},
           "A2": {"controlList": [{"name":"BrowOutV", "type":"symmetric", "offset": 0, "multiplier": 2}]},
           "leftEye" : {"controlList" :[{"name":"CloseLid", "type":"left", "offset": 1, "multiplier": -.7}]},
           "rightEye" : {"controlList" :[{"name":"CloseLid", "type":"right", "offset": 1, "multiplier": -.7}]},
           "leftBrow" : {"controlList" :[{"name":"BrowOutV", "type":"left", "offset": 0, "multiplier": 1},
                                         {"name":"BrowInV", "type":"left", "offset": .5, "multiplier": .5}]},
           "rightBrow" : {"controlList" :[{"name":"BrowOutV", "type":"right", "offset": 0, "multiplier": 1},
                                         {"name":"BrowInV", "type":"right", "offset": .5, "multiplier": .5}]}
           }
           

def processJSONData(inputData):
  for AU in inputData:
    # If the absoluteTime flag is clear, we'll find the playhead and
    #  offset the times by that
    offset = 0
    if AU in FACSmap:
      if absoluteTime.get() == 0 and int(fps.get()) > 0 :
        currentFrame = sfm.GetCurrentFrame()
        offset = (currentFrame / int(fps.get())) * 10000
      # Set up arrays to hold the time and value data
      auTimes = []
      auValues = []
      for element in inputData[AU]:
        auTimes.append((element["time"] * 10) + offset)
        auValues.append((element["value"]))
      # Now push those arrays to the animation control
      # control[0] is the control name,
      for control in FACSmap[AU]["controlList"]:
        replaceControlAnimation(control["name"], auTimes, auValues, control["type"],
                                control["offset"], control["multiplier"])
        
    else:
      print "Wasn't in FACSmap:"
      print AU
  # Now, let's get the rotation data
  # Make sure there's at least one bit of rotation data
  if "facePitch" in inputData or "xRotation" in inputData or \
     "faceYaw" in inputData or "zRotation" in inputData or \
     "faceRoll" in inputData or "yRotation" in inputData:

    # NOTE: The _Rotation elements are just there to support old data. Get rid of them soon.
    if "xRotation" in inputData:
      pitchPoints = inputData["xRotation"]
    if "facePitch" in inputData:
      pitchPoints = inputData["facePitch"]
    if "yRotation" in inputData: 
      rollPoints = inputData["yRotation"]
    if "faceRoll" in inputData: 
      rollPoints = inputData["faceRoll"]
    if "zRotation" in inputData:
      yawPoints = inputData["zRotation"]
    if "faceYaw" in inputData: 
      yawPoints = inputData["faceYaw"]
    # And update the appropriate control!
    times = []
    if absoluteTime.get() == 0 and int(fps.get()) > 0 :
      currentFrame = sfm.GetCurrentFrame()
      offset = (currentFrame / int(fps.get())) * 10000
    # Set up arrays to hold the time and value data
    times = []
    pitchValues = []
    rollValues = []
    yawValues = []
    for element in pitchPoints:
      times.append((element["time"] * 10) + offset)
      pitchValues.append(element["value"] + headPitchOffset)
    for element in rollPoints:
      #If we didn't get times from pitch...
      if len(times) == 0:
        times.append((element["time"] * 10) + offset)
      rollValues.append(element["value"])
    for element in yawPoints:
      #If we didn't get times from pitch OR roll... 
      #(We're guaranteed one of these lists has values at least)
      if len(times) == 0:
        times.append((element["time"] * 10) + offset)
      yawValues.append(element["value"])
      
    #Now fill in any blank data with zeroes
    if len(pitchValues) == 0:
      for i in range(0, len(times)):
        pitchValues.append(0)
    if len(rollValues) == 0:
      for i in range(0, len(times)):
        rollValues.append(0)
    if len(yawValues) == 0:
      for i in range(0, len(times)):
        yawValues.append(0)
    
      
    print pitchValues
    print rollValues
    print yawValues
    
    quaternionValues = []
    #Now make some quaternions out of those values
    for i in range(0, len(pitchValues)):
      qAngle = mathlib.QAngle(rollValues[i], yawValues[i], pitchValues[i])
      # Can we go from that straight to quaternion?
      radianEulerAngle = mathlib.RadianEuler(qAngle)
      quaternion = mathlib.Quaternion(radianEulerAngle)
      quaternionValues.append(quaternion)
      
    replaceRotationAnimation("bip_head", times, quaternionValues)
  
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


# Aaaand run Tkinter's main loop, so everything updates
root.mainloop()
