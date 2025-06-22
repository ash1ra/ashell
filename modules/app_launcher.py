from typing import Iterator

from fabric import Application
from fabric.utils import DesktopApp, get_desktop_applications, idle_add, remove_handler
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.wayland import WaylandWindow
from gi.repository import Gdk


class AppLauncher(WaylandWindow):
    def __init__(self, **kwargs):
        super().__init__(
            title="app-launcher",
            name="app-launcher",
            layer="top",
            anchor="center",
            exclusivity="none",
            keyboard_mode="on-demand",
            visible=False,
            all_visible=False,
            **kwargs,
        )

        self._arranger_handler: int = 0
        self._apps_list = get_desktop_applications()

        self.viewport = Box(orientation="vertical")
        self.search_entry = Entry(
            placeholder="Search for apps...",
            h_expand=True,
            name="app-launcher-search-entry",
            notify_text=lambda entry, *_: self.arrange_viewport(entry.get_text()),
            on_key_press_event=self.on_key_press,
        )
        self.scrolled_window = ScrolledWindow(
            min_content_size=(600, 320),
            max_content_size=(280 * 2, 320),
            child=self.viewport,
            name="app-launcher-scrolled-window",
        )

        self.add(
            Box(
                orientation="vertical",
                children=[
                    self.search_entry,
                    self.scrolled_window,
                ],
            )
        )

        self.show_all()

    def arrange_viewport(self, query: str = ""):
        remove_handler(self._arranger_handler) if self._arranger_handler else None

        self.viewport.children = []

        filtered_apps_iter = []
        for app in self._apps_list:
            app_names = [app.display_name, app.name, app.generic_name]
            if (
                query.casefold()
                in "".join(app_name for app_name in app_names if app_name).casefold()
            ):
                filtered_apps_iter.append(app)

        self._arranger_handler = idle_add(
            lambda *args: self.add_next_application(*args),
            iter(filtered_apps_iter),
            pin=True,
        )

        return False

    def add_next_application(self, apps_iter: Iterator[DesktopApp]):
        if not (app := next(apps_iter, None)):
            return False

        self.viewport.add(self.bake_application_slot(app))
        return True

    def bake_application_slot(self, app: DesktopApp, **kwargs) -> Button:
        return Button(
            child=Label(label=app.display_name or "No name"),
            on_clicked=lambda *_: (app.launch(), self.application.quit()),
            **kwargs,
        )

    def on_key_press(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.application.quit()


if __name__ == "__main__":
    app_launcher = AppLauncher()
    app = Application("app-launcher", app_launcher)
    app.run()
