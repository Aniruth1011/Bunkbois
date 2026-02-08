"""
Medical Knowledge Base for Healthcare Agent System
Contains medical domain rules, requirements, and validation logic
"""

from typing import Dict, List, Set


class MedicalKnowledge:
    """Medical domain knowledge for skill-infrastructure validation."""
    
    # Equipment requirements for medical procedures/specialties
    SKILL_REQUIREMENTS: Dict[str, Dict[str, List[str]]] = {
        "neurosurgery": {
            "critical": ["ICU", "operating room", "operating microscope", "anesthesia machine"],
            "required": ["CT scan", "surgical instruments", "autoclave", "ventilator"],
            "recommended": ["MRI", "neuromonitoring equipment"]
        },
        "cardiovascular surgery": {
            "critical": ["ICU", "operating room", "cardiopulmonary bypass machine", "anesthesia machine"],
            "required": ["ECG", "defibrillator", "surgical instruments", "blood bank"],
            "recommended": ["cardiac catheterization lab", "ECMO"]
        },
        "cataract surgery": {
            "critical": ["operating microscope", "phacoemulsification machine", "operating room"],
            "required": ["surgical instruments", "autoclave", "slit lamp"],
            "recommended": ["optical coherence tomography", "IOL master"]
        },
        "dialysis": {
            "critical": ["dialysis machine", "water purification system", "dialysis chair"],
            "required": ["vascular access supplies", "emergency equipment"],
            "recommended": ["portable dialysis machine"]
        },
        "cardiology": {
            "critical": ["ECG machine", "defibrillator"],
            "required": ["echocardiography", "cardiac monitor", "stress test equipment"],
            "recommended": ["holter monitor", "cardiac catheterization lab"]
        },
        "ophthalmology": {
            "critical": ["slit lamp", "ophthalmoscope"],
            "required": ["tonometer", "refraction equipment"],
            "recommended": ["optical coherence tomography", "fundus camera"]
        },
        "surgery": {
            "critical": ["operating room", "anesthesia machine", "surgical instruments"],
            "required": ["autoclave", "surgical lights", "operating table"],
            "recommended": ["laparoscopic equipment", "surgical microscope"]
        },
        "orthopedic surgery": {
            "critical": ["operating room", "C-arm fluoroscopy", "surgical instruments"],
            "required": ["orthopedic implants", "power tools", "casting equipment"],
            "recommended": ["arthroscopy equipment"]
        },
        "maternity": {
            "critical": ["delivery room", "fetal monitor", "resuscitation equipment"],
            "required": ["ultrasound", "blood bank access", "neonatal care equipment"],
            "recommended": ["operating room for C-sections", "NICU"]
        },
        "intensive care": {
            "critical": ["ICU beds", "ventilator", "cardiac monitor", "defibrillator"],
            "required": ["infusion pumps", "emergency medications", "laboratory access"],
            "recommended": ["dialysis capability", "advanced imaging"]
        },
        "hospitalist": {
            "critical": ["hospital beds", "monitoring equipment", "emergency cart"],
            "required": ["laboratory access", "imaging access", "pharmacy"],
            "recommended": ["electronic health records", "consultation services"]
        },
        "emergency medicine": {
            "critical": ["emergency department", "defibrillator", "crash cart", "oxygen supply"],
            "required": ["X-ray", "CT scan", "laboratory", "pharmacy"],
            "recommended": ["trauma bay", "helicopter pad"]
        }
    }
    
    # Procedure-to-specialty mapping
    PROCEDURE_SPECIALTY_MAP: Dict[str, str] = {
        "cataract surgery": "ophthalmology",
        "glaucoma surgery": "ophthalmology",
        "retinal surgery": "ophthalmology",
        "LASIK": "ophthalmology",
        "coronary bypass": "cardiovascular surgery",
        "valve replacement": "cardiovascular surgery",
        "angioplasty": "cardiology",
        "hemodialysis": "dialysis",
        "peritoneal dialysis": "dialysis",
        "knee replacement": "orthopedic surgery",
        "hip replacement": "orthopedic surgery",
        "cesarean section": "maternity",
        "normal delivery": "maternity",
        "brain surgery": "neurosurgery",
        "spinal surgery": "neurosurgery"
    }
    
    # Equipment categories
    EQUIPMENT_CATEGORIES: Dict[str, List[str]] = {
        "imaging": ["X-ray", "CT scan", "MRI", "ultrasound", "mammography", "fluoroscopy"],
        "surgical": ["operating room", "surgical instruments", "operating microscope", 
                    "laparoscopic equipment", "surgical lights", "operating table"],
        "life_support": ["ventilator", "defibrillator", "cardiac monitor", "infusion pump"],
        "diagnostic": ["ECG machine", "echocardiography", "endoscope", "spirometer"],
        "sterilization": ["autoclave", "sterilizer"],
        "specialty": ["dialysis machine", "phacoemulsification machine", 
                     "cardiopulmonary bypass machine", "C-arm fluoroscopy"]
    }
    
    @classmethod
    def get_requirements(cls, capability: str) -> Dict[str, List[str]]:
        """
        Get equipment requirements for a medical capability.
        
        Args:
            capability: Medical capability/specialty/procedure
            
        Returns:
            Dict with critical, required, and recommended equipment
        """
        # Normalize capability name
        capability_lower = capability.lower().strip()
        
        # Try exact match
        if capability_lower in cls.SKILL_REQUIREMENTS:
            return cls.SKILL_REQUIREMENTS[capability_lower]
        
        # Try procedure-to-specialty mapping
        if capability_lower in cls.PROCEDURE_SPECIALTY_MAP:
            specialty = cls.PROCEDURE_SPECIALTY_MAP[capability_lower]
            if specialty in cls.SKILL_REQUIREMENTS:
                return cls.SKILL_REQUIREMENTS[specialty]
        
        # Try partial matching
        for skill, requirements in cls.SKILL_REQUIREMENTS.items():
            if skill in capability_lower or capability_lower in skill:
                return requirements
        
        # Default empty requirements
        return {"critical": [], "required": [], "recommended": []}
    
    @classmethod
    def validate_equipment(cls, claimed_capability: str, available_equipment: List[str]) -> Dict[str, any]:
        """
        Validate if available equipment meets requirements for claimed capability.
        
        Args:
            claimed_capability: Medical capability being claimed
            available_equipment: List of available equipment
            
        Returns:
            Validation result with missing equipment and severity
        """
        requirements = cls.get_requirements(claimed_capability)
        
        if not requirements or not requirements.get("critical"):
            # No requirements found - cannot validate
            return {
                "valid": None,
                "severity": "unknown",
                "missing_critical": [],
                "missing_required": [],
                "missing_recommended": [],
                "justification": f"No validation rules available for '{claimed_capability}'"
            }
        
        # Normalize available equipment
        available_lower = {eq.lower().strip() for eq in available_equipment}
        
        # Check critical equipment
        missing_critical = []
        for critical_eq in requirements.get("critical", []):
            if not cls._equipment_available(critical_eq, available_lower):
                missing_critical.append(critical_eq)
        
        # Check required equipment
        missing_required = []
        for required_eq in requirements.get("required", []):
            if not cls._equipment_available(required_eq, available_lower):
                missing_required.append(required_eq)
        
        # Check recommended equipment
        missing_recommended = []
        for recommended_eq in requirements.get("recommended", []):
            if not cls._equipment_available(recommended_eq, available_lower):
                missing_recommended.append(recommended_eq)
        
        # Determine severity
        if missing_critical:
            severity = "critical"
            valid = False
            justification = f"{claimed_capability} requires critical equipment: {', '.join(missing_critical)}"
        elif len(missing_required) >= 2:
            severity = "moderate"
            valid = False
            justification = f"{claimed_capability} missing multiple required items: {', '.join(missing_required)}"
        elif missing_required:
            severity = "minor"
            valid = True
            justification = f"{claimed_capability} missing some required equipment but may be operational"
        else:
            severity = "none"
            valid = True
            justification = f"{claimed_capability} has all critical and required equipment"
        
        return {
            "valid": valid,
            "severity": severity,
            "missing_critical": missing_critical,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "justification": justification
        }
    
    @classmethod
    def _equipment_available(cls, required_eq: str, available_eq: Set[str]) -> bool:
        """
        Check if required equipment is available (fuzzy matching).
        
        Args:
            required_eq: Required equipment name
            available_eq: Set of available equipment (normalized)
            
        Returns:
            True if equipment found
        """
        required_lower = required_eq.lower().strip()
        
        # Exact match
        if required_lower in available_eq:
            return True
        
        # Partial match (e.g., "operating room" matches "operating theatre")
        for available in available_eq:
            if required_lower in available or available in required_lower:
                return True
        
        # Synonym matching
        synonyms = {
            "operating room": ["operating theatre", "surgery room", "OR"],
            "anesthesia machine": ["anesthesia", "anaesthesia machine"],
            "ICU": ["intensive care", "critical care", "ICU bed"],
            "dialysis machine": ["hemodialysis machine", "dialysis equipment"],
            "CT scan": ["CT scanner", "computed tomography", "CAT scan"],
            "MRI": ["MRI scanner", "magnetic resonance imaging"]
        }
        
        if required_lower in synonyms:
            for synonym in synonyms[required_lower]:
                if synonym.lower() in available_eq:
                    return True
                for available in available_eq:
                    if synonym.lower() in available:
                        return True
        
        return False
    
    @classmethod
    def get_specialty_keywords(cls, specialty: str) -> List[str]:
        """Get keywords associated with a medical specialty."""
        keywords_map = {
            "cardiology": ["heart", "cardiac", "cardiovascular", "coronary"],
            "neurosurgery": ["brain", "neuro", "spine", "spinal", "neurological"],
            "ophthalmology": ["eye", "vision", "ophthalmic", "ocular", "retinal"],
            "orthopedic": ["bone", "joint", "fracture", "orthopedic", "musculoskeletal"],
            "maternity": ["pregnancy", "delivery", "obstetric", "maternal", "prenatal"],
            "dialysis": ["kidney", "renal", "nephrology", "dialysis"],
            "emergency": ["trauma", "emergency", "urgent", "critical"],
            "hospitalist": ["inpatient", "hospital medicine", "general medicine"]
        }
        return keywords_map.get(specialty.lower(), [])
