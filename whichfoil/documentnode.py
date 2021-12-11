from model import Model, overridable_property
from weakref import WeakKeyDictionary


class Owners:
    def __init__(self):
        self._data = WeakKeyDictionary()

    def add_owner(self, obj, owner, name):
        try:
            d = self._data[obj]
        except KeyError:
            d = WeakKeyDictionary()
            self._data[obj] = d
        try:
            d[owner].append(name)
        except KeyError:
            d[owner] = [name]

    def remove_owner(self, obj, owner, name):
        d = self._data[obj]
        d[owner].remove(name)
        if not d[owner]:
            del d[owner]

    def get_owners(self, obj):
        try:
            return self._data[obj].keys()
        except KeyError:
            return ()

    def get_owner_attributes(self, obj):
        try:
            d = self._data[obj]
        except KeyError:
            return ()
        r = []
        for owner, names in d.items():
            for name in names:
                r.append((owner, name))
        return r
        

OWNERS = Owners()

def attribute(name, doc=""):
    return property(
        lambda self:self.get_attribute(name),
        lambda self, value:self.set_attribute(name, value),
        None,
        doc)


class DocumentNode(Model):
    owners = overridable_property('owners', 
        "List of owners.")
    owner_attributes = overridable_property('owner_attributes', 
        "List of tuples (owner, attribute name).")
    
    def notify_owners(self):
        # notify owners and their views that this object has been
        # modified
        for owner, name in self.get_owner_attributes():
            msg = name+'_modified'
            self._call_if_present(owner, msg, self)
            for view in owner.views:
                self._call_if_present(view, msg, owner)                
            
    def get_owners(self):
        return OWNERS.get_owners(self)

    def get_owner_attributes(self):
        return OWNERS.get_owner_attributes(self)
    
    def get_attribute(self, name):
        return getattr(self, '_'+name, None)

    def set_attribute(self, name, value):
        old = getattr(self, '_'+name, None)
        if old == value:
            return
        if isinstance(old, DocumentNode):
            OWNERS.remove_owner(old, self, name)
        if isinstance(value, DocumentNode):
            OWNERS.add_owner(value, self, name)
        if hasattr(self, "set_"+name):
            getattr(self, "set_"+name)(value)
        else:
            setattr(self, '_'+name, value)
        # notify views that attribute changed
        self.notify_views(name+'_changed', old)
        self.notify_owners()
        
            

def test_00():
    from viewbase import ViewBase
    
    class Child(DocumentNode):
        a = attribute("a")
        
    class Document(DocumentNode):
        child = attribute("child")

    class DocView(ViewBase):
        
        def child_changed(self, *args):
            self.msg = "changed", args

        def child_modified(self, *args):
            self.msg = "modified", args

            
    doc = Document()
    view = DocView()
    view.set_model(doc)
    doc.child = child = Child()
    assert view.msg == ('changed', (doc, None))
    
    assert doc.child.owner_attributes == [(doc, 'child')]
    doc.child.notify_owners()
    assert view.msg == ('modified', (doc, ))

    doc.child = None
    assert child.owners == []
    assert child.owner_attributes == []
    assert view.msg == ('changed', (doc, child))

    
if __name__ == '__main__':
    test_00()
