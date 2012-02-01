import collections
import inspect
import signal
import traceback

from twisted.internet import task

# These values are seconds
CANCEL_INTERVAL = 0.1
MAX_DELAY = 0.5


class HangWatcher(object):
    bad_functions = collections.defaultdict(int)
    hang_count = 0

    def __init__(self, cancel_interval=CANCEL_INTERVAL, max_delay=MAX_DELAY):
        # Handle SIGALRMs with print_traceback
        signal.signal(signal.SIGALRM, self.log_traceback)

        # this LoopingCall is run by the reactor.
        # If the reactor is hung, cancel_sigalrm won't run and the handler for SIGALRM will fire
        self.lc = task.LoopingCall(self.cancel_sigalrm)
        self.cancel_interval = cancel_interval
        self.max_delay = MAX_DELAY

    def start(self):
        self.lc.start(self.cancel_interval)

    def reset_itimer(self):
        # TODO: change this to ITIMER_VIRTUAL for real-life usage
        #signal.setitimer(signal.ITIMER_VIRTUAL, self.max_delay)
        signal.setitimer(signal.ITIMER_REAL, self.max_delay)

    def log_traceback(self, signal, frame):
        # Oh snap, cancel_sigalrm didn't get called
        traceback.print_stack(frame)

        self.hang_count += 1

        code_tuple = (frame.f_code.co_name, frame.f_code.co_filename, frame.f_code.co_firstlineno)
        self.bad_functions[code_tuple] += 1
        self.reset_itimer()

    def cancel_sigalrm(self):
        # Cancel any pending alarm
        if signal.alarm(0) == 0:
            print "No SIGALRM to cancel. This should only happen if we handled a traceback"
        self.reset_itimer()

    def print_stats(self):
        print "Main thread was hung %s times" % self.hang_count
        print "Worst offending functions:"
        for k, v in self.bad_functions.items():
            print "Function %s count %s" % (k, v)

    def stats(self):
        stats_dict = {"hang_count": self.hang_count,
                      "bad_functions": self.bad_functions,
                     }

        return stats_dict
