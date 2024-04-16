from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import importlib.util

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == "../parameters.py":
            print("Parameters file modified. Reloading parameters...")
            spec = importlib.util.spec_from_file_location("parameters", "../parameters.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print("New parameters:")
            print("TP:", module.TP)
            print("SL:", module.SL)
            print("LEVERAGE:", module.LEVERAGE)
            print("TYPE:", module.TYPE)
            print("QTY:", module.QTY)