#
#		Python GUI - View Base - Generic
#

from .properties import overridable_property


class ViewBase(object):
    """ViewBase is an abstract base class for user-defined views.
    It provides facilities for handling mouse and keyboard events
    and associating the view with one or more models, and default
    behaviour for responding to changes in the models."""

    models = overridable_property('models',
        "List of Models being observed. Do not modify directly.")
    
    model = overridable_property('model',
        "Convenience property for views which observe only one Model.")


    def __init__(self):
        self._models = []

    def destroy(self):
        #print "GViewBase.destroy:", self ###
        for m in self._models[:]:
            #print "GViewBase.destroy: removing model", m ###
            self.remove_model(m)
    
    def get_model(self):
        models = self._models
        if models:
            return self._models[0]
        else:
            return None

    def get_models(self):
        return self._models

    #
    #		Setting properties
    #

    def set_model(self, new_model):
        models = self._models
        if not (len(models) == 1 and models[0] == new_model):
            for old_model in models[:]:
                self.remove_model(old_model)
            if new_model is not None:
                self.add_model(new_model)

    #
    #   Model association
    #
    
    def add_model(self, model):
        """Add the given Model to the set of models being observed."""
        if model not in self._models:
            self._models.append(model)
            add_view = getattr(model, 'add_view', None)
            if add_view:
                add_view(self)
            self.model_added(model)
    
    def remove_model(self, model):
        """Remove the given Model from the set of models being observed."""
        if model in self._models:
            self._models.remove(model)
            remove_view = getattr(model, 'remove_view', None)
            if remove_view:
                remove_view(self)
            self.model_removed(model)
    
    def model_added(self, model):
        """Called after a model has been added to the view."""
        pass

    def model_removed(self, model):
        """Called after a model has been removed from the view."""
        pass


    #
    #		Callbacks
    #

    def model_changed(self, model, *args, **kwds):
        pass

    def model_destroyed(self, model):
        pass

