import sys

import cluttergtk   # must be the first to be imported
import clutter
import gtk
import qwerty
import glib

SCALE = 1.0

already_changed = False
stage = None


def on_button_clicked(button):
    global already_changed, stage

    if already_changed:
        stage_color = clutter.Color(0, 0, 0, 255) # Black
        stage.set_color(stage_color)
    else:
        stage_color = clutter.Color(32, 32, 160, 255)
        stage.set_color(stage_color)

    already_changed = not already_changed

    return True # Stop further handling of this event


def on_stage_button_press(stage, event):
    print "Stage clicked at (%f, %f)" % (event.x, event.y)

    return True # Stop further handling of this event


def main ():
    global stage

    stage_color = clutter.Color(0, 0, 0, 255) # Black

    # Create the window and add some child widgets
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)

    # Stop the application when the window is closed
    window.connect('hide', gtk.main_quit)

    # Create the clutter widget
    clutter_widget = cluttergtk.Embed()
    window.add(clutter_widget)
    clutter_widget.show()

    # Set the size of the widget,
    # because we should not set the size of its stage when using GtkClutterEmbed.
    clutter_widget.set_size_request(700, 175)

    # Get the stage and set its size and color
    stage = clutter_widget.get_stage()
    stage.set_color(clutter.Color(0x20, 0x4a, 0x87, 0xff))


    # Show the stage
    stage.show()

    maxw, maxh = 0, 0

    grid = []

    for row in qwerty.lowercase:
        trow = []
        for k in row:
            if isinstance(k, tuple):
                k = k[0]

            text = clutter.Text(
                "Sans 30", k, clutter.Color(0xff, 0, 0, 0xff))

            if text.get_width() > maxw:
                maxw = text.get_width()

            if text.get_height() > maxh:
                maxh = text.get_height()

            trow.append(text)
        grid.append(trow)

    offsetx, offsety = 10, 10
    print maxw, maxh

    for trow in grid:
        for text in trow:
            g = clutter.Group()

            rect = clutter.Rectangle()
            rect.set_position(0, 0)
            rect.set_size(maxw + 10, maxh + 10)
            rect.set_color(clutter.Color(0x33, 0x22, 0x22, 0xff))
            rect.set_border_color(clutter.color_from_string('white'))
            rect.set_border_width(2)
            g.add(rect)

            text.set_position((rect.get_width() - text.get_width() - 5)/2,
                              (rect.get_height() - text.get_height() - 15)/2)
            g.add(text)


            g.set_property("anchor-gravity", clutter.GRAVITY_CENTER)
            g.set_property("scale-x", 0.5)
            g.set_property("scale-y", 0.5)

            g.set_position(offsetx + maxw/2 + 5, offsety + maxh/2 + 5)

            g.set_reactive (True)
            g.connect('enter-event', _on_enter)
            g.connect('leave-event', _on_leave)

            g.show_all()
            stage.add(g)

            offsetx += maxw/2 + 15
        offsety += maxh/2 + 20
        offsetx = 10

    stage.connect("button-press-event", on_stage_button_press)

    # Show the window
    window.show()

    # Start the main loop, so we can respond to events:
    gtk.main()

    return 0


def _on_enter(button, event):
    scale_button (button)

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
