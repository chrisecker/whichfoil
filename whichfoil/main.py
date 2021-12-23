# -*- coding: latin-1 -*-

import wx
import os
from math import pi

from .menu import mk_menu
from .document import AnalysisModel, load_model
from .view import Canvas, load_airfoil

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
        #return u"%.1f" % value
    

class AirfoilBrowser(wx.Frame):
    path = "/home/ecker/foils" # XXX
    def __init__(self, main):
        self.main = main
        self.read_foils()
        wx.Frame.__init__(self, None)
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
                
    def on_load(self, event):
        i = event.GetSelection()
        name = self.lb.Items[i]
        airfoil = self.foils[name]
        self.main.document.airfoil = name, airfoil
        
    
class MainWindow(wx.Frame):
    file_entries = ['new', 'open', 'save', 'save_as', 'load_image', 'close']
    _filename = None
    def __init__(self, filename=None):
        wx.Frame.__init__(self, None, size=(800, 600))
        #self.Bind(wx.EVT_CLOSE, self.on_exit)
        updaters = []
        accel = []
        menubar = wx.MenuBar()
        menubar.Append(
            mk_menu(self, self.file_entries, updaters, accel), '&File')
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
        
        sizer.Add(canvas, 1, wx.EXPAND)

        panel = wx.Panel(self)
        panel.MinSize=(100, -1)
        sizer.Add(panel, 0, wx.EXPAND)

        sizer2 = wx.BoxSizer(wx.VERTICAL)

        t = wx.Button(panel, label=u"Browse Airfoils")
        t.Bind(wx.EVT_BUTTON, self.on_browser)
        sizer2.Add(t)
        
        t = wx.Button(panel, label=u"Mirror")
        t.Bind(wx.EVT_BUTTON, self.on_mirror)
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

        l = wx.StaticText(panel, label=_("xshift:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'xshift', t)

        l = wx.StaticText(panel, label=_("yshift:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'yshift', t)

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

    def on_browser(self, event):
        self.browser = AirfoilBrowser(self)
        print("stored browser in", self)
        # store it for debugging and scripting
    
    def on_mirror(self, event):
        self.document.mirror = not self.document.mirror

    def new(self):
        "New Window"
        f = MainWindow(None)
        f.Show()
    
    def open(self):
        "Open WFD file"
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
        dlg.Destroy()        


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
    doc.hue = 0.3
    #canvas.shift = 100, 0

    

    from . import testing
    testing.pyshell(locals())
    app.MainLoop()
