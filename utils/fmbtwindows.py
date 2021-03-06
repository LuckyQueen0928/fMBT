# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
This is library implements fMBT GUITestInterface for Windows

How to setup Windows device under test

1. Install Python 2.X. (For example 2.7.)

2. Add Python to PATH, so that command "python" starts the interpreter.

3. Copy fMBT's pythonshare directory to Windows.

4. In the pythonshare directory, run "python setup.py install"

5. Run:
   cd \\python27\\scripts
   python pythonshare-server --interface=all --password=xxxxxxxx


How to connect to the device

import fmbtwindows
d = fmbtwindows.Device("IP-ADDRESS-OF-THE-DEVICE", password="xxxxxxxx")
"""

import ast
import fmbt
import fmbt_config
import fmbtgti
import inspect
import os
import pythonshare
import subprocess
import zlib

try:
    import fmbtpng
except ImportError:
    fmbtpng = None

if os.name == "nt":
    _g_closeFds = False
else:
    _g_closeFds = True

def _adapterLog(msg):
    fmbt.adapterlog("fmbtwindows %s" % (msg,))

def _run(command, expectedExitStatus=None):
    """
    Execute command in child process, return status, stdout, stderr.
    """
    if type(command) == str or os.name == "nt":
        shell = True
    else:
        shell = False

    try:
        p = subprocess.Popen(command, shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=_g_closeFds)
        if expectedExitStatus != None:
            out, err = p.communicate()
        else:
            out, err = ('', None)
    except Exception, e:
        class fakeProcess(object): pass
        p = fakeProcess
        p.returncode = 127
        out, err = ('', e)

    exitStatus = p.returncode

    if (expectedExitStatus != None and
        exitStatus != expectedExitStatus and
        exitStatus not in expectedExitStatus):
        msg = "Executing %s failed. Exit status: %s, expected %s" % (
            command, exitStatus, expectedExitStatus)
        _adapterLog("%s\n    stdout: %s\n    stderr: %s\n" % (msg, out, err))
        raise FMBTWindowsError(msg)

    return exitStatus, out, err

_g_keyNames = [
    "VK_LBUTTON", "VK_RBUTTON", "VK_CANCEL", "VK_MBUTTON",
    "VK_XBUTTON1", "VK_XBUTTON2", "VK_BACK", "VK_TAB", "VK_CLEAR",
    "VK_RETURN", "VK_SHIFT", "VK_CONTROL", "VK_MENU", "VK_PAUSE",
    "VK_CAPITAL", "VK_KANA", "VK_HANGUL", "VK_JUNJA", "VK_FINAL",
    "VK_HANJA", "VK_KANJI", "VK_ESCAPE", "VK_CONVERT", "VK_NONCONVERT",
    "VK_ACCEPT", "VK_MODECHANGE", "VK_SPACE", "VK_PRIOR", "VK_NEXT",
    "VK_END", "VK_HOME", "VK_LEFT", "VK_UP", "VK_RIGHT", "VK_DOWN",
    "VK_SELECT", "VK_PRINT", "VK_EXECUTE", "VK_SNAPSHOT", "VK_INSERT",
    "VK_DELETE", "VK_HELP", "VK_LWIN", "VK_RWIN", "VK_APPS", "VK_SLEEP",
    "VK_NUMPAD0", "VK_NUMPAD1", "VK_NUMPAD2", "VK_NUMPAD3", "VK_NUMPAD4",
    "VK_NUMPAD5", "VK_NUMPAD6", "VK_NUMPAD7", "VK_NUMPAD8", "VK_NUMPAD9",
    "VK_MULTIPLY", "VK_ADD", "VK_SEPARATOR", "VK_SUBTRACT", "VK_DECIMAL",
    "VK_DIVIDE", "VK_F1", "VK_F2", "VK_F3", "VK_F4", "VK_F5", "VK_F6",
    "VK_F7", "VK_F8", "VK_F9", "VK_F10", "VK_F11", "VK_F12", "VK_F13",
    "VK_F14", "VK_F15", "VK_F16", "VK_F17", "VK_F18", "VK_F19", "VK_F20",
    "VK_F21", "VK_F22", "VK_F23", "VK_F24", "VK_NUMLOCK", "VK_SCROLL",
    "VK_LSHIFT", "VK_RSHIFT", "VK_LCONTROL", "VK_RCONTROL", "VK_LMENU",
    "VK_RMENU", "VK_BROWSER_BACK", "VK_BROWSER_FORWARD",
    "VK_BROWSER_REFRESH", "VK_BROWSER_STOP", "VK_BROWSER_SEARCH",
    "VK_BROWSER_FAVORITES", "VK_BROWSER_HOME", "VK_VOLUME_MUTE",
    "VK_VOLUME_DOWN", "VK_VOLUME_UP", "VK_MEDIA_NEXT_TRACK",
    "VK_MEDIA_PREV_TRACK", "VK_MEDIA_STOP", "VK_MEDIA_PLAY_PAUSE",
    "VK_LAUNCH_MAIL", "VK_LAUNCH_MEDIA_SELECT", "VK_LAUNCH_APP1",
    "VK_LAUNCH_APP2", "VK_OEM_1", "VK_OEM_PLUS", "VK_OEM_COMMA",
    "VK_OEM_MINUS", "VK_OEM_PERIOD", "VK_OEM_2", "VK_OEM_3", "VK_OEM_4",
    "VK_OEM_5", "VK_OEM_6", "VK_OEM_7", "VK_OEM_8", "VK_OEM_102",
    "VK_PROCESSKEY", "VK_PACKET", "VK_ATTN", "VK_CRSEL", "VK_EXSEL",
    "VK_EREOF", "VK_PLAY", "VK_ZOOM", "VK_PA1", "VK_OEM_CLEAR", "0", "1",
    "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F",
    "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z"]

# ShowWindow showCmd
SW_HIDE          = 0
SW_NORMAL        = 1
SW_MINIMIZED     = 2
SW_MAXIMIZE      = 3
SW_NOACTIVATE    = 4
SW_SHOW          = 5
SW_MINIMIZE      = 6
SW_MINNOACTIVE   = 7
SW_SHOWNA        = 8
SW_RESTORE       = 9
SW_DEFAULT       = 10
SW_FORCEMINIMIZE = 11

_g_showCmds = [
    "SW_HIDE", "SW_NORMAL", "SW_MINIMIZED", "SW_MAXIMIZE", "SW_NOACTIVATE",
    "SW_SHOW", "SW_MINIMIZE", "SW_MINNOACTIVE", "SW_SHOWNA", "SW_RESTORE",
    "SW_DEFAULT", "SW_FORCEMINIMIZE"]

class ViewItem(fmbtgti.GUIItem):
    def __init__(self, view, itemId, parentId, className, text, bbox, dumpFilename):
        self._view = view
        self._itemId = itemId
        self._parentId = parentId
        self._className = className
        self._text = text
        fmbtgti.GUIItem.__init__(self, self._className, bbox, dumpFilename)

    def children(self):
        return [self._view._viewItems[winfo[0]]
                for winfo in self._view._itemTree[self._itemId]]

    def __str__(self):
        return "ViewItem(%s)" % (self._view._dumpItem(self),)

class View(object):
    def __init__(self, dumpFilename, itemTree):
        self._dumpFilename = dumpFilename
        self._itemTree = itemTree
        self._viewItems = {}
        for itemId, winfoList in itemTree.iteritems():
            for winfo in winfoList:
                itemId, parentId, className, text, bbox = winfo
                self._viewItems[itemId] = ViewItem(
                    self, itemId, parentId, className, text, bbox, dumpFilename)

    def rootItem(self):
        return self._viewItems[self._itemTree["root"][0][0]]

    def _dumpItem(self, viewItem):
        return "id=%s cls=%s text=%s bbox=%s" % (
            viewItem._itemId, repr(viewItem._className), repr(viewItem._text),
            viewItem._bbox)

    def _dumpTree(self, rootItem, depth=0):
        l = ["%s%s" % (" " * (depth * 4), self._dumpItem(rootItem))]
        for child in rootItem.children():
            l.extend(self._dumpTree(child, depth+1))
        return l

    def dumpTree(self, rootItem=None):
        """
        Returns item tree as a string
        """
        if rootItem == None:
            rootItem = self.rootItem()
        return "\n".join(self._dumpTree(rootItem))

    def __str__(self):
        return "View(%s, %s items)" % (repr(self._dumpFilename), len(self._viewItems))

    def findItems(self, comparator, count=-1, searchRootItem=None, searchItems=None):
        foundItems = []
        if count == 0: return foundItems
        if searchRootItem != None:
            if comparator(searchRootItem):
                foundItems.append(searchRootItem)
            for c in searchRootItem.children():
                foundItems.extend(self.findItems(comparator, count=count-len(foundItems), searchRootItem=c))
        else:
            if searchItems:
                domain = iter(searchItems)
            else:
                domain = self._viewItems.itervalues
            for i in domain():
                if comparator(i):
                    foundItems.append(i)
                    if count > 0 and len(foundItems) >= count:
                        break
        return foundItems

    def findItemsByText(self, text, partial=False, count=-1, searchRootItem=None, searchItems=None):
        if partial:
            c = lambda item: (text in item._text)
        else:
            c = lambda item: (text == item._text)
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems)

    def findItemsByClass(self, className, partial=False, count=-1, searchRootItem=None, searchItems=None):
        if partial:
            c = lambda item: (className in item._className)
        else:
            c = lambda item: (className == item._className)
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems)


class Device(fmbtgti.GUITestInterface):
    def __init__(self, connspec, password=None, screenshotSize=(None, None), **kwargs):
        """Connect to windows device under test.

        Parameters:

          connspec (string):
                  specification for connecting to a pythonshare
                  server that will run fmbtwindows-agent. The format is
                  "socket://<host>[:<port>]".

          password (optional, string or None):
                  authenticate to pythonshare server with given
                  password. The default is None (no authentication).

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).

        To prepare a windows device for connection, launch there

        python pythonshare-server --password mysecretpwd

        When not on trusted network, consider ssh port forward, for
        instance.
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self.setConnection(WindowsConnection(connspec, password))

    def existingView(self):
        if self._lastView:
            return self._lastView
        else:
            raise FMBTWindowsError("view is not available. Missing refreshView()?")

    def getFile(self, remoteFilename, localFilename=None):
        """
        Fetch file from the device.

        Parameters:

          remoteFilename (string):
                  file to be fetched on device

          localFilename (optional, string or None):
                  file to be saved to local filesystem. If None,
                  return contents of the file without saving them.
        """
        return self._conn.recvFile(remoteFilename, localFilename)

    def getMatchingPaths(self, pathnamePattern):
        """
        Returns list of paths matching pathnamePattern on the device.

        Parameters:

          pathnamePattern (string):
                  Pattern for matching files and directories on the device.

        Example:

          getMatchingPaths("c:/windows/*.ini")

        Implementation runs glob.glob(pathnamePattern) on remote device.
        """
        return self._conn.recvMatchingPaths(pathnamePattern)

    def keyNames(self):
        """
        Returns list of key names recognized by pressKey
        """
        return sorted(_g_keyNames)

    def refreshView(self, window=None, forcedView=None):
        """
        (Re)reads widgets on the top window and updates the latest view.

        Parameters:

          window (integer (hWnd) or string (title), optional):
                  read widgets from given window instead of the top window.

          forcedView (View or filename, optional):
                  use given View object or view file instead of reading the
                  items from the device.

        Returns View object.
        """
        if forcedView != None:
            if isinstance(forcedView, View):
                self._lastView = forcedView
            elif type(forcedView) in [str, unicode]:
                self._lastView = View(forcedView,
                                      ast.literal_eval(file(forcedView).read()))
        else:
            if self.screenshotDir() == None:
                self.setScreenshotDir(self._screenshotDirDefault)
            if self.screenshotSubdir() == None:
                self.setScreenshotSubdir(self._screenshotSubdirDefault)
            viewFilename = self._newScreenshotFilepath()[:-3] + "view"
            viewData = self._conn.recvViewData(window)
            file(viewFilename, "w").write(repr(viewData))
            self._lastView = View(viewFilename, viewData)
        return self._lastView

    def setDisplaySize(self, size):
        """
        Transform coordinates of synthesized events (like a tap) from
        screenshot resolution to display input area size. By default
        events are synthesized directly to screenshot coordinates.

        Parameters:

          size (pair of integers: (width, height)):
                  width and height of display in pixels. If not given,
                  values from EnumDisplayMonitors are used.

        Returns None.
        """
        width, height = size
        screenWidth, screenHeight = self.screenSize()
        self._conn.setScreenToDisplayCoords(
            lambda x, y: (x * width / screenWidth,
                          y * height / screenHeight))
        self._conn.setDisplayToScreenCoords(
            lambda x, y: (x * screenWidth / width,
                          y * screenHeight / height))

    def setForegroundWindow(self, window):
        """
        Set a window with the title as a foreground window

        Parameters:

          window (title (string) or hwnd (integer):
                  title or handle of the window to be raised
                  foreground.

        Returns True if the window was brought to the foreground,
        otherwise False.

        Notes: calls SetForegroundWindow in user32.dll.
        """
        return self.existingConnection().sendSetForegroundWindow(window)

    def setScreenshotSize(self, size):
        """
        Force screenshots from device to use given resolution.
        Overrides detected monitor resolution on device.

        Parameters:

          size (pair of integers: (width, height)):
                  width and height of screenshot.
        """
        self._conn.setScreenshotSize(size)

    def shell(self, command):
        """
        Execute command in Windows.

        Parameters:

          command (string or list of strings):
                  command to be executed. Will be forwarded directly
                  to subprocess.check_output.  If command is a string,
                  then it will be executed in subshell, otherwise without
                  shell.

        Returns what is printed by the command.

        If you wish to receive exitstatus or standard output and error
        separated from command, refer to shellSOE().

        """
        return self._conn.evalPython('shell(%s)' % (repr(command),))

    def shellSOE(self, command, asyncStatus=None, asyncOut=None, asyncError=None):
        """
        Execute command in Windows.

        Parameters:

          command (string or list of strings):
                  command to be executed. Will be forwarded directly
                  to subprocess.check_output.  If command is a string,
                  then it will be executed in subshell, otherwise without
                  shell.

          asyncStatus (string or None)
                  filename (on device) to which the status of
                  asynchronously executed shellCommand will be
                  written. The default is None, that is, command will
                  be run synchronously, and status will be returned in
                  the tuple.

          asyncOut (string or None)
                  filename (on device) to which the standard output of
                  asynchronously executed shellCommand will be
                  written. The default is None.

          asyncError (string or None)
                  filename (on device) to which the standard error of
                  asynchronously executed shellCommand will be
                  written. The default is None.

        Returns triplet: exit status, standard output and standard error
        from the command.

        If executing command fails, returns None, None, None.
        """
        return self._conn.evalPython(
            'shellSOE(%s, asyncStatus=%s, asyncOut=%s, asyncError=%s)'
            % (repr(command),
               repr(asyncStatus), repr(asyncOut), repr(asyncError)))

    def showWindow(self, window, showCmd=SW_NORMAL):
        """
        Send showCmd to window.

        Parameters:

          window (window title (string) or handle (integer)):
                  window to which the command will be sent.

          showCmd (integer or string):
                  command to be sent. Valid commands are 0..11:
                  SW_HIDE, SW_NORMAL, SW_MINIMIZED, SW_MAXIMIZE,
                  SW_NOACTIVATE, SW_SHOW SW_MINIMIZE, SW_MINNOACTIVE,
                  SW_SHOWNA, SW_RESTORE, SW_DEFAULT, SW_FORCEMINIMIZE.

        Returns True if the window was previously visible,
        otherwise False.

        Notes: calls ShowWindow in user32.dll.
        """
        return self.existingConnection().sendShowWindow(window, showCmd)

    def tapText(self, text, partial=False, **tapKwArgs):
        """
        Find an item with given text from the latest view, and tap it.

        Parameters:

          partial (boolean, optional):
                  refer to verifyText documentation. The default is
                  False.

          tapPos (pair of floats (x, y)):
                  refer to tapItem documentation.

          button, long, hold, count, delayBetweenTaps (optional):
                  refer to tap documentation.

        Returns True if successful, otherwise False.
        """
        items = self.existingView().findItemsByText(text, partial=partial, count=1)
        if len(items) == 0: return False
        return self.tapItem(items[0], **tapKwArgs)

    def topWindowProperties(self):
        """
        Return properties of the top window as a dictionary
        """
        return self._conn.recvTopWindowProperties()

    def windowList(self):
        """
        Return list of properties of windows (dictionaries)

        Example: list window handles and titles:
          for props in d.windowList():
              print props["hwnd"], props["title"]
        """
        return self._conn.recvWindowList()

    def launchHTTPD(self):
        """
        DEPRECATED, will be removed, do not use!
        """
        return self._conn.evalPython("launchHTTPD()")

    def stopHTTPD(self):
        """
        DEPRECATED, will be removed, do not use!
        """
        return self._conn.evalPython("stopHTTPD()")

    def view(self):
        return self._lastView

class WindowsConnection(fmbtgti.GUITestConnection):
    def __init__(self, connspec, password):
        fmbtgti.GUITestConnection.__init__(self)
        self._screenshotSize = (None, None) # autodetect
        self._agent_ns = "fmbtwindows-agent"
        self._agent = pythonshare.connection(connspec, password=password)
        agentFilename = os.path.join(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
            "fmbtwindows_agent.py")
        self._agent.exec_in(self._agent_ns, file(agentFilename).read())
        self.setScreenToDisplayCoords(lambda x, y: (x, y))
        self.setDisplayToScreenCoords(lambda x, y: (x, y))

    def setScreenshotSize(self, screenshotSize):
        self._screenshotSize = screenshotSize
        screenW, screenH = self._screenshotSize
        inputW, inputH = self._agent.eval_in(self._agent_ns, "_mouse_input_area")
        self.setScreenToDisplayCoords(
            lambda x, y: (x * inputW / screenW, y * inputH / screenH))
        self.setDisplayToScreenCoords(
            lambda x, y: (x * screenW / inputW, y * screenH / inputH))

    def execPython(self, code):
        return self._agent.exec_in(self._agent_ns, code)

    def evalPython(self, code):
        return self._agent.eval_in(self._agent_ns, code)

    def recvFile(self, remoteFilename, localFilename=None):
        data = self._agent.eval_in(self._agent_ns, "file(%s).read()" % (repr(remoteFilename),))
        if localFilename:
            file(localFilename, "wb").write(data)
            return True
        else:
            return data

    def recvMatchingPaths(self, pathnamePattern):
        return self._agent.eval_in(self._agent_ns,
                                   "glob.glob(%s)" % (repr(pathnamePattern),))

    def recvScreenshot(self, filename, screenshotSize=(None, None)):
        ppmfilename = filename + ".ppm"

        if screenshotSize == (None, None):
            screenshotSize = self._screenshotSize

        width, height, zdata = self._agent.eval_in(
            self._agent_ns, "screenshotZYBGR(%s)" % (repr(screenshotSize),))

        data = zlib.decompress(zdata)

        fmbtgti.eye4graphics.wbgr2rgb(data, width, height)
        if fmbtpng != None:
            file(filename, "wb").write(
                fmbtpng.raw2png(data, width, height, 8, "RGB"))
        else:
            ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)

            f = file(filename + ".ppm", "wb")
            f.write(ppm_header)
            f.write(data)
            f.close()
            _run([fmbt_config.imagemagick_convert, ppmfilename, filename], expectedExitStatus=[0])
            os.remove(ppmfilename)
        return True

    def recvTopWindowProperties(self):
        return self.evalPython("topWindowProperties()")

    def recvViewData(self, window=None):
        if window == None:
            rv = self.evalPython("topWindowWidgets()")
        elif isinstance(window, int):
            rv = self.evalPython("windowWidgets(%s)" % (repr(window),))
        elif isinstance(window, str) or isinstance(window, unicode):
            wlist = self.evalPython("windowList()")
            for w in wlist:
                if w["title"] == window:
                    rv = self.evalPython("windowWidgets(%s)" % (repr(w["hwnd"]),))
                    break
            else:
                raise ValueError('no window with title "%s"' % (window,))
        else:
            raise ValueError('illegal window "%s", expected integer or string (hWnd or title)' % (window,))
        return rv

    def recvWindowList(self):
        return self.evalPython("windowList()")

    def _window2hwnd(self, window):
        if isinstance(window, str) or isinstance(window, unicode):
            windowList = self.recvWindowList()
            hwndList = [w["hwnd"] for w in windowList if w["title"] == window]
            if not hwndList:
                raise ValueError('no window with title "%s"' % (title,))
            hwnd = hwndList[0]
        elif isinstance(window, int):
            hwnd = window
        else:
            raise ValueError('invalid window "%s", string or integer expected' % (window,))
        return hwnd

    def sendSetForegroundWindow(self, window):
        hwnd = self._window2hwnd(window)
        return 0 != self.evalPython("ctypes.windll.user32.SetForegroundWindow(%s)" %
                                    (repr(hwnd),))

    def sendShowWindow(self, window, showCmd):
        hwnd = self._window2hwnd(window)
        if isinstance(showCmd, str) or isinstance(showCmd, unicode):
            if showCmd in _g_showCmds:
                showCmd = _g_showCmds.index(showCmd)
            else:
                raise ValueError('invalid showCmd: "%s"' % (showCmd,))
        return 0 != self.evalPython("ctypes.windll.user32.ShowWindow(%s, %s)" %
                                    (repr(hwnd), repr(showCmd)))

    def sendType(self, text):
        command = 'sendType(%s)' % (repr(text),)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendPress(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKey("%s",[])' % (keyCode,)
        else:
            command = 'sendKey("%s",%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendKeyDown(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKeyDown("%s",[])' % (keyCode,)
        else:
            command = 'sendKeyDown("%s",%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendKeyUp(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKeyUp("%s",[])' % (keyCode,)
        else:
            command = 'sendKeyUp("%s",%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTap(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTap(%s, %s)" % (x, y)
        else:
            command = "sendClick(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchDown(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchDown(%s, %s)" % (x, y)
        else:
            command = "(sendMouseMove(%s, %s), sendMouseDown(%s))" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchMove(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchMove(%s, %s)" % (x, y)
        else:
            command = "sendMouseMove(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchUp(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchUp(%s, %s)" % (x, y)
        else:
            command = "sendMouseUp(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def setScreenToDisplayCoords(self, screenToDisplayFunction):
        self._screenToDisplay = screenToDisplayFunction

    def setDisplayToScreenCoords(self, displayToScreenFunction):
        self._displayToScreen = displayToScreenFunction

class FMBTWindowsError(Exception): pass
