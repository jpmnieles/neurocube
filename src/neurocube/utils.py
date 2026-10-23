import threading
import time

class PrecisionTimer:
    # 1. Make function optional by defaulting to None
    def __init__(self, interval, function=None):
        self.interval = interval
        self.function = function
        
        self.timer = None
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()

    def _wrapper(self):
        with self.lock:
            self.end_time = time.perf_counter()
        
        # 2. Only execute if a function was passed
        if self.function:
            self.function()

    def start(self):
        with self.lock:
            self.start_time = time.perf_counter()
            self.end_time = None 
            self.timer = threading.Timer(self.interval, self._wrapper)
            self.timer.start()

    def cancel(self):
        with self.lock:
            if self.timer:
                self.timer.cancel()
            if self.end_time is None:
                self.end_time = time.perf_counter()

    def elapsed(self) -> float:
        with self.lock:
            if self.start_time is None:
                return 0.0
            if self.end_time is None:
                return time.perf_counter() - self.start_time
            return self.end_time - self.start_time

    def remaining(self) -> float:
        return max(0.0, self.interval - self.elapsed())