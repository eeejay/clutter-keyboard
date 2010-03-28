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
    Svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"> 
  <rect
       style="fill:$fill;fill-opacity:1.0;fill-rule:evenodd;stroke:$stroke;stroke-opacity:1.0;stroke-width:$stroke_width;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none"
       id="highlight"
       width="$width"
       height="$height"
       x="$x"
       y="$y"
       rx="$corner_radius"
       ry="$corner_radius" />
</svg>
"""
    def __init__(self, width, height, label, stroke_width=8):
        clutter.Group.__init__(self)
        if self.__class__.Style == None:
            self._init_style()
        self.label = label
        self.width = width
        self.height = height
        self.stroke_width = stroke_width
        self.state = gtk.STATE_NORMAL

        self.texture = clutter.CairoTexture(width=width, height=height)
        self.text = clutter.Text()
        self.add(self.texture)
        self.add(self.text)

        self.draw_text(label)
        self.draw_bg()

    def _init_style(self):
        w = gtk.Window(gtk.WINDOW_POPUP)
        w.set_name('gtk-button')
        w.ensure_style()
        self.__class__.Style = w.rc_get_style()

    def draw_text(self, label):
        color = self.__class__.Style.fg[self.state]
        self.text.set_font_name("Sans 24")
        self.text.set_color(
            clutter.Color(color.red, color.green, color.blue, 0xff))
        self.text.set_text(label)
        self.text.set_position((self.width - self.text.get_width() - 5)/2,
                               (self.height - self.text.get_height() - 15)/2)

    def draw_bg(self):
        s = self.__class__.Style
        svg = string.Template(self.Svg).substitute(
            x = self.stroke_width/2.0, y=self.stroke_width/2.0,
            width=self.width - self.stroke_width, 
            height=self.height - self.stroke_width,
            fill=s.bg[self.state], 
            stroke_width=self.stroke_width,
            stroke=s.fg[self.state],
            corner_radius=self.stroke_width*2)

        svgh = rsvg.Handle()
        svgh.write (svg)
        svgh.close()

        self.texture.set_size(self.width, self.height)

        cr = self.texture.cairo_create()
        #cr.scale(self.width, self.height)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.paint()
        svgh.render_cairo(cr)

        del svgh
        del cr

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

    for row in qwerty.lowercase:
        trow = []
        for k in row:
            if isinstance(k, tuple):
                k = k[0]

            rect = KeyboardButton(maxw + 10, maxh + 10, k)
            rect.set_property("anchor-gravity", clutter.GRAVITY_CENTER)
            rect.set_property("scale-x", 0.5)
            rect.set_property("scale-y", 0.5)

            rect.set_position(offsetx + maxw/2 + 5, offsety + maxh/2 + 5)

            rect.set_reactive (True)
            rect.connect('enter-event', _on_enter)
            rect.connect('leave-event', _on_leave)
            rect.connect("button-press-event", _on_press, k)

            rect.show_all()
            stage.add(rect)

            offsetx += maxw/2 + 12

        if offsetx - 2> kbw:
            kbw = offsetx - 2
        offsety += maxh/2 + 11
        offsetx = 0
        
    kbh = offsety - 2

    clutter_widget.set_size_request(kbw + 52, kbh + 52)

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
