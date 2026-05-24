"""
alignment_instinct.py – غريزة الانسجام الدستوري
تفحص كل فكرة جديدة قبل قبولها (نسخة مبسطة للتشغيل الأول)
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AlignmentVerdict:
    is_aligned: bool
    reason: str
    conflicting_principles: List[str]
    confidence: float


class AlignmentInstinct:
    
    def __init__(self):
        self.principles: List[Dict[str, Any]] = [
            {"id": "p1", "name": "التوحيد", "keywords": ["شرك", "أوثان", "تعدد آلهة", "مع الله"]},
            {"id": "p2", "name": "العدل", "keywords": ["ظلم", "جور", "لا عدل", "تفرقة"]},
            {"id": "p3", "name": "الرحمة", "keywords": ["قسوة", "عنف", "لا رحمة", "تعذيب"]},
            {"id": "p4", "name": "الصدق", "keywords": ["كذب", "غش", "خداع", "تدليس"]},
            {"id": "p5", "name": "الأمانة", "keywords": ["خيانة", "غدر", "سرقة", "اختلاس"]},
        ]
        logger.info(f"✅ AlignmentInstinct جاهز مع {len(self.principles)} مبدأ دستوري")
    
    def check(self, statement: str) -> AlignmentVerdict:
        if not statement or not statement.strip():
            return AlignmentVerdict(False, "عبارة فارغة", [], 0.0)
        
        statement_lower = statement.lower()
        conflicting = []
        max_confidence = 1.0
        
        for principle in self.principles:
            for keyword in principle["keywords"]:
                if keyword in statement_lower:
                    conflicting.append(principle["name"])
                    max_confidence *= 0.7
                    break
        
        if conflicting:
            reason = f"يتعارض مع المبادئ: {', '.join(conflicting)}"
            return AlignmentVerdict(False, reason, conflicting, max_confidence)
        
        return AlignmentVerdict(True, "متفق مع الدستور", [], 0.9)
    
    def get_principles(self) -> List[Dict[str, Any]]:
        return self.principles.copy()
