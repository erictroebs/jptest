from typing import Callable, Any, List
from .JPTestBook import JPTestBook


class JPPreRun:
    FN: List[Callable[[], Any]] = []

    def __init__(self, f: Callable[[], Any]):
        self.FN.append(f)


class JPPreTest:
    FN: List[Callable[[JPTestBook], Any]] = []

    def __init__(self, f: Callable[[JPTestBook], Any]):
        self.FN.append(f)


class JPPostTest:
    FN: List[Callable[[JPTestBook], Any]] = []

    def __init__(self, f: Callable[[JPTestBook], Any]):
        self.FN.append(f)


class JPPostRun:
    FN: List[Callable[[], Any]] = []

    def __init__(self, f: Callable[[], Any]):
        self.FN.append(f)
