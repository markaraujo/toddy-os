"""Use the actual introspectable ValueObject.new(GValue) constructor."""
import gi,json
gi.require_version('Handy','1')
from gi.repository import Handy,GObject
v=GObject.Value();v.init(GObject.TYPE_STRING);v.set_string('Toddy ã')
obj=Handy.ValueObject.new(v);v.set_string('changed')
assert obj.get_string()=='Toddy ã' and obj.dup_string()=='Toddy ã'
print(json.dumps({'namespace':'Handy1','UTF8_value_object':True,'widget_or_display_tested':False}))
