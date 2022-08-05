import os
import pyinotify

MODEL = "/home/kobayashi/Scrivania/andreasala/covid-classifier/src/covidlib/model"
OUTPUT = "/home/kobayashi/Scrivania/andreasala/data_from_pacs/results"
HISTORY = "/home/kobayashi/Scrivania/clearlung-history/"

class EventProcessor(pyinotify.ProcessEvent):
    _methods = ["IN_CREATE",
                # "IN_OPEN",
                # "IN_ACCESS",
                # "IN_ATTRIB",
                # "IN_CLOSE_NOWRITE",
                # "IN_CLOSE_WRITE",
                # "IN_DELETE",
                # "IN_DELETE_SELF",
                # "IN_IGNORED",
                # "IN_MODIFY",
                # "IN_MOVE_SELF",
                # "IN_MOVED_FROM",
                # "IN_MOVED_TO",
                # "IN_Q_OVERFLOW",
                # "IN_UNMOUNT",
                #"default",
                ]

def process_generator(cls, method):
    def _method_name(self, event):
        if event.maskname=="IN_CREATE|IN_ISDIR":
            print(f"Starting pipeline for {event.pathname}")
            os.system(f"clearlung --single --automatic --base_dir {event.pathname} --target_dir CT " + \
            		f"--model {MODEL} --subroi --output_dir {OUTPUT} --tag 0 --history_path {HISTORY}")
            pass

    _method_name.__name__ = "process_{}".format(method)
    setattr(cls, _method_name.__name__, _method_name)

for method in EventProcessor._methods:
    process_generator(EventProcessor, method)

class PathWatcher():

    def __init__(self, path_to_watch) -> None:
        self.path = path_to_watch

        if not os.path.isdir(self.path):
            raise FileNotFoundError()
         
    def watch(self,):
        print(f"Waiting for changes in {self.path}...")

        watch_manager = pyinotify.WatchManager()
        event_notifier = pyinotify.Notifier(watch_manager, EventProcessor())

        watch_this = os.path.abspath(self.path)
        watch_manager.add_watch(watch_this, pyinotify.ALL_EVENTS)
        event_notifier.loop()