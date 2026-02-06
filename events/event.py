from enum import Enum
from queue import Queue, Empty as QueueEmpty, Full as QueueFull
from typing import Any, Callable, Literal, NamedTuple, Union

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
    """

    DEFAULT_SLEEP_DURATION = 100  # Default sleep duration in milliseconds

    event_queue: Queue[Event]
    after: Callable[[Union[int, Literal["idle"]], Callable], Any]

    def __init__(self, trigger_func: Callable[[Union[int, Literal["idle"]], Callable], Any]):
        """
        Initialize the EventLoop.
        
        :param self: Self instance
        :param trigger_func: Function to trigger events after a delay
            :type trigger_func: Callable[[Union[int, Literal["idle"]], Callable], Any]
        """

        self.event_queue = Queue()
        self.after = trigger_func

    def start(self):
        """
        Start processing events.
        
        :param self: Self instance
        """

        self.handle_event()

    # Not used currently
    def stop(self):
        """
        Stop the event loop.
        
        :param self: Self instance
        """

        # Clear the event queue
        with self.event_queue.mutex:
            self.event_queue.queue.clear()

    def has_pending_tasks(self) -> bool:
        """
        Check if there are pending tasks in the event queue.
        
        :param self: Self instance

        :return: True if there are pending tasks, False otherwise
        """

        return not self.event_queue.empty()

    def handle_event(self):
        """
        Handle the next event in the queue.
        
        :param self: Self instance
        """

        try:
            event = self.event_queue.get_nowait()
        except QueueEmpty:
            # If no event available, check again in 100ms
            self.after(self.DEFAULT_SLEEP_DURATION, self.handle_event)
            return
            
        if event.type == EventType.SLEEP:
            self.after(event.data["duration"], self.handle_event)
        elif event.type == EventType.FUNC:
            event.data["func"]()
            self.after(self.DEFAULT_SLEEP_DURATION, self.handle_event)
        elif event.type == EventType.SLEEP_UNTIL:
            self._sleep_until(event.data["func"])
        else:
            # self.after(self.DEFAULT_SLEEP_DURATION, self.handle_event)
            raise ValueError("Unimplemented event type: " + str(event.type))

    def run(self, func: Callable):
        """
        Schedule a function to be run in the event loop.
        
        :param self: Self instance
        :param func: Function to be scheduled
            :type func: Callable
        """

        self.queue_event(Event(EventType.FUNC, {"func": func}))

    def sleep(self, duration):
        """
        Schedule a sleep event for a specified duration.
        Event loop will pause for duration before next event.
        
        :param self: Self instance
        :param duration: Duration in milliseconds to sleep
            :type duration: int
        """

        self.queue_event(Event(EventType.SLEEP, {"duration": duration}))

    def sleep_until(self, func: Callable[[], bool]):
        """
        Schedule a sleep until event based on a condition function.
        Intended function will run when condition is met.
        
        :param self: Self instance
        :param func: Condition function to evaluate
            :type func: Callable[[], bool]
        """

        self.queue_event(Event(EventType.SLEEP_UNTIL, {"func": func}))
        
    def queue_event(self, event: Event):
        """
        Queue an event to be processed by the event loop.

        :param self: Self instance
        :param event: Event to be queued
            :type event: Event
        """
        try:
            self.event_queue.put_nowait(event)
        except QueueFull:
            raise RuntimeError("Event queue is full, cannot schedule new event.")
        
    def run_and_wait(self, func: Callable, condition: Callable[[], bool]):
        """
        Run a function and wait until a condition is met.
        
        :param self: Self instance
        :param func: Function to be run
            :type func: Callable
        :param condition: Condition to wait for
            :type condition: Callable[[], bool]
        """

        self.run(func)
        self.sleep_until(condition)

    def _sleep_until(self, func: Callable[[], bool]):
        """
        Internal method to handle sleep until condition is met.
        
        :param self: Self instance
        :param func: Condition function to evaluate
            :type func: Callable[[], bool]
        """

        result = func()

        if result:
            self.after(self.DEFAULT_SLEEP_DURATION, self.handle_event)
        else:
            self.after(self.DEFAULT_SLEEP_DURATION, lambda: self._sleep_until(func))