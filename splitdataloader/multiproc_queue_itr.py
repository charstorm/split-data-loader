from multiprocessing import Process, Queue
from typing import Callable, Any, TypeVar, Generic, Self
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EndOfQueue:
    pass


def iterator_handler(
    outq: Queue, itr_func: Callable, args: list[Any], kwargs: dict[str, Any]
) -> None:
    """
    creates an iterator using itr_func and pushes the results to outq.
    """
    try:
        for item in itr_func(*args, **kwargs):
            outq.put(item)
    except Exception:
        logger.exception("Error while iterating")

    outq.put(EndOfQueue())


class MpQItr(Generic[T]):
    """
    Run the iterator in a child process and yield the values.
    """

    def __init__(self, itr_func: Callable, *args: Any, **kwargs: Any) -> None:
        self.itr_func = itr_func
        self.args = args
        self.kwargs = kwargs
        self.qsize = 16

    def __iter__(self) -> Self:
        self.yield_q: Queue | None = Queue(self.qsize)
        self.proc = Process(
            target=iterator_handler,
            args=(self.yield_q, self.itr_func, self.args, self.kwargs),
        )
        self.proc.daemon = True
        self.proc.start()
        return self

    def __next__(self) -> T:
        if self.yield_q is None:
            raise StopIteration

        item = self.yield_q.get()
        if isinstance(item, EndOfQueue):
            self.proc = None
            self.yield_q = None
            raise StopIteration
        return item
