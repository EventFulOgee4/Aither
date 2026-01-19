#This module is ESSENTIAL for Aither, it detects crisis detection within user messages, and patterns across pattern history
from aither.modules.memory import AitherMemory as mem



class AitherSafety():
    def __init__(self, memory):
        self.memory = memory

