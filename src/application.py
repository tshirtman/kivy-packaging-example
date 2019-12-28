from utils import load_kv
from kivy.app import App


class Application(App):
    def build(self):
        return ROOT

    def build_config(self):
        pass

    def build_settings(self):
        pass

    def on_start(self):
        pass

    def on_pause(self):
        pass

    def on_stop(self):
        pass


app = Application()

# build() will be called when app.run() is called, so it's fine to load
# the root after creating the app
ROOT = load_kv()
