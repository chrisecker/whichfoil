# -*- coding: latin-1 -*-

import wx
import os
import sys
import pkg_resources
try:
    import importlib_resources as resources # py2
except:
    from importlib import resources # py3

from math import pi
from .menu import mk_menu
from .document import AnalysisModel, load_model
from .view import Canvas
from .airfoil import load_airfoil, interpolate_airfoil
from .bindwx import Binder, TextBinder, InvalidValue
from . import foils


DEBUG = False

def _(x): return x



    
class AngleBinder(TextBinder):
    def fromstr(self, s):
        value = s.split()[0]
        try:
            return float(value)
        except ValueError:
            raise InvalidValue(s)

    def tostr(self, value):
        return u"%.1f °" % value


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

    

_airfoils = None
def read_airfoils():
    global _airfoils
    if _airfoils is not None:
        return _airfoils
    d = {}
    # This drives me nuts! Resources in python3.8 does not have "files"!
    if hasattr(resources, 'files'):
        files = resources.files(foils)
        for p in files.iterdir():
            if not p.name.lower().endswith('.dat'):
                continue
            f = p.open(encoding='latin-1')
            comments, (xl, yl) = load_airfoil(f)
            foilname = p.name
            d[foilname] = xl, yl
    else:
        contents = resources.contents(foils)
        for p in contents:
            if not p.lower().endswith('.dat'):
                continue
            f = resources.open_text(foils, p, encoding='latin-1')
            comments, (xl, yl) = load_airfoil(f)
            d[p] = xl, yl
    _airfoils = d
    return d

    
class AirfoilBrowser(wx.Frame):
    def __init__(self, main):
        self.main = main
        self.foils = read_airfoils()
        style=wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, main, style=style, title="Browse airfoils")
        s = wx.BoxSizer(wx.VERTICAL)

        t = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        t.Bind(wx.EVT_TEXT_ENTER, self.on_filter)
        self.t = t
        s.Add(t, 0, wx.EXPAND|wx.ALL, 5)
        
        lb = wx.ListBox(self)
        lb.Bind(wx.EVT_LISTBOX_DCLICK, self.on_load)
        s.Add(lb, 1, wx.EXPAND)
        b = wx.Button(self, label="filter")
        b.Bind(wx.EVT_BUTTON, self.on_filter)
        s.Add(b, 0, wx.EXPAND)

        self.Sizer = s
        self.lb = lb
        self.Show()
        self.on_filter()
        
    def apply_filter(self, pattern):
        r = set()
        pattern = pattern.lower()
        for name, foil in self.foils.items():
            if pattern in name.lower():
                r.add(name)
        self.lb.SetItems(sorted(r))

    def on_filter(self, event=None):
        self.apply_filter(self.t.Value)

    def on_load(self, event):
        i = event.GetSelection()
        name = self.lb.Items[i]
        airfoil = self.foils[name]
        self.main.document.airfoil = name, airfoil


        
class AirfoilMatcher(wx.Frame):
    def __init__(self, main):
        self.main = main
        self.foils = read_airfoils()
        style=wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, main, style=style, title="Match airfoils")
        s = wx.BoxSizer(wx.VERTICAL)
        lb = wx.ListBox(self)
        lb.Bind(wx.EVT_LISTBOX_DCLICK, self.on_load)
        s.Add(lb, 1, wx.EXPAND)
        b = wx.Button(self, label="filter")
        b.Bind(wx.EVT_BUTTON, self.on_filter)
        s.Add(b, 0, wx.EXPAND)

        s2 = wx.BoxSizer(wx.HORIZONTAL)
        l = wx.StaticText(self, label="delta:")
        s2.Add(l, 1, wx.ALL, 5)
        t = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        t.Bind(wx.EVT_TEXT_ENTER, self.on_delta)
        t.Value = "0.01"
        self.t = t
        s2.Add(t, 0, wx.ALL, 5)
        s.Add(s2, 0)         
        self.Sizer = s
        self.lb = lb
        self.Show()
        
    def apply_filter(self, sliders25, sliders50, sliders75, delta=0.005):
        r = set()
        positions = [0.25, 0.5, 0.75]
        sliders = sliders25, sliders50, sliders75
        for name, foil in self.foils.items():
            xv, yv = foil
            ok = True
            for sx, sy in zip(positions, sliders):                
                values = interpolate_airfoil(sx, xv, yv)
                if not values:
                     ok = False
                     break
                y1 = min(values)
                y2 = max(values)
                lower = min(sy)
                upper = max(sy)
                if abs(y1-lower) > delta:
                     ok = False
                     break
                if abs(y2-upper) > delta:
                     ok = False
                     break
            if ok:
                r.add(name)
        self.lb.SetItems(sorted(r))

    def on_filter(self, event):
        delta = float(self.t.Value)
        sliders = self.main.document.sliders
        sliders25 = sliders[0:2]
        sliders50 = sliders[2:4]
        sliders75 = sliders[4:6]
        self.apply_filter(sliders25, sliders50, sliders75, delta)

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
    airfoil_entries = ['open_browser', 'open_matcher']
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
            mk_menu(self, self.airfoil_entries, updaters, accel), '&Airfoil')
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

        l = wx.StaticText(panel, label=_("air foil:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_READONLY)
        sizer2.Add(t)
        self.t_airfoil = t
        
        t = wx.Button(panel, label=u"Match Airfoils")
        t.Bind(wx.EVT_BUTTON, self.open_matcher)
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
        
        if DEBUG:
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

        l = wx.StaticText(panel, label=_("y-scale factor:"))
        sizer2.Add(l)
        t = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer2.Add(t)
        FloatBinder(document, 'yfactor', t)        
        panel.SetSizer(sizer2)
                
        self.SetSizer(sizer)
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

        # update airfoil name
        foil = self.document.airfoil
        if foil is None:
            name = "<None>"
        else:
            name, coordinates = foil
        self.t_airfoil.Value = name

        # update menus
        for updater in self.updaters:
            updater()
        
    def open_matcher(self, event=None):
        "Match airfoils"
        self.matcher = AirfoilMatcher(self)
        # store it for debugging and scripting

    def open_browser(self, event=None):
        "Browse airfoils"
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
            if not os.path.splitext(path)[1]:
                path += '.wfd'
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

    def read_image(self, path):
        s = open(path, "rb").read()
        model = self.document
        model.bmp = s
        # reset canvas
        w, h = self.canvas.bmp.Size
        model.p1 = 0.1*w, 0.5*h
        model.p2 = 0.9*w, 0.5*h
        model.sliders = (0.2, -0.2)*3
        model.mirror = False
        model.scale = 1.0
        model.xshift = 0
        model.yshift = 0
        model.alpha = 0.0
        model.focus = 0.5*w, 0.5*h
        
    def load_image(self):
        "Open image file"
        wildcard = wildcard = "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose an image file",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                self.read_image(path)
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
        m = self.canvas.get_image2window()
        focus_ = m(wx.Point2D(*self.document.focus))
        step = 20.0
        new_ = focus_+(dx*step, dy*step)
        inv = m.Inverted()
        self.document.focus = tuple(inv(new_))

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
        self.document.alpha += 5

    def rotateleft(self):
        "Rotate left\tCtrl-PgUp"
        self.document.alpha -= 5
        
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
            
            

def main():
    app = wx.App(True)
    args = sys.argv[1:]
    if len(args):
        for name in args:
            if name.lower().endswith("wfd"):
                main = MainWindow(filename=name)
            else:
                main = MainWindow()
                main.read_image(name)
            main.Show()
    else:
        main = MainWindow()
        main.Show()
    app.MainLoop()


def test_00():
    app = wx.App(False)
    from .document import AnalysisModel


    main = MainWindow()
    main.Show()

    s = open("test/ah79k135.gif", "rb").read()
    doc = main.document
    doc.bmp = s
    doc.hue = 0.8
    w, h = main.canvas.bmp.Size
    doc.focus = 0.5*w, 0.5*h
    doc.p1 = (148.0, 433.0)
    doc.p2 = (1087.0, 437.0)
    doc.sliders = (0.0885, -0.0361, 0.0940, -0.0351, 0.0513, -0.0224)
    if 0:
        try:
            main.open_notebook(locals())
        except: # ModuleNotFoundError: not available in py2
            pass
    main.open_browser(None)
    app.MainLoop()


def test_01():
    document = load_model("test/clarky.wfd")




    
