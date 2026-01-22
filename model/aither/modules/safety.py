#This module is ESSENTIAL for Aither, it detects crisis detection within user messages, and patterns across pattern history
from aither.modules.memory import AitherMemory as mem
from enum import Enum
from dataclasses import dataclass

class RiskAssessment(Enum):
    BASELINE = 0
    WATCHFUL = 1
    CONCERNED = 2
    URGENT = 3
    CRITICAL = 4

    
@dataclass
class SafetyAssessment:
    riskLevel : RiskAssessment
    recommendedAction : str  
    triggers : list[str]
    confidence : float
    toneChange : str 


class AitherSafety():
    def __init__(self, memory):
        self.memory = memory

