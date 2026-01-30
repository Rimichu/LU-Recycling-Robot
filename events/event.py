from enum import Enum
from queue import Queue, Empty as QueueEmpty
from typing import Any, Callable, Literal, NamedTuple, Union
import threading
import time

class EventType(Enum):
    """
    Event types for the event loop.

    Sleep: wait for a duration before next event.
        Param: duration in milliseconds.
    
    Func: execute a function immediately.
        Param: function to execute.
    
    SleepUntil: wait until a condition function returns True before next event.
        Param: condition function to evaluate.
    """

    SLEEP = 1
    FUNC = 2
    SLEEP_UNTIL = 3

'Event data structure.'
class Event(NamedTuple):
    type: EventType
    data: dict


class EventLoop:
    """
    Event loop to manage and process events sequentially.
    Can run in a background thread to allow concurrent execution.
    """
    event_queue: Queue[Event]
    after: Callable[[Union[int, Literal["idle"]], Callable], Any]
    _running: bool
    _thread: threading.Thread

    def __init__(self, trigger_func: Callable[[Union[int, Literal["idle"]], Callable], Any]) -> None:
        self.event_queue = Queue()
        self.after = trigger_func
        self._running = False
        self._thread = None

    def start(self) -> None:
        """Start the event loop in a background thread."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop the event loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        """Internal method to run the event loop."""
        self.handle_event()

    def handle_event(self):
        if not self._running:
            return
        try:
            event = self.event_queue.get_nowait()
        except QueueEmpty:
            # no events, wait.
            self.after(100, self.handle_event)
            return

        if event.type == EventType.SLEEP:
            self.after(event.data["duration"], self.handle_event)
        elif event.type == EventType.FUNC:
            event.data["func"]()
            self.after(100, self.handle_event)
        elif event.type == EventType.SLEEP_UNTIL:
            self._sleep_until(event.data["func"])
        else:
            self.after(100, self.handle_event)
            raise ValueError("Unimplemented event type: " + str(event.type))

    def handle_event(self):
        try:
            event = self.event_queue.get_nowait()
        except QueueEmpty:
            # no events, wait.
            self.after(100, self.handle_event)
            return

        if event.type == EventType.SLEEP:
            self.after(event.data["duration"], self.handle_event)
        elif event.type == EventType.FUNC:
            event.data["func"]()
            self.after(100, self.handle_event)
        elif event.type == EventType.SLEEP_UNTIL:
            self._sleep_until(event.data["func"])
        else:
            self.after(100, self.handle_event)
            raise ValueError("Unimplemented event type: " + str(event.type))

    def run(self, func: Callable) -> None:
        """Queue a function to run in the event loop."""
        self.event_queue.put_nowait(Event(EventType.FUNC, {"func": func}))

    def sleep(self, duration: int) -> None:
        """Queue a sleep event."""
        self.event_queue.put_nowait(Event(EventType.SLEEP, {"duration": duration}))

    def sleep_until(self, func: Callable[[], bool]) -> None:
        """Queue a sleep-until event."""
        self.event_queue.put_nowait(Event(EventType.SLEEP_UNTIL, {"func": func}))

    def wait_for(self, condition: Callable[[], bool], timeout: float = None) -> bool:
        """
        Synchronously wait for a condition to become true.
        
        :param condition: Function that returns True when condition is met
        :param timeout: Maximum time to wait in seconds (None for infinite)
        :return: True if condition met, False if timeout
        """
        start = time.time()
        while True:
            if condition():
                return True
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(0.05)  # Small sleep to avoid busy-waiting

    def run_and_wait(self, func: Callable, condition: Callable[[], bool]):
        self.run(func)
        self.sleep_until(condition)

    ' Continually check the condition function until it returns True.'
    def _sleep_until(self, func: Callable[[], bool]):
        result = func()
        if result:
            self.after(100, self.handle_event)
        else:
            self.after(100, lambda: self._sleep_until(func))
