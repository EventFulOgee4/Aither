#This module is ESSENTIAL for Aither, it detects crisis detection within user messages, and patterns across pattern history
from ml.memory import AitherMemory as mem
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
        self.action_map = {
            RiskAssessment.BASELINE: "continue_normal",
            RiskAssessment.WATCHFUL: "gentle_checkin",
            RiskAssessment.CONCERNED: "express_support",
            RiskAssessment.URGENT: "direct_acknowledgment",
            RiskAssessment.CRITICAL: "crisis_protocol"
        }



    def detect_crisis(self, message : str):

        implications = []

        message = message.lower()

        for crisis in self.crisis_patterns:
            crisisData = self.crisis_patterns[crisis]
            crisisPatterns = crisisData.get("patterns")

            for pattern in crisisPatterns:
                if pattern in message:
                    severity = crisisData.get("severity")
                    implications.append((pattern, severity))

        if len(implications) == 0:
            return SafetyAssessment(
                riskLevel=RiskAssessment.BASELINE,
                recommendedAction=self.action_map[RiskAssessment.BASELINE],
                triggers=[],
                confidence=0.9,
                toneChange="none"
            )
        else:
            temp_triggers = []
            for imp in implications:
                temp_triggers.append(imp[0])
            severity = max(implications, key=lambda x: x[1].value)
            temp_confidence = min(0.5 + (len(implications) * 0.15), 0.95)
            return SafetyAssessment(
                riskLevel=severity[1],
                recommendedAction=self.action_map[severity[1]],
                triggers=temp_triggers,
                confidence=temp_confidence,
                toneChange="N/A" #subject to change later with memory integration
            )


