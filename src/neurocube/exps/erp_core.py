#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2026.1.3),
    on Sun Sep  6 17:25:03 2026
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019) 
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. 
        https://doi.org/10.3758/s13428-018-01193-y

"""

# --- Import packages ---
from psychopy import locale_setup
from psychopy import prefs
from psychopy import plugins
plugins.activatePlugins()
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout, hardware
from psychopy.tools import environmenttools
from psychopy.constants import (
    NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, STOPPING, FINISHED, PRESSED, 
    RELEASED, FOREVER, priority
)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard

from typing import Any

# Tells VS Code this variable exists, but doesn't overwrite it
fixation_isi: Any

# --- Setup global variables (available in all functions) ---
# create a device manager to handle hardware (keyboards, mice, mirophones, speakers, etc.)
deviceManager = hardware.DeviceManager()
# ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
# store info about the experiment session
psychopyVersion = '2026.1.3'
expName = 'erp-core'  # from the Builder filename that created this script
expVersion = ''
# a list of functions to run when the experiment ends (starts off blank)
runAtExit = []
# information about this experiment
expInfo = {
    'participant': f"{randint(0, 999999):06.0f}",
    'session': '001',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'expVersion|hid': expVersion,
    'psychopyVersion|hid': psychopyVersion,
}

# --- Define some variables which will change depending on pilot mode ---
'''
To run in pilot mode, either use the run/pilot toggle in Builder, Coder and Runner, 
or run the experiment with `--pilot` as an argument. To change what pilot 
#mode does, check out the 'Pilot mode' tab in preferences.
'''
# work out from system args whether we are running in pilot mode
PILOTING = core.setPilotModeFromArgs()
# start off with values from experiment settings
_fullScr = True
_winSize = [1920,1080]
# if in pilot mode, apply overrides according to preferences
if PILOTING:
    # force windowed mode
    if prefs.piloting['forceWindowed']:
        _fullScr = False
        # set window size
        _winSize = prefs.piloting['forcedWindowSize']
    # replace default participant ID
    if prefs.piloting['replaceParticipantID']:
        expInfo['participant'] = 'pilot'

def showExpInfoDlg(expInfo):
    """
    Show participant info dialog.
    Parameters
    ==========
    expInfo : dict
        Information about this experiment.
    
    Returns
    ==========
    dict
        Information about this experiment.
    """
    # show participant info dialog
    dlg = gui.DlgFromDict(
        dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True
    )
    if dlg.OK == False:
        core.quit()  # user pressed cancel
    # return expInfo
    return expInfo


def setupData(expInfo, dataDir=None):
    """
    Make an ExperimentHandler to handle trials and saving.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    dataDir : Path, str or None
        Folder to save the data to, leave as None to create a folder in the current directory.    
    Returns
    ==========
    psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    # remove dialog-specific syntax from expInfo
    for key, val in expInfo.copy().items():
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)
    
    # data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
    # make sure filename is relative to dataDir
    if os.path.isabs(filename):
        dataDir = os.path.commonprefix([dataDir, filename])
        filename = os.path.relpath(filename, dataDir)
    
    # an ExperimentHandler isn't essential but helps with data saving
    thisExp = data.ExperimentHandler(
        name=expName, version=expVersion,
        extraInfo=expInfo, runtimeInfo=None,
        originPath='/home/jay/Documents/PsychoPy/ERP-CORE/erp-core.py',
        savePickle=True, saveWideText=True,
        dataFileName=dataDir + os.sep + filename, sortColumns='time'
    )
    # store pilot mode in data file
    thisExp.addData('piloting', PILOTING, priority=priority.LOW)
    thisExp.setPriority('thisRow.t', priority.CRITICAL)
    thisExp.setPriority('expName', priority.LOW)
    # return experiment handler
    return thisExp


def setupLogging(filename):
    """
    Setup a log file and tell it what level to log at.
    
    Parameters
    ==========
    filename : str or pathlib.Path
        Filename to save log file and data files as, doesn't need an extension.
    
    Returns
    ==========
    psychopy.logging.LogFile
        Text stream to receive inputs from the logging system.
    """
    # set how much information should be printed to the console / app
    if PILOTING:
        logging.console.setLevel(
            prefs.piloting['pilotConsoleLoggingLevel']
        )
    else:
        logging.console.setLevel('warning')
    # save a log file for detail verbose info
    logFile = logging.LogFile(filename+'.log')
    if PILOTING:
        logFile.setLevel(
            prefs.piloting['pilotLoggingLevel']
        )
    else:
        logFile.setLevel(
            logging.getLevel('info')
        )
    
    return logFile


def setupWindow(expInfo=None, win=None):
    """
    Setup the Window
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    win : psychopy.visual.Window
        Window to setup - leave as None to create a new window.
    
    Returns
    ==========
    psychopy.visual.Window
        Window in which to run this experiment.
    """
    if PILOTING:
        logging.debug('Fullscreen settings ignored as running in pilot mode.')
    
    if win is None:
        # if not given a window to setup, make one
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=0,
            winType='pyglet', allowGUI=False, allowStencil=False,
            monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
            backgroundImage='', backgroundFit='none',
            blendMode='avg', useFBO=True,
            units='pix',
            checkTiming=False  # we're going to do this ourselves in a moment
        )
    else:
        # if we have a window, just set the attributes which are safe to set
        win.color = [0,0,0]
        win.colorSpace = 'rgb'
        win.backgroundImage = ''
        win.backgroundFit = 'none'
        win.units = 'pix'
    if expInfo is not None:
        # get/measure frame rate if not already in expInfo
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='Attempting to measure frame rate of screen, please wait...')
        expInfo['frameRate'] = win._monitorFrameRate
    win.hideMessage()
    if PILOTING:
        # show a visual indicator if we're in piloting mode
        if prefs.piloting['showPilotingIndicator']:
            win.showPilotingIndicator()
        # always show the mouse in piloting mode
        if prefs.piloting['forceMouseVisible']:
            win.mouseVisible = True
    
    return win


def setupDevices(expInfo, thisExp, win):
    """
    Setup whatever devices are available (mouse, keyboard, speaker, eyetracker, etc.) and add them to 
    the device manager (deviceManager)
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window in which to run this experiment.
    Returns
    ==========
    bool
        True if completed successfully.
    """
    # --- Setup input devices ---
    ioConfig = {}
    ioSession = ioServer = eyetracker = None
    
    # store ioServer object in the device manager
    deviceManager.ioServer = ioServer
    
    # create a default keyboard (e.g. to check for escape)
    if deviceManager.getDevice('defaultKeyboard') is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='ptb'
        )
    # return True if completed successfully
    return True

def pauseExperiment(thisExp, win=None, timers=[], currentRoutine=None):
    """
    Pause this experiment, preventing the flow from advancing to the next routine until resumed.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    timers : list, tuple
        List of timers to reset once pausing is finished.
    currentRoutine : psychopy.data.Routine
        Current Routine we are in at time of pausing, if any. This object tells PsychoPy what Components to pause/play/dispatch.
    """
    # if we are not paused, do nothing
    if thisExp.status != PAUSED:
        return
    
    # start a timer to figure out how long we're paused for
    pauseTimer = core.Clock()
    # pause any playback components
    if currentRoutine is not None:
        for comp in currentRoutine.getPlaybackComponents():
            comp.pause()
    # make sure we have a keyboard
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        defaultKeyboard = deviceManager.addKeyboard(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend='PsychToolbox',
        )
    # run a while loop while we wait to unpause
    while thisExp.status == PAUSED:
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=['escape']):
            endExperiment(thisExp, win=win)
        # dispatch messages on response components
        if currentRoutine is not None:
            for comp in currentRoutine.getDispatchComponents():
                comp.device.dispatchMessages()
        # sleep 1ms so other threads can execute
        clock.time.sleep(0.001)
    # if stop was requested while paused, quit
    if thisExp.status == FINISHED:
        endExperiment(thisExp, win=win)
    # resume any playback components
    if currentRoutine is not None:
        for comp in currentRoutine.getPlaybackComponents():
            comp.play()
    # reset any timers
    for timer in timers:
        timer.addTime(-pauseTimer.getTime())


def run(expInfo, thisExp, win, globalClock=None, thisSession=None):
    """
    Run the experiment flow.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    psychopy.visual.Window
        Window in which to run this experiment.
    globalClock : psychopy.core.clock.Clock or None
        Clock to get global time from - supply None to make a new one.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    # mark experiment as started
    thisExp.status = STARTED
    # update experiment info
    expInfo['date'] = data.getDateStr()
    expInfo['expName'] = expName
    expInfo['expVersion'] = expVersion
    expInfo['psychopyVersion'] = psychopyVersion
    # make sure window is set to foreground to prevent losing focus
    win.winHandle.activate()
    # make sure variables created by exec are available globally
    exec = environmenttools.setExecEnvironment(globals())
    # get device handles from dict of input devices
    ioServer = deviceManager.ioServer
    # get/create a default keyboard (e.g. to check for escape)
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='PsychToolbox'
        )
    eyetracker = deviceManager.getDevice('eyetracker')
    # make sure we're running in the directory for this experiment
    os.chdir(_thisDir)
    # get filename from ExperimentHandler for convenience
    filename = thisExp.dataFileName
    frameTolerance = 0.001  # how close to onset before 'same' frame
    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    # get frame duration from frame rate in expInfo
    if 'frameRate' in expInfo and expInfo['frameRate'] is not None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0  # could not measure, so guess
    
    # Start Code - component code to be run after the window creation
    
    # --- Initialize components for Routine "prepareBlock" ---
    # Run 'Begin Experiment' code from blockCode
    import random
    # Create the pool of 5 potential block targets
    block_targets = ['A', 'B', 'C', 'D', 'E']
    # Shuffle them once at the start so they are in a completely random order
    random.shuffle(block_targets)
    
    # Fallback to satisfy editor warnings
    target_letter = 'A'
    
    # Import the LSL components from mne-lsl
    from mne_lsl.lsl import StreamInfo, StreamOutlet
    
    # Define the Stream Info with all required positional arguments:
    # 1. name: 'PsychoPy_Markers'
    # 2. stype: 'Markers'
    # 3. n_channels: 1
    # 4. sfreq: 0.0 (Since it's an irregular event stream, nominal rate must be 0)
    # 5. dtype: 'string' (Since we are sending letters like 'A', 'B', 'C')
    # 6. source_id: 'psychopy_trigger_stream'
    info = StreamInfo(
        name='PsychoPy_Markers', 
        stype='Markers', 
        n_channels=1, 
        sfreq=0.0, 
        dtype='string', 
        source_id='psychopy_trigger_stream'
    )
    
    # Create the Stream Outlet to broadcast markers across the network
    outlet = StreamOutlet(info)
    prepareblockText = visual.TextStim(win=win, name='prepareblockText',
        text='',
        font='Roboto',
        pos=[0,0], draggable=False, height=61.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-1.0);
    prepareBlock_key_resp = keyboard.Keyboard(deviceName='defaultKeyboard')
    
    # --- Initialize components for Routine "readysetgo" ---
    fixationPrepare = visual.ShapeStim(
        win=win, name='fixationPrepare',units='pix', 
        size=[6,6], vertices='circle',
        ori=0.0, pos=[0,0], draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='white', fillColor='white',
        opacity=None, depth=-1.0, interpolate=True)
    readyText = visual.TextStim(win=win, name='readyText',
        text='READY',
        font='Roboto',
        pos=[0,0], draggable=False, height=91.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='named', opacity=None, 
        languageStyle='LTR',
        depth=-2.0);
    setText = visual.TextStim(win=win, name='setText',
        text='SET',
        font='Roboto',
        pos=[0,0], draggable=False, height=91.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-3.0);
    goText = visual.TextStim(win=win, name='goText',
        text='GO',
        font='Roboto',
        pos=[0,0], draggable=False, height=91.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='named', opacity=None, 
        languageStyle='LTR',
        depth=-4.0);
    
    # --- Initialize components for Routine "trial" ---
    # Run 'Begin Experiment' code from code
    myText = 'A'
    corrAns = 'left'
    fixationTrial = visual.ShapeStim(
        win=win, name='fixationTrial',units='pix', 
        size=[6,6], vertices='circle',
        ori=0.0, pos=[0,0], draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='white', fillColor='white',
        opacity=None, depth=-1.0, interpolate=True)
    stim_text = visual.TextStim(win=win, name='stim_text',
        text='',
        font='Roboto',
        pos=[0,0], draggable=False, height=91.0, wrapWidth=None, ori=0.0, 
        color='black', colorSpace='named', opacity=None, 
        languageStyle='LTR',
        depth=-2.0);
    key_resp = keyboard.Keyboard(deviceName='defaultKeyboard')
    
    # --- Initialize components for Routine "block_feedback" ---
    # Run 'Begin Experiment' code from calc_block_stats
    msg = 'Calculating'
    feedbackText = visual.TextStim(win=win, name='feedbackText',
        text='',
        font='Roboto',
        pos=[0,0], draggable=False, height=65.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-1.0);
    
    # create some handy timers
    
    # global clock to track the time since experiment started
    if globalClock is None:
        # create a clock if not given one
        globalClock = core.Clock()
    if isinstance(globalClock, str):
        # if given a string, make a clock accoridng to it
        if globalClock == 'float':
            # get timestamps as a simple value
            globalClock = core.Clock(format='float')
        elif globalClock == 'iso':
            # get timestamps in ISO format
            globalClock = core.Clock(format='%Y-%m-%d_%H:%M:%S.%f%z')
        else:
            # get timestamps in a custom format
            globalClock = core.Clock(format=globalClock)
    if ioServer is not None:
        ioServer.syncClock(globalClock)
    logging.setDefaultClock(globalClock)
    if eyetracker is not None:
        eyetracker.enableEventReporting()
    # routine timer to track time remaining of each (possibly non-slip) routine
    routineTimer = core.Clock()
    win.flip()  # flip window to reset last flip timer
    # store the exact time the global clock started
    expInfo['expStart'] = data.getDateStr(
        format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6
    )
    
    # set up handler to look after randomisation of conditions etc
    blocks = data.TrialHandler2(
        name='blocks',
        nReps=5, 
        method='sequential', 
        extraInfo=expInfo, 
        originPath=-1, 
        trialList=[None], 
        seed=None, 
        isTrials=True, 
    )
    thisExp.addLoop(blocks)  # add the loop to the experiment
    thisBlock = blocks.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisBlock.rgb)
    if thisBlock != None:
        for paramName in thisBlock:
            globals()[paramName] = thisBlock[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    
    for thisBlock in blocks:
        blocks.status = STARTED
        if hasattr(thisBlock, 'status'):
            thisBlock.status = STARTED
        currentLoop = blocks
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisBlock.rgb)
        if thisBlock != None:
            for paramName in thisBlock:
                globals()[paramName] = thisBlock[paramName]
        
        # --- Prepare to start Routine "prepareBlock" ---
        # create an object to store info about Routine prepareBlock
        prepareBlock = data.Routine(
            name='prepareBlock',
            components=[prepareblockText, prepareBlock_key_resp],
        )
        prepareBlock.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from blockCode
        # PsychoPy tracks the current block number (0, 1, 2, 3, or 4) using blocks.thisN
        # We grab the corresponding shuffled target for this block block-by-block
        
        # 1. Grab the shuffled target letter for this block (blocks.thisN starts at 0)
        target_letter = block_targets[blocks.thisN]
        prepareblockText.setText("In this block, your target is: " + target_letter + "\nPress any key to start!")
        # create starting attributes for prepareBlock_key_resp
        prepareBlock_key_resp.keys = []
        prepareBlock_key_resp.rt = []
        _prepareBlock_key_resp_allKeys = []
        # store start times for prepareBlock
        prepareBlock.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        prepareBlock.tStart = globalClock.getTime(format='float')
        prepareBlock.status = STARTED
        thisExp.addData('prepareBlock.started', prepareBlock.tStart)
        prepareBlock.maxDuration = None
        # keep track of which components have finished
        prepareBlockComponents = prepareBlock.components
        for thisComponent in prepareBlock.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "prepareBlock" ---
        thisExp.currentRoutine = prepareBlock
        prepareBlock.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # if trial has changed, end Routine now
            if hasattr(thisBlock, 'status') and thisBlock.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *prepareblockText* updates
            
            # if prepareblockText is starting this frame...
            if prepareblockText.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                # keep track of start time/frame for later
                prepareblockText.frameNStart = frameN  # exact frame index
                prepareblockText.tStart = t  # local t and not account for scr refresh
                prepareblockText.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(prepareblockText, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'prepareblockText.started')
                # update status
                prepareblockText.status = STARTED
                prepareblockText.setAutoDraw(True)
            
            # if prepareblockText is active this frame...
            if prepareblockText.status == STARTED:
                # update params
                pass
            
            # *prepareBlock_key_resp* updates
            waitOnFlip = False
            
            # if prepareBlock_key_resp is starting this frame...
            if prepareBlock_key_resp.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                # keep track of start time/frame for later
                prepareBlock_key_resp.frameNStart = frameN  # exact frame index
                prepareBlock_key_resp.tStart = t  # local t and not account for scr refresh
                prepareBlock_key_resp.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(prepareBlock_key_resp, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'prepareBlock_key_resp.started')
                # update status
                prepareBlock_key_resp.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(prepareBlock_key_resp.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(prepareBlock_key_resp.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if prepareBlock_key_resp.status == STARTED and not waitOnFlip:
                theseKeys = prepareBlock_key_resp.getKeys(keyList=None, ignoreKeys=["escape"], waitRelease=False)
                _prepareBlock_key_resp_allKeys.extend(theseKeys)
                if len(_prepareBlock_key_resp_allKeys):
                    prepareBlock_key_resp.keys = _prepareBlock_key_resp_allKeys[-1].name  # just the last key pressed
                    prepareBlock_key_resp.rt = _prepareBlock_key_resp_allKeys[-1].rt
                    prepareBlock_key_resp.duration = _prepareBlock_key_resp_allKeys[-1].duration
                    # a response ends the routine
                    continueRoutine = False
            
            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer, globalClock], 
                    currentRoutine=prepareBlock,
                )
                # skip the frame we paused on
                continue
            
            # has a Component requested the Routine to end?
            if not continueRoutine:
                prepareBlock.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if prepareBlock.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in prepareBlock.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "prepareBlock" ---
        for thisComponent in prepareBlock.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for prepareBlock
        prepareBlock.tStop = globalClock.getTime(format='float')
        prepareBlock.tStopRefresh = tThisFlipGlobal
        thisExp.addData('prepareBlock.stopped', prepareBlock.tStop)
        # the Routine "prepareBlock" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        
        # --- Prepare to start Routine "readysetgo" ---
        # create an object to store info about Routine readysetgo
        readysetgo = data.Routine(
            name='readysetgo',
            components=[fixationPrepare, readyText, setText, goText],
        )
        readysetgo.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from readyCode
        # 2. Construct a descriptive block marker (e.g., "Block_1_Target_B")
        block_marker = f"Block_{blocks.thisN + 1}_Target_{target_letter}"
        
        # 3. Push the block marker immediately to your LSL stream
        # Since this is a macro-level event, it doesn't need to be flipped-synced to the frame
        outlet.push_sample([block_marker])
        # store start times for readysetgo
        readysetgo.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        readysetgo.tStart = globalClock.getTime(format='float')
        readysetgo.status = STARTED
        thisExp.addData('readysetgo.started', readysetgo.tStart)
        readysetgo.maxDuration = None
        # keep track of which components have finished
        readysetgoComponents = readysetgo.components
        for thisComponent in readysetgo.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "readysetgo" ---
        thisExp.currentRoutine = readysetgo
        readysetgo.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 4.3:
            # if trial has changed, end Routine now
            if hasattr(thisBlock, 'status') and thisBlock.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *fixationPrepare* updates
            
            # if fixationPrepare is starting this frame...
            if fixationPrepare.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                # keep track of start time/frame for later
                fixationPrepare.frameNStart = frameN  # exact frame index
                fixationPrepare.tStart = t  # local t and not account for scr refresh
                fixationPrepare.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(fixationPrepare, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'fixationPrepare.started')
                # update status
                fixationPrepare.status = STARTED
                fixationPrepare.setAutoDraw(True)
            
            # if fixationPrepare is active this frame...
            if fixationPrepare.status == STARTED:
                # update params
                pass
            
            # if fixationPrepare is stopping this frame...
            if fixationPrepare.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > fixationPrepare.tStartRefresh + 4.3-frameTolerance:
                    # keep track of stop time/frame for later
                    fixationPrepare.tStop = t  # not accounting for scr refresh
                    fixationPrepare.tStopRefresh = tThisFlipGlobal  # on global time
                    fixationPrepare.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'fixationPrepare.stopped')
                    # update status
                    fixationPrepare.status = FINISHED
                    fixationPrepare.setAutoDraw(False)
            
            # *readyText* updates
            
            # if readyText is starting this frame...
            if readyText.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                # keep track of start time/frame for later
                readyText.frameNStart = frameN  # exact frame index
                readyText.tStart = t  # local t and not account for scr refresh
                readyText.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(readyText, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'readyText.started')
                # update status
                readyText.status = STARTED
                readyText.setAutoDraw(True)
            
            # if readyText is active this frame...
            if readyText.status == STARTED:
                # update params
                pass
            
            # if readyText is stopping this frame...
            if readyText.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > readyText.tStartRefresh + 1-frameTolerance:
                    # keep track of stop time/frame for later
                    readyText.tStop = t  # not accounting for scr refresh
                    readyText.tStopRefresh = tThisFlipGlobal  # on global time
                    readyText.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'readyText.stopped')
                    # update status
                    readyText.status = FINISHED
                    readyText.setAutoDraw(False)
            
            # *setText* updates
            
            # if setText is starting this frame...
            if setText.status == NOT_STARTED and tThisFlip >= 1-frameTolerance:
                # keep track of start time/frame for later
                setText.frameNStart = frameN  # exact frame index
                setText.tStart = t  # local t and not account for scr refresh
                setText.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(setText, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'setText.started')
                # update status
                setText.status = STARTED
                setText.setAutoDraw(True)
            
            # if setText is active this frame...
            if setText.status == STARTED:
                # update params
                pass
            
            # if setText is stopping this frame...
            if setText.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > setText.tStartRefresh + 1-frameTolerance:
                    # keep track of stop time/frame for later
                    setText.tStop = t  # not accounting for scr refresh
                    setText.tStopRefresh = tThisFlipGlobal  # on global time
                    setText.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'setText.stopped')
                    # update status
                    setText.status = FINISHED
                    setText.setAutoDraw(False)
            
            # *goText* updates
            
            # if goText is starting this frame...
            if goText.status == NOT_STARTED and tThisFlip >= 2-frameTolerance:
                # keep track of start time/frame for later
                goText.frameNStart = frameN  # exact frame index
                goText.tStart = t  # local t and not account for scr refresh
                goText.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(goText, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'goText.started')
                # update status
                goText.status = STARTED
                goText.setAutoDraw(True)
            
            # if goText is active this frame...
            if goText.status == STARTED:
                # update params
                pass
            
            # if goText is stopping this frame...
            if goText.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > goText.tStartRefresh + 1-frameTolerance:
                    # keep track of stop time/frame for later
                    goText.tStop = t  # not accounting for scr refresh
                    goText.tStopRefresh = tThisFlipGlobal  # on global time
                    goText.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'goText.stopped')
                    # update status
                    goText.status = FINISHED
                    goText.setAutoDraw(False)
            
            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer, globalClock], 
                    currentRoutine=readysetgo,
                )
                # skip the frame we paused on
                continue
            
            # has a Component requested the Routine to end?
            if not continueRoutine:
                readysetgo.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if readysetgo.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in readysetgo.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "readysetgo" ---
        for thisComponent in readysetgo.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for readysetgo
        readysetgo.tStop = globalClock.getTime(format='float')
        readysetgo.tStopRefresh = tThisFlipGlobal
        thisExp.addData('readysetgo.stopped', readysetgo.tStop)
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if readysetgo.maxDurationReached:
            routineTimer.addTime(-readysetgo.maxDuration)
        elif readysetgo.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-4.300000)
        
        # set up handler to look after randomisation of conditions etc
        trials = data.TrialHandler2(
            name='trials',
            nReps=40, 
            method='sequential', 
            extraInfo=expInfo, 
            originPath=-1, 
            trialList=[None], 
            seed=None, 
            isTrials=True, 
        )
        thisExp.addLoop(trials)  # add the loop to the experiment
        thisTrial = trials.trialList[0]  # so we can initialise stimuli with some values
        # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
        if thisTrial != None:
            for paramName in thisTrial:
                globals()[paramName] = thisTrial[paramName]
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        
        for thisTrial in trials:
            trials.status = STARTED
            if hasattr(thisTrial, 'status'):
                thisTrial.status = STARTED
            currentLoop = trials
            thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
            if thisSession is not None:
                # if running in a Session with a Liaison client, send data up to now
                thisSession.sendExperimentData()
            # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
            if thisTrial != None:
                for paramName in thisTrial:
                    globals()[paramName] = thisTrial[paramName]
            
            # --- Prepare to start Routine "trial" ---
            # create an object to store info about Routine trial
            trial = data.Routine(
                name='trial',
                components=[fixationTrial, stim_text, key_resp],
            )
            trial.status = NOT_STARTED
            continueRoutine = True
            # update component parameters for each repeat
            # Run 'Begin Routine' code from code
            import random
            
            # 1. Random letter selection with replacement (each has a 0.2 probability)
            letters = ['A', 'B', 'C', 'D', 'E']
            myText = random.choice(letters)
            
            # 2. Randomly Select the ISI from a Uniform Distribution
            # Draw a random float from a rectangular distribution between 1.2 and 1.4 seconds
            isi_dur = random.uniform(1.2, 1.4)
            
            # 3. Check if the randomly selected letter matches our current block target
            if myText == target_letter:
                corrAns = 'left'   # Target button
            else:
                corrAns = 'right'  # Non-target button
            
            # Reset tracking states for the new trial
            stim_trigger_sent = False
            resp_trigger_sent = False
            stim_onset_time = None  # Tracks when the stimulus actually starts
            
            # 3. Log everything to your final data file for analysis
            thisExp.addData('myText', myText)
            thisExp.addData('corrAns', corrAns)
            thisExp.addData('block_target', target_letter) # Stores which letter was the active target
            thisExp.addData('block_number', blocks.thisN + 1) # Keeps track of block 1, 2, 3...
            # Save this exact duration to your data file so you can analyze it later!
            thisExp.addData('isi_duration', isi_dur)
            stim_text.setText(myText)
            # create starting attributes for key_resp
            key_resp.keys = []
            key_resp.rt = []
            _key_resp_allKeys = []
            # store start times for trial
            trial.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            trial.tStart = globalClock.getTime(format='float')
            trial.status = STARTED
            thisExp.addData('trial.started', trial.tStart)
            trial.maxDuration = None
            # keep track of which components have finished
            trialComponents = trial.components
            for thisComponent in trial.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            # reset timers
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1
            
            # --- Run Routine "trial" ---
            thisExp.currentRoutine = trial
            trial.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine:
                # if trial has changed, end Routine now
                if hasattr(thisTrial, 'status') and thisTrial.status == STOPPING:
                    continueRoutine = False
                # get current time
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
                # update/draw components on each frame
                # Run 'Each Frame' code from code
                # 1. Detect Stimulus Onset, Send Marker, and Clear Pre-Stimulus Keys
                # (Checks the status of your visual component named 'stim_text')
                if stim_text.status == STARTED and stim_onset_time is None:
                    stim_onset_time = t  # Record the routine time 't' when stimulus appeared
                    
                    # Send stimulus marker synced to the exact screen refresh frame
                    win.callOnFlip(outlet.push_sample, [myText]) 
                    stim_trigger_sent = True 
                    
                    # Discard any early keypresses made before the stimulus appeared
                    key_resp.keys = []
                    key_resp.rt = []
                    if hasattr(key_resp, 'clearEvents'):
                        key_resp.clearEvents()
                
                # 2. Check if the ISI has finished
                # (Because 'fixation_isi' is a Builder component, its variable exists directly in the script)
                isi_finished = False
                try:
                    if fixation_isi.status == FINISHED:
                        isi_finished = True
                except NameError:
                    # Safe fallback if 'fixation_isi' is renamed or temporarily missing
                    pass
                
                # 3. Determine if the Valid Response Window is active
                # Window opens ONLY after the stimulus has started, and closes once the ISI ends
                response_window_open = (stim_onset_time is not None) and not isi_finished
                
                # 4. Record and Send Marker for the FIRST keypress within this window
                if key_resp.keys and response_window_open and not resp_trigger_sent:
                    # Safely get the first key pressed during the active window
                    first_key = key_resp.keys if isinstance(key_resp.keys, list) else key_resp.keys
                    
                    # Extract the key name (handles modern KeyPress classes and strings)
                    if hasattr(first_key, 'name'):
                        key_name = first_key.name
                    else:
                        key_name = str(first_key)
                        
                    # Stream the clean key name (e.g. ['left']) to LSL
                    outlet.push_sample([key_name])
                    resp_trigger_sent = True
                
                # *fixationTrial* updates
                
                # if fixationTrial is starting this frame...
                if fixationTrial.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    # keep track of start time/frame for later
                    fixationTrial.frameNStart = frameN  # exact frame index
                    fixationTrial.tStart = t  # local t and not account for scr refresh
                    fixationTrial.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(fixationTrial, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'fixationTrial.started')
                    # update status
                    fixationTrial.status = STARTED
                    fixationTrial.setAutoDraw(True)
                
                # if fixationTrial is active this frame...
                if fixationTrial.status == STARTED:
                    # update params
                    pass
                
                # if fixationTrial is stopping this frame...
                if fixationTrial.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > fixationTrial.tStartRefresh + 0.2 + isi_dur-frameTolerance:
                        # keep track of stop time/frame for later
                        fixationTrial.tStop = t  # not accounting for scr refresh
                        fixationTrial.tStopRefresh = tThisFlipGlobal  # on global time
                        fixationTrial.frameNStop = frameN  # exact frame index
                        # add timestamp to datafile
                        thisExp.timestampOnFlip(win, 'fixationTrial.stopped')
                        # update status
                        fixationTrial.status = FINISHED
                        fixationTrial.setAutoDraw(False)
                
                # *stim_text* updates
                
                # if stim_text is starting this frame...
                if stim_text.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    # keep track of start time/frame for later
                    stim_text.frameNStart = frameN  # exact frame index
                    stim_text.tStart = t  # local t and not account for scr refresh
                    stim_text.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(stim_text, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'stim_text.started')
                    # update status
                    stim_text.status = STARTED
                    stim_text.setAutoDraw(True)
                
                # if stim_text is active this frame...
                if stim_text.status == STARTED:
                    # update params
                    pass
                
                # if stim_text is stopping this frame...
                if stim_text.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > stim_text.tStartRefresh + 0.2-frameTolerance:
                        # keep track of stop time/frame for later
                        stim_text.tStop = t  # not accounting for scr refresh
                        stim_text.tStopRefresh = tThisFlipGlobal  # on global time
                        stim_text.frameNStop = frameN  # exact frame index
                        # add timestamp to datafile
                        thisExp.timestampOnFlip(win, 'stim_text.stopped')
                        # update status
                        stim_text.status = FINISHED
                        stim_text.setAutoDraw(False)
                
                # *key_resp* updates
                waitOnFlip = False
                
                # if key_resp is starting this frame...
                if key_resp.status == NOT_STARTED and tThisFlip >= 0.2-frameTolerance:
                    # keep track of start time/frame for later
                    key_resp.frameNStart = frameN  # exact frame index
                    key_resp.tStart = t  # local t and not account for scr refresh
                    key_resp.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(key_resp, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'key_resp.started')
                    # update status
                    key_resp.status = STARTED
                    # keyboard checking is just starting
                    waitOnFlip = True
                    win.callOnFlip(key_resp.clock.reset)  # t=0 on next screen flip
                    win.callOnFlip(key_resp.clearEvents, eventType='keyboard')  # clear events on next screen flip
                
                # if key_resp is stopping this frame...
                if key_resp.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > key_resp.tStartRefresh + isi_dur-frameTolerance:
                        # keep track of stop time/frame for later
                        key_resp.tStop = t  # not accounting for scr refresh
                        key_resp.tStopRefresh = tThisFlipGlobal  # on global time
                        key_resp.frameNStop = frameN  # exact frame index
                        # add timestamp to datafile
                        thisExp.timestampOnFlip(win, 'key_resp.stopped')
                        # update status
                        key_resp.status = FINISHED
                        key_resp.status = FINISHED
                if key_resp.status == STARTED and not waitOnFlip:
                    theseKeys = key_resp.getKeys(keyList=['left','right'], ignoreKeys=["escape"], waitRelease=False)
                    _key_resp_allKeys.extend(theseKeys)
                    if len(_key_resp_allKeys):
                        key_resp.keys = _key_resp_allKeys[0].name  # just the first key pressed
                        key_resp.rt = _key_resp_allKeys[0].rt
                        key_resp.duration = _key_resp_allKeys[0].duration
                        # was this correct?
                        if (key_resp.keys == str(corrAns)) or (key_resp.keys == corrAns):
                            key_resp.corr = 1
                        else:
                            key_resp.corr = 0
                
                # check for quit (typically the Esc key)
                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return
                # pause experiment here if requested
                if thisExp.status == PAUSED:
                    pauseExperiment(
                        thisExp=thisExp, 
                        win=win, 
                        timers=[routineTimer, globalClock], 
                        currentRoutine=trial,
                    )
                    # skip the frame we paused on
                    continue
                
                # has a Component requested the Routine to end?
                if not continueRoutine:
                    trial.forceEnded = routineForceEnded = True
                # has the Routine been forcibly ended?
                if trial.forceEnded or routineForceEnded:
                    break
                # has every Component finished?
                continueRoutine = False
                for thisComponent in trial.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break  # at least one component has not yet finished
                
                # refresh the screen
                if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                    win.flip()
            
            # --- Ending Routine "trial" ---
            for thisComponent in trial.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            # store stop times for trial
            trial.tStop = globalClock.getTime(format='float')
            trial.tStopRefresh = tThisFlipGlobal
            thisExp.addData('trial.stopped', trial.tStop)
            # check responses
            if key_resp.keys in ['', [], None]:  # No response was made
                key_resp.keys = None
                # was no response the correct answer?!
                if str(corrAns).lower() == 'none':
                   key_resp.corr = 1;  # correct non-response
                else:
                   key_resp.corr = 0;  # failed to respond (incorrectly)
            # store data for trials (TrialHandler)
            trials.addData('key_resp.keys',key_resp.keys)
            trials.addData('key_resp.corr', key_resp.corr)
            if key_resp.keys != None:  # we had a response
                trials.addData('key_resp.rt', key_resp.rt)
                trials.addData('key_resp.duration', key_resp.duration)
            # the Routine "trial" was not non-slip safe, so reset the non-slip timer
            routineTimer.reset()
            # mark thisTrial as finished
            if hasattr(thisTrial, 'status'):
                thisTrial.status = FINISHED
            # if awaiting a pause, pause now
            if trials.status == PAUSED:
                thisExp.status = PAUSED
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[globalClock], 
                )
                # once done pausing, restore running status
                trials.status = STARTED
            thisExp.nextEntry()
            
        # completed 40 repeats of 'trials'
        trials.status = FINISHED
        
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # get names of stimulus parameters
        if trials.trialList in ([], [None], None):
            params = []
        else:
            params = trials.trialList[0].keys()
        # save data for this loop
        trials.saveAsText(filename + '_trials.csv', delim=',',
            stimOut=params,
            dataOut=['n','all_mean','all_std', 'all_raw'])
        
        # --- Prepare to start Routine "block_feedback" ---
        # create an object to store info about Routine block_feedback
        block_feedback = data.Routine(
            name='block_feedback',
            components=[feedbackText],
        )
        block_feedback.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from calc_block_stats
        # This extracts the reaction times from your loop (assuming it's named 'trials')
        # and calculates the mean using NumPy, which is built-in
        meanRt = trials.data['key_resp.rt'].mean()
        
        # You can also fetch accuracy data if you enabled 'Store correct' on key_resp
        nCorr = trials.data['key_resp.corr'].sum()
        totalTrials = trials.data['key_resp.corr'].size
        
        # Format the message to show on the screen (RT rounded to 3 decimal places)
        msg = f"Average Response Time: {meanRt:.3f} seconds\nAccuracy: {nCorr} / {totalTrials} correct"
        feedbackText.setText(msg)
        # store start times for block_feedback
        block_feedback.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        block_feedback.tStart = globalClock.getTime(format='float')
        block_feedback.status = STARTED
        thisExp.addData('block_feedback.started', block_feedback.tStart)
        block_feedback.maxDuration = None
        # keep track of which components have finished
        block_feedbackComponents = block_feedback.components
        for thisComponent in block_feedback.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "block_feedback" ---
        thisExp.currentRoutine = block_feedback
        block_feedback.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 3.0:
            # if trial has changed, end Routine now
            if hasattr(thisBlock, 'status') and thisBlock.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *feedbackText* updates
            
            # if feedbackText is starting this frame...
            if feedbackText.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                # keep track of start time/frame for later
                feedbackText.frameNStart = frameN  # exact frame index
                feedbackText.tStart = t  # local t and not account for scr refresh
                feedbackText.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(feedbackText, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'feedbackText.started')
                # update status
                feedbackText.status = STARTED
                feedbackText.setAutoDraw(True)
            
            # if feedbackText is active this frame...
            if feedbackText.status == STARTED:
                # update params
                pass
            
            # if feedbackText is stopping this frame...
            if feedbackText.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > feedbackText.tStartRefresh + 3-frameTolerance:
                    # keep track of stop time/frame for later
                    feedbackText.tStop = t  # not accounting for scr refresh
                    feedbackText.tStopRefresh = tThisFlipGlobal  # on global time
                    feedbackText.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'feedbackText.stopped')
                    # update status
                    feedbackText.status = FINISHED
                    feedbackText.setAutoDraw(False)
            
            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer, globalClock], 
                    currentRoutine=block_feedback,
                )
                # skip the frame we paused on
                continue
            
            # has a Component requested the Routine to end?
            if not continueRoutine:
                block_feedback.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if block_feedback.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in block_feedback.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "block_feedback" ---
        for thisComponent in block_feedback.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for block_feedback
        block_feedback.tStop = globalClock.getTime(format='float')
        block_feedback.tStopRefresh = tThisFlipGlobal
        thisExp.addData('block_feedback.stopped', block_feedback.tStop)
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if block_feedback.maxDurationReached:
            routineTimer.addTime(-block_feedback.maxDuration)
        elif block_feedback.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-3.000000)
        # mark thisBlock as finished
        if hasattr(thisBlock, 'status'):
            thisBlock.status = FINISHED
        # if awaiting a pause, pause now
        if blocks.status == PAUSED:
            thisExp.status = PAUSED
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[globalClock], 
            )
            # once done pausing, restore running status
            blocks.status = STARTED
        thisExp.nextEntry()
        
    # completed 5 repeats of 'blocks'
    blocks.status = FINISHED
    
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    # get names of stimulus parameters
    if blocks.trialList in ([], [None], None):
        params = []
    else:
        params = blocks.trialList[0].keys()
    # save data for this loop
    blocks.saveAsText(filename + '_blocks.csv', delim=',',
        stimOut=params,
        dataOut=['n','all_mean','all_std', 'all_raw'])
    # Run 'End Experiment' code from blockCode
    outlet.push_sample(["Experiment_End"])
    
    # mark experiment as finished
    endExperiment(thisExp, win=win)


def saveData(thisExp):
    """
    Save data from this experiment
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    filename = thisExp.dataFileName
    # these shouldn't be strictly necessary (should auto-save)
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)


def endExperiment(thisExp, win=None):
    """
    End this experiment, performing final shut down operations.
    
    This function does NOT close the window or end the Python process - use `quit` for this.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    """
    # stop any playback components
    if thisExp.currentRoutine is not None:
        for comp in thisExp.currentRoutine.getPlaybackComponents():
            comp.stop()
    if win is not None:
        # remove autodraw from all current components
        win.clearAutoDraw()
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed
        win.flip()
    # return console logger level to WARNING
    logging.console.setLevel(logging.WARNING)
    # mark experiment handler as finished
    thisExp.status = FINISHED
    # run any 'at exit' functions
    for fcn in runAtExit:
        fcn()
    logging.flush()


def quit(thisExp, win=None, thisSession=None):
    """
    Fully quit, closing the window and ending the Python process.
    
    Parameters
    ==========
    win : psychopy.visual.Window
        Window to close.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    thisExp.abort()  # or data files will save again on exit
    # make sure everything is closed down
    if win is not None:
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed before quitting
        win.flip()
        win.close()
    logging.flush()
    if thisSession is not None:
        thisSession.stop()
    # terminate Python process
    core.quit()


def main(expInfo=expInfo):
    # call all functions in order
    expInfo = showExpInfoDlg(expInfo=expInfo)
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    run(
        expInfo=expInfo, 
        thisExp=thisExp, 
        win=win,
        globalClock='float'
    )
    saveData(thisExp=thisExp)
    quit(thisExp=thisExp, win=win)


# if running this experiment as a script...
if __name__ == '__main__':
    # call all functions in order
    expInfo = showExpInfoDlg(expInfo=expInfo)
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    run(
        expInfo=expInfo, 
        thisExp=thisExp, 
        win=win,
        globalClock='float'
    )
    saveData(thisExp=thisExp)
    quit(thisExp=thisExp, win=win)
