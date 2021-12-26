# -*- coding: latin-1 -*-

import wx
import os
from math import pi

from .menu import mk_menu
from .document import AnalysisModel, load_model
from .view import Canvas
from .airfoil import load_airfoil
from .bindwx import Binder, TextBinder, InvalidValue

def _(x): return x


class AngleBinder(TextBinder):
    def fromstr(self, s):
        value = s.split()[0]
        try:
            return float(value)*pi/180.0
        except ValueError:
            raise InvalidValue(s)

    def tostr(self, value):
        return u"%.1f °" % (value*180.0/pi)


class FloatBinder(TextBinder):
    def fromstr(self, s):
        value = s.split()[0]
        try:
            return float(value)
        except ValueError:
            raise InvalidValue(s)

    def tostr(self, value):
        return str(value)


class VectorBinder(Binder):
    def __init__(self, model, attrname, widget1, widget2):
        self.widget1 = widget1
        self.widget2 = widget2
        Binder.__init__(self, model, attrname, widget1)
        for widget in (widget1, widget2):
            widget.Bind(wx.EVT_TEXT_ENTER, self.check_widget)
            widget.Bind(wx.EVT_KILL_FOCUS, self.check_widget)

    def get_widget_state(self):
        return self.widget1.Value, self.widget2.Value

    def set_widget_value(self, value):
        self.widget1.Value = u"%.1f" % value[0]
        self.widget2.Value = u"%.1f" % value[1]

    def get_widget_value(self):
        s1, s2 = self.get_widget_state()
        try:
            x = float(s1)
            y = float(s2)
        except ValueError:
            raise InvalidValue((s1, s2))
        return x, y

    
class AirfoilBrowser(wx.Frame):
    path = "/home/ecker/foils" # XXX
    def __init__(self, main):
        self.main = main
        self.read_foils()
        style=wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE#| wx.FRAME_TOOL_WINDOW
        wx.Frame.__init__(self, main, style=style, title="Air foil browser")
        s = wx.BoxSizer(wx.VERTICAL)
        lb = wx.ListBox(self)
        lb.Bind(wx.EVT_LISTBOX_DCLICK, self.on_load)
        s.Add(lb, 1, wx.EXPAND)
        #b = wx.Button(self, label="load")
        #b.Bind(wx.EVT_BUTTON, self.on_load)
        #s.Add(b, 0, wx.EXPAND)
        b = wx.Button(self, label="filter")
        b.Bind(wx.EVT_BUTTON, self.on_filter)
        s.Add(b, 0, wx.EXPAND)

        s2 = wx.BoxSizer(wx.HORIZONTAL)
        l = wx.StaticText(self, label="delta:")
        s2.Add(l, 1, wx.ALL, 5)
        t = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        t.Bind(wx.EVT_TEXT_ENTER, self.on_delta)
        t.Value = "0.005"
        self.t = t
        s2.Add(t, 0, wx.ALL, 5)
        s.Add(s2, 0)         
        self.Sizer = s
        self.lb = lb
        self.Show()
        
    def read_foils(self):
        foils = {}
        import os
        for name in os.listdir(self.path):
            p = os.path.join(self.path, name)
            foilname = os.path.splitext(name)[0]
            xl, yl = load_airfoil(p)
            foils[foilname] = xl, yl
        self.foils = foils

    def apply_filter(self, upper, lower, delta=0.005):
        r = set()
        for name, foil in self.foils.items():
            y1 = min(foil[1])
            y2 = max(foil[1])
            if abs(y1+lower) > delta:
                 continue
            if abs(y2-upper) > delta:
                 continue
            r.add(name)
        self.lb.SetItems(sorted(r))

    def on_filter(self, event):
        delta = float(self.t.Value)
        upper = self.main.document.upper
        lower = self.main.document.lower
        self.apply_filter(upper, lower, delta)

    def on_delta(self, event):
        t = self.t
        try:
            delta = float(t.Value)
        except:
            delta = 0.0
        if delta<=0:
            delta = 0.0
        t.Value = str(delta)
        self.on_filter(None)
                
    def on_load(self, event):
        i = event.GetSelection()
        name = self.lb.Items[i]
        airfoil = self.foils[name]
        self.main.document.airfoil = name, airfoil
        
    
class MainWindow(wx.Frame):
    file_entries = ['new', 'open', 'save', 'save_as', 'close']
    image_entries = ['load_image', 'flip_image']
    view_entries = ['zoomin', 'zoomout', 'moveleft', 'moveright', 'moveup', 'movedown',
                    'rotateleft', 'rotateright']
    debug_entries = ['open_notebook', 'open_shell']

    _filename = None
    def __init__(self, filename=None):
        wx.Frame.__init__(self, None, size=(800, 600))
        #self.Bind(wx.EVT_CLOSE, self.on_exit)
        updaters = []
        accel = []
        menubar = wx.MenuBar()
        menubar.Append(
            mk_menu(self, self.file_entries, updaters, accel), '&File')
        menubar.Append(
            mk_menu(self, self.image_entries, updaters, accel), '&Image')
        menubar.Append(
            mk_menu(self, self.view_entries, updaters, accel), '&View')
        menubar.Append(
            mk_menu(self, self.debug_entries, updaters, accel), '&Debug')
        self.SetMenuBar(menubar)
        self.updaters = updaters
        #self.SetAcceleratorTable(wx.AcceleratorTable(accel))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        if filename is not None:
            document = load_model(filename)
            self._filename = filename
        else:
            document = AnalysisModel()
        self.document = document
        #appcontext.document = document

        self.canvas = canvas = Canvas(self)
        canvas.set_model(document)
        self.canvas.Bind(wx.EVT_CHAR, self.on_char)
        
        sizer.Add(canvas, 1, wx.EXPAND)

        panel = wx.Panel(self)
        panel.MinSize=(100, -1)
        sizer.Add(panel, 0, wx.EXPAND)

        sizer2 = wx.BoxSizer(wx.VERTICAL)

        t = wx.Button(panel, label=u"Browse Airfoils")
        t.Bind(wx.EVT_BUTTON, self.on_browser)
        sizer2.Add(t)
        
        l = wx.StaticText(panel, label=_("hue:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'hue', t)
        
        l = wx.StaticText(panel, label=_("angle:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        AngleBinder(document, 'alpha', t)
        
        l = wx.StaticText(panel, label=_("zoom:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'zoom', t)

        l = wx.StaticText(panel, label=_("x-focus:"))
        sizer2.Add(l)
        tx = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(tx)
        l = wx.StaticText(panel, label=_("y-focus:"))
        sizer2.Add(l)
        ty = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(ty)        
        VectorBinder(document, 'focus', tx, ty)

        l = wx.StaticText(panel, label=_("upper camber:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'upper', t)

        l = wx.StaticText(panel, label=_("lower camber:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'lower', t)
        
        panel.SetSizer(sizer2)
        
        
        self.SetSizer(sizer)
        #sizer2.Fit(self)
        #self.Layout()
        self.Bind(wx.EVT_IDLE, self.update)
        self.SetFocus()


    def update(self, event):
        # update filename in window title
        if self._filename:
            path, name = os.path.split(self._filename)
            title = name
        else:
            title = '<unnamed>'
        #if self.changed():
        #    title = title+' *'
        self.SetTitle(title)

        # update menus
        for updater in self.updaters:
            updater()
        
    def on_browser(self, event):
        self.browser = AirfoilBrowser(self)
        # store it for debugging and scripting
    
    def new(self):
        "New Window"
        f = MainWindow(None)
        f.Show()
    
    def open(self):
        "Open WFD file\tCtrl+o"
        wildcard = "WFD files (*.wfd)|*.wfd|" \
                   "All files (*.*)|*.*"

        dlg = wx.FileDialog(
            self, message="Choose a file",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                f = MainWindow(path)
                f.Show()
        dlg.Destroy()

    def _save_as(self, filename):
        # save & set filename
        self.document.save_as(filename)
        self._filename = filename

    def can_save(self):
        return self._filename is not None
    
    def save(self):
        "Save analysis\tCtrl-s"
        self._save_as(self._filename)
    
    def save_as(self):
        "Save analysis as ..." #\tCtrl-Shift-S"
        wildcard = "WFD files (*.wfd)|*.wfd|" \
                   "All files (*.*)|*.*"        
        dlg = wx.FileDialog(
            self, message="Save as ...", 
            defaultFile="", wildcard=wildcard, 
            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._save_as(path)
            self._filename = path
        dlg.Destroy()        
        
    def close(self, event=None):
        "&Close\tCtrl-W"
        if 0: #self.changed():
            dlg = wx.MessageDialog(
                self, 'There are unsaved changes. Do you really want to close?',
                'Close window',
                wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
            )
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_YES:
                return            
        self.Close(True)

    def load_image(self):
        "Open image file"
        wildcard = wildcard = "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose an image file",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            model = self.document
            for path in dlg.GetPaths():
                s = open(path, "rb").read()
                model.bmp = s
            # reset canvas
            w, h = self.canvas.bmp.Size
            model.p1 = 0.1*w, 0.5*h
            model.p2 = 0.9*w, 0.5*h
            model.upper = 0.1 # upper camber 
            model.lower = 0.1 # lower camber
            model.mirror = False
            model.scale = 1.0
            model.xshift = 0
            model.yshift = 0
            model.alpha = 0.0
            model.focus = 0.5*w, 0.5*h
        dlg.Destroy()

    def flip_image(self):
        "Flip image horizontally"
        self.document.mirror = not self.document.mirror

    def open_notebook(self, namespace=None):
        "Open notebook"
        from .shelltool import ShellTool
        if namespace is None:
            namespace = dict(main=self)
        tool = ShellTool(self)
        tool.Show()
        tool.namespace.update(namespace)
        
    def open_shell(self, namespace=None):
        "Open shell"
        from .testing import pyshell
        if namespace is None:
            namespace = dict(main=self)
        pyshell(namespace)

    def zoomin(self):
        "Zoom in\tCtrl-+"
        self.document.zoom *= 1.5

    def zoomout(self):
        "Zoom out\tCtrl--"
        self.document.zoom /= 1.5

    def moveview(self, dx, dy):
        zoom = self.document.zoom
        x, y = self.document.focus
        step = 20.0/zoom
        self.document.focus = x+dx*step, y+dy*step

    def moveleft(self):
        "Move left\tCtrl-left"
        self.moveview(-1, 0)
        
    def moveright(self):
        "Move right\tCtrl-right"
        self.moveview(1, 0)

    def moveup(self):
        "Move up\tCtrl-up"
        self.moveview(0, -1)
        
    def movedown(self):
        "Move down\tCtrl-down"
        self.moveview(0, 1)

    def rotateright(self):
        "Rotate right\tCtrl-PgDn"
        deg = pi/180.0
        self.document.alpha += 5*deg

    def rotateleft(self):
        "Rotate left\tCtrl-PgUp"
        deg = pi/180.0
        self.document.alpha -= 5*deg
        
    def on_char(self, event):
        # Accelaretors from the menu do not work reliably. Here we
        # handle keys for scrolling on our own.
        keycode = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        alt = event.AltDown()
        #print(keycode)
        if ctrl and not shift and not alt:
            if keycode == 314:
                self.moveleft()
            elif keycode == 315:
                self.moveup()
            elif keycode == 316:
                self.moveright()
            elif keycode == 317:
                self.movedown()
            elif keycode == 366: # pgup
                self.rotateleft()
            elif keycode == 367: # pgdown
                self.rotateright()
            else:
                event.Skip()
        else:
                event.Skip()
            
            



def test_00():
    app = wx.App(True)
    from .document import AnalysisModel
    main = MainWindow()
    main.Show()


    #canvas.transient = (50, 50)
    #canvas.zoom = 2
    #canvas.p1 = 10, 100
    #canvas.p2 = 500, 100
    main.document.airfoil = "ag03", load_airfoil("foils/ah79k135-il.dat") # ag03.dat
    s = open("test/ah79k135.gif", "rb").read()
    doc = main.document
    doc.bmp = s
    doc.upper = 0.09859762675296653
    doc.lower = 0.03926645091693633
    doc.hue = 0.8
    w, h = main.canvas.bmp.Size
    doc.focus = 0.5*w, 0.5*h

    #canvas.shift = 100, 0

    try:
        main.open_notebook(locals())
    except ModuleNotFoundError:
        pass
    app.MainLoop()
