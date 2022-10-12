from typing import Callable, Any, List, Awaitable


class JPSetup:
    """
    decorator to use with functions that should be executed prior to all tests
    """
    FN: List[Callable[[], Awaitable]] = []

    def __init__(self, f: Callable[[], Any]):
        self.FN.append(f)


class JPTeardown:
    """
    decorator to use with functions that should be executed after all tests
    """
    FN: List[Callable[[], Any]] = []

    def __init__(self, f: Callable[[], Any]):
        self.FN.append(f)
