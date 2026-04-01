"""
Content Pack Generator - Export questions as JSON packs for offline distribution
"""
import json
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

from app.core.question_localization import prepare_questions_for_delivery

CONTENT_PACKS_DIR = Path("content_packs")
CONTENT_PACKS_DIR.mkdir(exist_ok=True)

async def generate_content_pack(
    questions_collection,
    grade: int,
    subject: str,
    limit: int = 2000,
    language: Optional[str] = None,
) -> Dict:
    """
    Generate a content pack JSON file for offline distribution
    
    Args:
        questions_collection: MongoDB collection
        grade: Grade level
        subject: Subject name
        limit: Maximum questions per pack
    
    Returns:
        Dict with pack info and file path
    """
    # Query approved questions
    query = {
        "approved": True,
        "status": "active",
        "grade": grade,
        "subject": subject
    }
    
    cursor = questions_collection.find(query).limit(limit)
    questions = await cursor.to_list(length=limit)
    
    # Remove MongoDB _id field
    for q in questions:
        q.pop("_id", None)

    questions = await prepare_questions_for_delivery(
        questions,
        target_langs=[language] if language else None,
        queue_missing=bool(language and language != "en"),
        queue_limit=min(limit, 100),
    )
    
    # Create pack metadata
    pack_id = f"grade{grade}_{subject.lower().replace(' ', '_')}_pack"
    pack_data = {
        "pack_id": pack_id,
        "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "grade": grade,
        "subject": subject,
        "question_count": len(questions),
        "generated_at": datetime.now().isoformat(),
        "languages": [language] if language else ["en", "hi", "ta", "te", "or"],
        "questions": questions
    }
    
    # Save to file
    filename = f"{pack_id}_v{pack_data['version']}.json"
    filepath = CONTENT_PACKS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(pack_data, f, ensure_ascii=False, indent=2)
    
    return {
        "pack_id": pack_id,
        "filename": filename,
        "filepath": str(filepath),
        "question_count": len(questions),
        "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2)
    }

async def list_content_packs() -> List[Dict]:
    """List all available content packs"""
    packs = []
    
    for filepath in CONTENT_PACKS_DIR.glob("*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            packs.append({
                "pack_id": data.get("pack_id"),
                "filename": filepath.name,
                "grade": data.get("grade"),
                "subject": data.get("subject"),
                "question_count": data.get("question_count"),
                "version": data.get("version"),
                "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2)
            })
        except Exception as e:
            print(f"Error reading pack {filepath}: {e}")
    
    return sorted(packs, key=lambda x: (x.get("grade", 0), x.get("subject", "")))

async def get_content_pack(pack_id: str) -> Optional[Dict]:
    """Get a specific content pack by ID"""
    for filepath in CONTENT_PACKS_DIR.glob(f"{pack_id}_*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading pack: {e}")
    
    return None
