import sys

import cluttergtk   # must be the first to be imported
import clutter
import gtk
import qwerty
import glib
import rsvg
import string
import cairo

SCALE = 1.0

already_changed = False
stage = None

class KeyboardButton(clutter.Group):
    Style = None
    FontDesc = None
    Svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
    def __init__(self, label, border_width=8, padding=20):
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
        self.__class__.FontDesc.set_size(self.__class__.FontDesc.get_size()*4)

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
        svg = string.Template(self.Svg).substitute(
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
    def __init__(self):
        clutter.Group.__init__(self)
        self._rows = []
        self._max_row_len = 0
        self._max_dimension = 0
        self.connect('realize', self._realize_cb)
        
    def _realize_cb(self, kb):
        for i, row in enumerate(self._rows):
            for r, k in enumerate(row):
                k.set_size(self._max_dimension, self._max_dimension)
                k.set_position(self._max_dimension/2 + r*self._max_dimension/2,
                               self._max_dimension/2 + i*self._max_dimension/2)

    def add_key(self, row_index, key):
        if row_index < 0 or row_index >= len(self._rows):
            self._rows.append([key])
        else:
            self._rows[row_index].append(key)
        
        min_d = max(*key.get_properties("min-width", "min-height"))
        if min_d > self._max_dimension:
            self._max_dimension = min_d

        self.add(key)
    
def main ():
    global stage

    stage_color = clutter.Color(0, 0, 0, 255) # Black

    # Create the window and add some child widgets
    window = gtk.Window(gtk.WINDOW_POPUP)

    colormap = window.get_screen().get_rgba_colormap()
    window.set_colormap(colormap)

    # Stop the application when the window is closed
    window.connect('hide', gtk.main_quit)

    # Create the clutter widget
    clutter_widget = cluttergtk.Embed()
    window.add(clutter_widget)
    clutter_widget.show()

    # Set the size of the widget,
    # because we should not set the size of its stage when using GtkClutterEmbed.
    # Get the stage and set its size and color
    stage = clutter_widget.get_stage()
    stage.set_color(clutter.Color(0x20, 0x4a, 0x87, 0x00))
    if not clutter.__version__.startswith('1.0'):
        stage.set_property('use-alpha', True)


    # Show the stage
    stage.show()

    maxw, maxh = 100, 100

    offsetx, offsety = 1, 1

    kbw, kbh = 0, 0

    kb = Keyboard()

    for i, row in enumerate(qwerty.lowercase):
        trow = []
        for k in row:
            if isinstance(k, tuple):
                k = k[0]

            rect = KeyboardButton(k)
            rect.set_property("anchor-gravity", clutter.GRAVITY_CENTER)
            rect.set_property("scale-x", 0.5)
            rect.set_property("scale-y", 0.5)

            rect.set_reactive (True)
            rect.connect('enter-event', _on_enter)
            rect.connect('leave-event', _on_leave)
            rect.connect("button-press-event", _on_press, k)

            rect.show_all()
            
            kb.add_key(i, rect)

            offsetx += maxw/2 + 12

        if offsetx - 2> kbw:
            kbw = offsetx - 2
        offsety += maxh/2 + 11
        offsetx = 0
        
    stage.add(kb)

    kbh = offsety - 2

    print kbw + 52, kbh + 52
    print kb.get_size()

    clutter_widget.set_size_request(*map(int,(kb.get_size())))

    # Show the window
    window.show()

    # Start the main loop, so we can respond to events:
    gtk.main()

    return 0


def _on_enter(button, event):
    scale_button (button)

def _on_press(button, event, char):
    print char

def _on_leave(button, event):
    scale_button (button, True)

def scale_button(b, reverse=False):
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
        a.connect_after('completed', _on_complete, b)

def _on_complete(animation, b):
    b.set_property("depth", 0)

if __name__ == '__main__':
    sys.exit(main())
