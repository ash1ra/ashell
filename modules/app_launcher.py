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

        self.arranger_handler: int = 0
        self.apps_list = get_desktop_applications()

        self.selected_index = -1

        self.apps_wrapper = Box(
            orientation="vertical",
            on_key_press_event=self.on_key_press,
        )
        self.search_entry = Entry(
            placeholder="Search for apps...",
            h_expand=True,
            name="app-launcher-search-entry",
            notify_text=lambda entry, *_: self.arrange_apps_wrapper(entry.get_text()),
        )
        self.scrolled_window = ScrolledWindow(
            min_content_size=(600, 320),
            max_content_size=(280 * 2, 320),
            child=self.apps_wrapper,
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

    def arrange_apps_wrapper(self, query: str = "") -> None:
        remove_handler(self.arranger_handler) if self.arranger_handler else None

        self.apps_wrapper.children = []

        filtered_apps_iter = []
        for app in self.apps_list:
            app_names = [app.display_name, app.name, app.generic_name]
            if query.casefold() in "".join(app_name for app_name in app_names if app_name).casefold():
                filtered_apps_iter.append(app)

        self.arranger_handler = idle_add(
            lambda *args: self.add_next_app(*args),
            iter(filtered_apps_iter),
            pin=True,
        )

    def add_next_app(self, apps_iter: Iterator[DesktopApp]) -> bool:
        if not (app := next(apps_iter, None)):
            return False

        self.apps_wrapper.add(self.create_app_slot(app))
        return True

    def create_app_slot(self, app: DesktopApp, **kwargs) -> Button:
        return Button(
            child=Label(label=app.display_name or "No name"),
            style_classes="app-launcher-app-button",
            on_clicked=lambda *_: (app.launch(), self.toggle()),
            **kwargs,
        )

    def change_selected_index(self, delta: int) -> None:
        if children := self.apps_wrapper.get_children():
            new_index = max(-1, min(self.selected_index + delta, len(children) - 1))
            self.move_selection(new_index)

    def move_selection(self, new_index: int) -> None:
        current_button = self.apps_wrapper.get_children()[self.selected_index]
        current_button.get_style_context().remove_class("selected")

        self.selected_index = new_index

        if self.selected_index > -1:
            new_button = self.apps_wrapper.get_children()[self.selected_index]
            new_button.get_style_context().add_class("selected")

            self.scroll_to_selected(new_button)

    def scroll_to_selected(self, button: Button) -> None:
        scrolled_window_adjustment = self.scrolled_window.get_vadjustment()
        button_allocation = button.get_allocation()

        button_position = button_allocation.y
        button_height = button_allocation.height
        scrolled_window_height = scrolled_window_adjustment.get_page_size()
        scrolled_window_delta = scrolled_window_adjustment.get_value()

        visible_top = scrolled_window_delta
        visible_bottom = scrolled_window_delta + scrolled_window_height

        if button_position < visible_top:
            scrolled_window_adjustment.set_value(button_position)
        elif button_position + button_height > visible_bottom:
            scrolled_window_adjustment.set_value(button_position + button_height - scrolled_window_height)

    def on_key_press(self, _, event) -> None:
        match event.keyval:
            case Gdk.KEY_Escape:
                self.toggle()
            case Gdk.KEY_Down:
                self.change_selected_index(1)
            case Gdk.KEY_Up:
                self.change_selected_index(-1)

    def toggle(self) -> None:
        self.search_entry.set_text("")
        self.selected_index = -1
        self.apps_list = get_desktop_applications()
        self.set_visible(not self.is_visible())


if __name__ == "__main__":
    app_launcher = AppLauncher()
    app = Application("app-launcher", app_launcher)
    app.run()
