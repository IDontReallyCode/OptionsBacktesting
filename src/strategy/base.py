"""
Strategy Base Module
====================

Responsibility:
    - Define the interface for all strategies.
    - Provide access to Data and Portfolio.
    - Output: List[SignalEvent]
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.events import SignalEvent

class Strategy(ABC):
    def __init__(self, data_handler, portfolio):
        self.data_handler = data_handler
        self.portfolio = portfolio

    @abstractmethod
    def on_bar(self, current_time: datetime) -> List[SignalEvent]:
        """
        Called by the Engine on every time step.
        Input: Current Time
        Output: A list of SignalEvents (or empty list)
        """
        raise NotImplementedError("Strategies must implement on_bar()")