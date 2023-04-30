"""Module to add a directory watcher"""

import os
import sys
import pathlib
import pyinotify

#this may be paramterized in the future
#MODEL = os.path.join(pathlib.Path(__file__).parent.absolute(), "model")
#OUTPUT = os.path.join(pathlib.Path(__file__).parent.parent.parent.absolute(), "results")
MODEL = os.path.join(pathlib.Path(__file__).parent.absolute(), "model")
OUTPUT = "/media/kobayashi/Archivio6T/CLEARLUNG/results"
HISTORY = "/media/kobayashi/Archivio6T/CLEARLUNG/clearlung-history/"

class EventProcessor(pyinotify.ProcessEvent):
    """Helper to process notifying events"""
    _methods = ["IN_CREATE",
                # "IN_OPEN",
                # "IN_ACCESS",
                ]

def process_generator(cls, method):
    """Generate and handle creation process"""
    def _method_name(event):
        if event.maskname=="IN_CREATE|IN_ISDIR":
            print(f"Starting pipeline for {event.pathname}")
            os.system(f"clearlung --single --automatic --base_dir {event.pathname} --target_dir CT " + \
            		f"--model {MODEL} --subroi --output_dir {OUTPUT} --tag 0 --history_path {HISTORY}")

    _method_name.__name__ = f"process_{method}"
    setattr(cls, _method_name.__name__, _method_name)

for method in EventProcessor._methods:
    process_generator(EventProcessor, method)

class PathWatcher():
    """Class to watch for changes"""

    def __init__(self, path_to_watch) -> None:
        """Base constructor"""
        self.path = path_to_watch

        if not os.path.isdir(self.path):
            raise FileNotFoundError()

    def watch(self,):
        """Main method of the PathWatcher class"""
        print(f"Waiting for changes in {self.path}...")

        watch_manager = pyinotify.WatchManager()
        event_notifier = pyinotify.Notifier(watch_manager, EventProcessor())

        watch_this = os.path.abspath(self.path)
        watch_manager.add_watch(watch_this, pyinotify.ALL_EVENTS)
        event_notifier.loop()
