import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from panels.menu import MenuPanel

def create_panel(*args):
    return MainPanel(*args)

class MainPanel(MenuPanel):
    def __init__(self, screen, title, back=False):
        super().__init__(screen, title, False)

    def initialize(self, panel_name, items, extrudercount):
        print("### Making MainMenu")

        grid = self._gtk.HomogeneousGrid()
        grid.set_hexpand(True)
        grid.set_vexpand(True)

        # Create Extruders and bed icons
        eq_grid = Gtk.Grid()
        eq_grid.set_hexpand(True)
        eq_grid.set_vexpand(True)

        self.heaters = []

        i = 0
        for x in self._printer.get_tools():
            self.labels[x] = self._gtk.ButtonImage("extruder-"+str(i), self._gtk.formatTemperatureString(0, 0))
            self.heaters.append(x)
            i += 1

        add_heaters = self._printer.get_heaters()
        for h in add_heaters:
            if h == "heater_bed":
                self.labels[h] = self._gtk.ButtonImage("bed", self._gtk.formatTemperatureString(0, 0))
            else:
                name = " ".join(h.split(" ")[1:])
                self.labels[h] = self._gtk.ButtonImage("heat-up", name)
            self.heaters.append(h)

        for c in self._printer.get_other_controllers():
            self.labels[c] = self._gtk.ButtonImage(c.split(" ")[-1], "val")
            self.heaters.append(c)

        cfg = self._config.get_config()
        _ = self.lang.gettext
        for category in sorted(cfg.keys()):
            if not category.startswith('main macro_'):
                continue
            macro = cfg[category]
            self.labels[category] = self._gtk.ButtonImage(
                                        macro["icon"],
                                        _(macro["name"]))
            self.labels[category].connect("clicked", self.run_macro, macro["script"])
            self.heaters.append(category)

        cols = 3 if len(self.heaters) > 4 else (1 if len(self.heaters) <= 2 else 2)
        if self._config.get_main_config_option("branding", "").lower() in ['true', '1', 't', 'y', 'yes']:
            eq_grid.attach(self._gtk.ButtonImage("manufacturer_logo", width_scale=6, height_scale=2), 0, 0, cols, 1)
            i = cols
        else:
            i = 0
        for h in self.heaters:
            eq_grid.attach(self.labels[h], i % cols, int(i/cols), 1, 1)
            i += 1

        self.items = items
        self.create_menu_items()

        self.grid = Gtk.Grid()
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_homogeneous(True)

        grid.attach(eq_grid, 0, 0, 1, 1)
        grid.attach(self.arrangeMenuItems(items, 2, True), 1, 0, 1, 1)

        self.grid = grid

        self.target_temps = {
            "heater_bed": 0,
            "extruder": 0
        }

        self.content.add(self.grid)
        self.layout.show_all()

    def activate(self):
        return

    def run_macro(self, widget, macro):
        self._screen._ws.klippy.gcode_script(macro.format(self))

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        for x in self._printer.get_tools():
            self.update_temp(
                x,
                self._printer.get_dev_stat(x, "temperature"),
                self._printer.get_dev_stat(x, "target")
            )
        for h in self._printer.get_heaters():
            self.update_temp(
                h,
                self._printer.get_dev_stat(h, "temperature"),
                self._printer.get_dev_stat(h, "target"),
                None if h == "heater_bed" else " ".join(h.split(" ")[1:])
            )
        for c in self._printer.get_other_controllers():
            stats = self._printer.get_dev_stats(c)
            self.labels[c].set_label("%.2f%s" %(stats["value"], stats["units"]))
        return
