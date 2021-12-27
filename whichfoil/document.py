import json
import os
import sys
from .documentnode import DocumentNode, attribute
from .viewbase import ViewBase
    


magic = 'profile_analyzer_0.0'

def load_model(filename):
    f = open(filename, "r")
    s = f.read()
    if not s.startswith(magic):
        raise Exception("Unknown file format.")
    else:
        s = s[len(magic):]
    state = json.loads(s)
    if '_bmp' in state:
        # XXX python 3 only!!
        state['_bmp'] = bytes(state['_bmp'], 'latin-1')
    model = AnalysisModel()
    model.__setstate__(state)
    return model


class AnalysisModel(DocumentNode):
    alpha = attribute("alpha")
    zoom = attribute("zoom")
    #shift = attribute("shift")
    p1 = attribute("p1")
    p2 = attribute("p2")
    upper = attribute("upper")
    lower = attribute("lower")
    bmp = attribute("bmp") # imagefile bytes array (py3) or string
    airfoil = attribute("airfoil")
    yfactor = attribute("yfactor")
    focus = attribute("focus")
    xshift = attribute("xshift")
    yshift = attribute("yshift")
    mirror = attribute("mirror")
    hue = attribute("hue")
    transparency = attribute("transparency")

    _alpha = 0.0
    _zoom = 1.0
    _focus = 50, 50
    _xshift = 0.0
    _yshift = 0.0
    _mirror = False
    _hue = 0.5
    _transparency = 1.0
    _p1 = 0, 50
    _p2 = 100, 50
    _lower = 0.2
    _upper = 0.2
    _bmp = None
    _airfoil = None
    _yfactor = 1.0
    
    
    def save_as(self, filename):
        state = self.__getstate__()
        bmp = self.bmp
        if bmp is not None:
            state['_bmp'] = bmp.decode('latin-1')
        s = json.dumps(state, indent=4)
        f = open(filename, 'w')
        f.write(magic)
        f.write(s)

    def __getstate__(self):
        d = self.__dict__.copy()
        return d

    def __setstate__(self, state):
        airfoil = state.get('_airfoil')
        if airfoil:
            try:
                name, (xv, yv) = airfoil
            except:
                # XXX Hack to allow reading old files
                xv, yv = airfoil 
                name = "<unnamed>"
            state['_airfoil'] = name, (xv, yv)
        self.__dict__.update(state)

    

class TestView(ViewBase):
    def __init__(self):
        self.messages = []
        ViewBase.__init__(self)

    def zoom_changed(self, obj, old):
        self.messages.append([obj, old]) 

        
def test_00():
    "set attributes"
    m = AnalysisModel()
    v = TestView()
    v.set_model(m)
    assert m.zoom == 1.0
    m.zoom = 2.5
    assert len(v.messages) == 1

def xxxtest_01():
    "pickle / unpickle"
    m1 = AnalysisModel()
    import cPickle
    s = cPickle.dumps(m1)
    m2 = cPickle.loads(s)

def test_02():
    "save / load"
    m1 = AnalysisModel()
    s = open("test/ah79k135.gif", "rb").read()
    m1.bmp = s

    m1.save_as("tmp.wpf")

    m2 = load_model("tmp.wpf")
    assert m2.bmp == m1.bmp

    
if __name__ == '__main__':
    test_00()
    
