from documentnode import DocumentNode, attribute
from viewbase import ViewBase
import json
import os, sys
    


magic = 'profile_analyzer_0.0'

def load_model(filename):
    f = open(filename, "rb")
    s = f.read()
    if not s.startswith(magic):
        raise Exception("Unknown file format.")
    else:
        s = s[len(magic):]
    state = json.loads(s)
    model = AnalysisModel()
    model.__setstate__(state)
    return model


class AnalysisModel(DocumentNode):
    zoom = attribute("zoom")
    shift = attribute("shift")
    p1 = attribute("p1")
    p2 = attribute("p2")
    bmp = attribute("bmp")
    foil = attribute("foil")
    
    _zoom = 1.0
    _shift = 0.0
    _pi = 0, 50
    _p2 = 100, 50
    _airfoil = None
    
    def save_as(self, filename):
        state = self.__getstate__()
        s = json.dumps(state, indent=4)
        f = open(filename, 'wb')
        f.write(magic)
        f.write(s)

    def __getstate__(self):
        d = self.__dict__.copy()
        return d

    def __setstate__(self, state):
        self.__dict__.update(state)

    

class TestView(ViewBase):
    def __init__(self):
        self.messages = []
        ViewBase.__init__(self)

    def zoom_changed(self, obj, old):
        #print "zoom changed", obj, old
        self.messages.append([obj, old]) 

        
def test_00():
    "set attributes"
    m = AnalysisModel()
    v = TestView()
    v.set_model(m)
    assert m.zoom == 1.0
    m.zoom = 2.5
    assert len(v.messages) == 1

def test_01():
    "pickle / unpickle"
    m1 = AnalysisModel(igc_filename='../test/aussenlandung_twin.igc')
    import cPickle
    s = cPickle.dumps(m1)
    m2 = cPickle.loads(s)

def test_02():
    "sabe / load"
    m1 = AnalysisModel(igc_filename='../test/aussenlandung_twin.igc')
    m1.save_as("tmp.iga")

    m2 = load_model("tmp.iga")
    
if __name__ == '__main__':
    test_00()
    
