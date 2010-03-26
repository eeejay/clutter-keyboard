import sys

import cluttergtk   # must be the first to be imported
import clutter
import gtk
import qwerty

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
    vbox = gtk.VBox(False, 6)
    window.add(vbox)
    vbox.show()
    button = gtk.Button("Change Color")
    vbox.pack_end(button, False, False, 0)
    button.show()
    button.connect('clicked', on_button_clicked)

    # Stop the application when the window is closed
    window.connect('hide', gtk.main_quit)

    # Create the clutter widget
    clutter_widget = cluttergtk.Embed()
    vbox.pack_start(clutter_widget, True, True, 0)
    clutter_widget.show()

    # Set the size of the widget,
    # because we should not set the size of its stage when using GtkClutterEmbed.
    clutter_widget.set_size_request(600, 200)

    # Get the stage and set its size and color
    stage = clutter_widget.get_stage()
    stage.set_color(stage_color)

    # Show the stage
    stage.show()

    offsetx, offsety = 0, 0

    maxw, maxh = 0, 0

    grid = []

    for row in qwerty.lowercase:
        for k in row:
            if isinstance(k, tuple):
                k = k[0]

            g = clutter.Group()

            text = clutter.Text(
                "Sans 10", k, clutter.Color(0xff, 0, 0, 0xff))
            text.set_position(offsetx + 15, offsety + 10)

            if text.get_width() > maxw:
                maxw = text.get_width()

            if text.get_height() > maxh:
                maxw = text.get_height()

            

            rect = clutter.Rectangle()
            rect.set_position(offsetx + 5, offsety + 5)
            rect.set_size(
                max(text.get_width() + 20, 30),
                max(text.get_height() + 15, 30))
            rect.set_color(clutter.Color(0x33, 0x22, 0x22, 0xff))
            rect.set_border_color(clutter.color_from_string('white'))
            rect.set_border_width(2)
            rect.show()
            g.add(rect)

            text.show()
            g.add(text)

            stage.add(g)

            offsetx += 50
        offsety += 50
        offsetx = 0

    # Connect a signal handler to handle mouse clicks and key presses on the stage
    stage.connect("button-press-event", on_stage_button_press)

    # Show the window
    window.show()

    # Start the main loop, so we can respond to events:
    gtk.main()

    return 0


if __name__ == '__main__':
    sys.exit(main())
