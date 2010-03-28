import sys

import cluttergtk   # must be the first to be imported
import clutter
import gtk
import qwerty
import glib
import rsvg
import string
import cairo
from math import sqrt

ROUNDED_RECT = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"> 
  <rect
       style="fill:$fill;fill-opacity:$fill_opacity;fill-rule:evenodd;stroke:$stroke;stroke-opacity:$stroke_opacity;stroke-width:$stroke_width;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none"
       id="highlight"
       width="$width"
       height="$height"
       x="$x"
       y="$y"
       rx="$corner_radius"
       ry="$corner_radius" />
</svg>
"""

already_changed = False
stage = None

class KeyboardButton(clutter.Group):
    Style = None
    FontDesc = None
    def __init__(self, label, border_width=4, padding=10):
        clutter.Group.__init__(self)
        if self.__class__.Style == None:
            self._init_style()
        self.label = label
        self.stroke_width = border_width
        self.padding = padding
        self.state = gtk.STATE_NORMAL

        self.text = clutter.Text()
        w, h = self.draw_text(self.label)

        self.set_properties(min_width=w + self.padding*2,
                            min_height=h + self.padding*2)

        self.texture = None

        self.connect('realize', self._on_realized)

    def _on_realized(self, button):
        width, height = self.get_size()

        self.texture = clutter.CairoTexture(
            width=int(width), height=int(height))
        self.draw_bg()

        self.add(self.texture)
        self.add(self.text)


    def _init_style(self):
        w = gtk.Window(gtk.WINDOW_POPUP)
        w.set_name('gtk-button')
        w.ensure_style()
        self.__class__.Style = w.rc_get_style()
        self.__class__.FontDesc = self.__class__.Style.font_desc.copy()
        self.__class__.FontDesc.set_size(self.__class__.FontDesc.get_size()*2)

    def set_size(self, w, h):
        clutter.Group.set_size(self, w, h)
        if self.texture:
            self.texture.set_size(w, h)
        if self.text:
            tw, th = self.text.get_size()
            x, y = self.get_position()
            self.text.set_position(x + (w - tw)/2, y + (h - th)/2)

    def draw_text(self, label):
        color = self.__class__.Style.fg[self.state]
        width, height = self.get_size()
        self.text.set_font_name(self.FontDesc.to_string())
        self.text.set_color(
            clutter.Color(color.red, color.green, color.blue, 0xff))
        self.text.set_text(label)
        return self.text.get_size()

    def draw_bg(self):
        width, height = self.get_size()
        s = self.__class__.Style
        svg = string.Template(ROUNDED_RECT).substitute(
            x = self.stroke_width/2.0, y=self.stroke_width/2.0,
            width=width - self.stroke_width, 
            height=height - self.stroke_width,
            fill=s.bg[self.state], 
            stroke_width=self.stroke_width,
            stroke=s.fg[self.state],
            corner_radius=self.stroke_width*2,
            fill_opacity=0.85,
            stroke_opacity=0.9)

        svgh = rsvg.Handle()
        svgh.write (svg)
        svgh.close()

        self.texture.set_size(width, height)

        cr = self.texture.cairo_create()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.paint()
        svgh.render_cairo(cr)

        del svgh
        del cr

class Keyboard(clutter.Group):
    def __init__(self, spacing=4):
        clutter.Group.__init__(self)
        self._rows = []
        self._max_row_len = 0
        self._max_dimension = 0
        self.spacing = spacing
        self.connect('realize', self._realize_cb)
        
    def _realize_cb(self, kb):
        for i, row in enumerate(self._rows):
            vspace = i*self.spacing
            for r, k in enumerate(row):
                hspace = r*self.spacing
                k.set_size(self._max_dimension, self._max_dimension)
                k.set_position(
                    self._max_dimension/2 + r*self._max_dimension/2 + hspace,
                    self._max_dimension/2 + i*self._max_dimension/2 + vspace)

    def add_key(self, row_index, key):
        if isinstance(key, tuple):
            key, val = key
        else:
            val = key

        keybutton = KeyboardButton(key)
        keybutton.set_properties(anchor_gravity=clutter.GRAVITY_CENTER,
                                 scale_x=0.5, scale_y=0.5)

        if row_index < 0 or row_index >= len(self._rows):
            self._rows.append([keybutton])
        else:
            self._rows[row_index].append(keybutton)
        
        min_d = max(*keybutton.get_properties("min-width", "min-height"))
        if min_d > self._max_dimension:
            self._max_dimension = min_d

        self.add(keybutton)

        self.connect_key_signals(keybutton, val)

        return keybutton

    def connect_key_signals(self, keybutton, value):
        keybutton.set_reactive (True)
        keybutton.connect("button-press-event", self._on_press, value)

class ProximityKeyboard(Keyboard):
    def connect_key_signals(self, keybutton, value):
        Keyboard.connect_key_signals(self, keybutton, value)
        keybutton.connect('enter-event', self._on_enter)
        keybutton.connect('leave-event', self._on_leave)
        keybutton.connect('motion-event', self._on_motion)

    def _on_motion(self, button, event):
        bx, by =  button.get_position()
        distance = sqrt((event.x - bx)**2 + (event.y - by)**2)
        button.set_properties(scale_x=max((distance - 50)/-40, 0.5),
                              scale_y=max((distance - 50)/-40, 0.5))

    def _on_enter(self, button, event):
        button.set_property("depth", 1)

    def _on_press(self, button, event, char):
        print char

    def _on_leave(self, button, event):
        button.set_properties(scale_x=0.5, scale_y=0.5)
        button.set_property("depth", 0)

    

class BouncyKeyboard(Keyboard):
    def connect_key_signals(self, keybutton, value):
        Keyboard.connect_key_signals(self, keybutton, value)
        keybutton.connect('enter-event', self._on_enter)
        keybutton.connect('leave-event', self._on_leave)

    def _on_enter(self, button, event):
        self._scale_button (button)

    def _on_press(self, button, event, char):
        print char

    def _on_leave(self, button, event):
        self._scale_button (button, True)

    def _scale_button(self, b, reverse=False):
        if reverse:
            scale = 0.5
        else:
            scale = 1

        if reverse:
            b.set_property("depth", 1)
        else:
            b.set_property("depth", 2)

        a = b.animate(clutter.EASE_OUT_ELASTIC, 300, 
                      "scale-x", scale,
                      "scale-y", scale)
        if reverse:
            a.connect_after('completed', self._on_complete, b)

    def _on_complete(self, animation, b):
        b.set_property("depth", 0)

class Main(object):
    def __init__(self, keyboard_cls):
        self.window =  gtk.Window()
        clutter_widget = cluttergtk.Embed()
        self.window.add(clutter_widget)
        clutter_widget.show()

        self.stage = clutter_widget.get_stage()
        self.stage.set_color(clutter.Color(0x20, 0x4a, 0x87, 0x00))
        if not clutter.__version__.startswith('1.0'):
            self.stage.set_property('use-alpha', True)
        
        self.stage.show_all()


        self.keyboard = keyboard_cls()

        self._populate_keyboard(qwerty.lowercase)

        self.stage.add(self.keyboard)

        clutter_widget.set_size_request(*map(int,(self.keyboard.get_size())))

        # Show the window
        self.window.show()

        
    def start(self):
        gtk.main()

    def _populate_keyboard(self, layout):
        for i, row in enumerate(layout):
            for k in row:                                
                keybutton = self.keyboard.add_key(i, k)

        self.keyboard.show_all()

if __name__ == '__main__':
    if "proximity" in sys.argv[1:]:
        keyboard = ProximityKeyboard
    elif "bouncy" in sys.argv[1:]:
        keyboard = BouncyKeyboard
    else:
        print "usage: %s %s|%s <options>" % \
            (sys.argv[0], "proximity", "bouncy")
        sys.exit(1)

    m = Main(keyboard)
    m.start()
