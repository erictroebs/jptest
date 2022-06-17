from typing import Callable, Any, List
from .JPTestBook import JPTestBook


class JPPreRun:
    """
    decorator to use with functions that should be executed prior to all tests
    """
    FN: List[Callable[[], Any]] = []

    def __init__(self, f: Callable[[], Any]):
        self.FN.append(f)


class JPPreTest:
    """
    decorator to use with functions that should be executed prior to any test
    """
    FN: List[Callable[[JPTestBook], Any]] = []

    def __init__(self, f: Callable[[JPTestBook], Any]):
        self.FN.append(f)


class JPPostTest:
    """
    decorator to use with functions that should be executed after any test
    """
    FN: List[Callable[[JPTestBook], Any]] = []

    def __init__(self, f: Callable[[JPTestBook], Any]):
        self.FN.append(f)


class JPPostRun:
    """
    decorator to use with functions that should be executed after all tests
    """
    FN: List[Callable[[], Any]] = []

    def __init__(self, f: Callable[[], Any]):
        self.FN.append(f)
