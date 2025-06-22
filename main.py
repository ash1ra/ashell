from fabric import Application
from fabric.utils import get_relative_path, monitor_file

from modules.app_launcher import AppLauncher


def apply_stylesheet(*_):
    return app.set_stylesheet_from_file(get_relative_path("./styles/main.css"))


if __name__ == "__main__":
    style_monitor = monitor_file(get_relative_path("./styles/main.css"))
    style_monitor.connect("changed", apply_stylesheet)

    app_launcher = AppLauncher()

    app = Application()

    apply_stylesheet()
    app.run()
