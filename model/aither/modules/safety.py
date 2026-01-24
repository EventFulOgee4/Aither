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
        self.crisis_patterns = {
        "explicitness": {
            "patterns": [
                "kill myself", "end my life", "want to die", "don't want to be here",
                "end it all", "better off dead", "going to do it", "not needed",
                "unalive", "no reason to live", "want it to be over", "can't do this anymore",
                "final goodbye", "won't be around", "checking out", "take my own life",
                "not gonna be here", "plan to end", "suicide", "hurt myself"
            ],
            "severity": RiskAssessment.CRITICAL
        },
        "hopelessness": {
            "patterns": [
                "no one cares", "no one likes me", "I'm hated", "burden to everyone",
                "they'd be better without me", "no point anymore", "given up",
                "no future", "no way out", "nothing will change", "trapped forever",
                "no one would notice", "completely alone", "nobody loves me",
                "worthless", "waste of space", "shouldn't exist", "don't belong"
            ],
            "severity": RiskAssessment.URGENT
        },
        "unwell": {
            "patterns": [
                "can't get out of bed", "stopped eating", "can't sleep", "sleep all day",
                "hate myself", "I'm a failure", "nothing matters", "don't care anymore",
                "crying all the time", "empty inside", "numb", "lost interest",
                "can't function", "falling apart", "barely surviving", "going through the motions",
                "isolating myself", "pushing everyone away", "self harm", "cutting"
            ],
            "severity": RiskAssessment.CONCERNED
        },
        "distress": {
            "patterns": [
                "overwhelmed", "can't cope", "stressed out", "anxious", "panic",
                "breaking down", "losing it", "can't handle", "so tired of",
                "exhausted", "burned out", "frustrated", "lonely", "scared",
                "worried sick", "can't relax", "on edge", "feeling down", "sad lately"
            ],
            "severity": RiskAssessment.WATCHFUL
        },
        "healthy": {
            "patterns": [],  # Default state - absence of concerning patterns
            "severity": RiskAssessment.BASELINE
        }
    }
        

