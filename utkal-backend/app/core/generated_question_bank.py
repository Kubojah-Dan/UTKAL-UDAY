import hashlib
import math
import random
import re
from typing import Dict, List, Optional, Sequence, Tuple

SUBJECTS: Tuple[str, ...] = ("Mathematics", "English", "Science")
GRADE_MIN = 1
GRADE_MAX = 12

SUBJECT_ALIASES = {
    "math": "Mathematics",
    "maths": "Mathematics",
    "mathematics": "Mathematics",
    "english": "English",
    "science": "Science",
}

SUBJECT_CODES = {"Mathematics": "MTH", "English": "ENG", "Science": "SCI"}
SUBJECT_FROM_CODE = {v: k for k, v in SUBJECT_CODES.items()}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def normalize_subject(subject: Optional[str]) -> Optional[str]:
    if subject is None:
        return None
    key = str(subject).strip().lower()
    if not key:
        return None
    if key in SUBJECT_ALIASES:
        return SUBJECT_ALIASES[key]
    for label in SUBJECTS:
        if key == label.lower():
            return label
    return None


def _stable_seed(*parts: object) -> int:
    payload = "|".join(str(p) for p in parts)
    digest = hashlib.md5(payload.encode("utf8")).hexdigest()
    return int(digest[:12], 16)


def _rng(*parts: object) -> random.Random:
    return random.Random(_stable_seed(*parts))


def _difficulty(grade: int) -> str:
    if grade <= 4:
        return "easy"
    if grade <= 8:
        return "medium"
    return "hard"


def _slug(value: str) -> str:
    return _SLUG_RE.sub("-", value.lower()).strip("-")


def _mcq_options(correct: str, distractors: Sequence[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in [correct, *distractors]:
        key = str(item).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(str(item))
        if len(out) == 4:
            break
    pad_idx = 1
    while len(out) < 4:
        candidate = f"{correct} ({pad_idx})"
        if candidate not in out:
            out.append(candidate)
        pad_idx += 1
    return out


def _build_math_question(grade: int, local_index: int) -> Dict:
    rng = _rng("math", grade, local_index)
    topic_pool = {
        "easy": ["Addition", "Subtraction", "Multiplication", "Shapes", "Measurement"],
        "medium": ["Fractions", "Decimals", "Ratio", "Percentages", "Linear Equations", "Geometry"],
        "hard": ["Algebra", "Functions", "Trigonometry", "Statistics", "Coordinate Geometry"],
    }[_difficulty(grade)]

    topic = rng.choice(topic_pool)
    if grade <= 4:
        op = rng.choice(["+", "-", "*"])
        a = rng.randint(grade + 2, grade * 8 + 14)
        b = rng.randint(grade + 1, grade * 6 + 9)
        if op == "-":
            a, b = max(a, b), min(a, b)
            answer_num = a - b
        elif op == "*":
            a = rng.randint(2, max(3, grade + 4))
            b = rng.randint(2, max(4, grade + 5))
            answer_num = a * b
        else:
            answer_num = a + b
        answer = str(answer_num)
        distractors = [str(answer_num + 1), str(max(0, answer_num - 1)), str(answer_num + rng.randint(2, 6))]
        question = f"What is {a} {op} {b}?"
        hint = "Break the operation into smaller steps."
        explanation = f"Compute {a} {op} {b} to get {answer_num}."
    elif grade <= 8:
        mode = rng.choice(["fraction", "percent", "equation"])
        if mode == "fraction":
            den = rng.randint(4, 12)
            n1 = rng.randint(1, den - 1)
            n2 = rng.randint(1, den - 1)
            num = n1 + n2
            g = math.gcd(num, den)
            num_s, den_s = num // g, den // g
            answer = f"{num_s}/{den_s}"
            question = f"Simplify: {n1}/{den} + {n2}/{den} = ?"
            distractors = [f"{num}/{den}", f"{max(1, num_s - 1)}/{den_s}", f"{num_s}/{max(1, den_s + 1)}"]
            hint = "Add numerators first, then simplify."
            explanation = f"({n1}+{n2})/{den} = {num}/{den}, which simplifies to {answer}."
        elif mode == "percent":
            base = rng.choice([20, 25, 40, 50, 80, 100, 120, 200])
            pct = rng.choice([10, 15, 20, 25, 30, 40, 50, 60])
            ans_val = int(base * pct / 100)
            answer = str(ans_val)
            question = f"What is {pct}% of {base}?"
            distractors = [str(ans_val + 5), str(max(0, ans_val - 5)), str(int(base / 2))]
            hint = "Convert percent to decimal and multiply."
            explanation = f"{pct}% of {base} is {base} x ({pct}/100) = {ans_val}."
        else:
            x = rng.randint(2, 16)
            a = rng.randint(2, 9)
            b = rng.randint(1, 30)
            c = a * x + b
            answer = str(x)
            question = f"Solve for x: {a}x + {b} = {c}"
            distractors = [str(x + 1), str(max(1, x - 1)), str(x + 2)]
            hint = "Move constants first, then divide by the coefficient of x."
            explanation = f"{a}x = {c}-{b} = {c-b}, so x = {(c-b)}/{a} = {x}."
    else:
        mode = rng.choice(["slope", "equation", "circle"])
        if mode == "slope":
            x1 = rng.randint(-5, 5)
            x2 = x1 + rng.randint(1, 6)
            y1 = rng.randint(-6, 6)
            y2 = y1 + rng.randint(-6, 6)
            while y2 == y1:
                y2 = y1 + rng.randint(-6, 6)
            dy = y2 - y1
            dx = x2 - x1
            g = math.gcd(abs(dy), abs(dx))
            n = dy // g
            d = dx // g
            answer = f"{n}/{d}" if d != 1 else str(n)
            question = f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2})."
            distractors = [f"{d}/{n}" if n != 0 else "0", str(round(dy / dx, 2)), str(dy)]
            hint = "Slope m = (y2 - y1) / (x2 - x1)."
            explanation = f"m = ({y2}-{y1})/({x2}-{x1}) = {dy}/{dx} = {answer}."
        elif mode == "circle":
            r = rng.randint(3, 12)
            area = round(3.14 * r * r, 2)
            answer = str(area)
            question = f"Using pi = 3.14, what is the area of a circle with radius {r}?"
            distractors = [str(round(2 * 3.14 * r, 2)), str(round(3.14 * (r + 1) * (r + 1), 2)), str(round(area - 6.28, 2))]
            hint = "Use A = pi r^2."
            explanation = f"A = 3.14 x {r}^2 = {area}."
        else:
            x = rng.randint(-6, 10)
            a = rng.randint(2, 8)
            b = rng.randint(-12, 18)
            c = a * x + b
            answer = str(x)
            question = f"Solve: {a}x + {b} = {c}"
            distractors = [str(x + 2), str(x - 2), str(-x)]
            hint = "Isolate x by undoing +b and then divide by a."
            explanation = f"x = ({c}-{b})/{a} = {x}."

    options = _mcq_options(answer, distractors)
    rng.shuffle(options)
    return {
        "skill_label": topic,
        "question": question,
        "type": "mcq",
        "options": options,
        "answer": answer,
        "accepted_answers": [answer],
        "hint": hint,
        "explanation": explanation,
    }


def _build_english_question(grade: int, local_index: int) -> Dict:
    rng = _rng("english", grade, local_index)
    level = _difficulty(grade)
    if level == "easy":
        names = ["Ava", "Rohan", "Mia", "Liam", "Noah", "Sana"]
        verbs = [("go", "goes"), ("play", "plays"), ("read", "reads"), ("write", "writes")]
        name = rng.choice(names)
        base, third = rng.choice(verbs)
        answer = third
        question = f"Choose the correct verb: \"{name} ___ to school every day.\""
        options = _mcq_options(answer, [base, f"{base}ing", f"{base}ed"])
        skill = "Grammar Basics"
        hint = "A singular subject in simple present usually takes verb+s."
        explanation = f"\"{name}\" is singular, so the correct form is \"{third}\"."
    elif level == "medium":
        pairs = [
            ("benefit", "advantage", ["danger", "delay", "noise"], "Vocabulary"),
            ("ancient", "very old", ["very loud", "very fast", "very large"], "Vocabulary"),
            ("careful", "cautious", ["careless", "lazy", "silent"], "Vocabulary"),
            ("create", "produce", ["destroy", "ignore", "refuse"], "Vocabulary"),
        ]
        word, answer, distract, skill = rng.choice(pairs)
        question = f"Choose the best meaning of \"{word}\"."
        options = _mcq_options(answer, distract)
        hint = "Eliminate clearly unrelated choices first."
        explanation = f"\"{word}\" is closest in meaning to \"{answer}\"."
    else:
        items = [
            {
                "question": "Select the sentence with correct punctuation.",
                "answer": "After the meeting, the team reviewed the action items.",
                "distractors": [
                    "After the meeting the team reviewed, the action items.",
                    "After the meeting the team, reviewed the action items.",
                    "After the meeting the team reviewed the action items",
                ],
                "skill": "Punctuation",
            },
            {
                "question": "Choose the sentence with correct subject-verb agreement.",
                "answer": "Neither the coach nor the players were ready.",
                "distractors": [
                    "Neither the coach nor the players was ready.",
                    "Neither the coach or the players were ready.",
                    "Neither coach nor players is ready.",
                ],
                "skill": "Advanced Grammar",
            },
            {
                "question": "Choose the best transition word: \"The data looked promising; ___, we repeated the experiment.\"",
                "answer": "however",
                "distractors": ["therefore", "meanwhile", "for example"],
                "skill": "Academic Writing",
            },
        ]
        chosen = rng.choice(items)
        question = chosen["question"]
        answer = chosen["answer"]
        options = _mcq_options(answer, chosen["distractors"])
        skill = chosen["skill"]
        hint = "Look for the option that preserves meaning and grammar."
        explanation = f"The best answer is \"{answer}\"."

    rng.shuffle(options)
    return {
        "skill_label": skill,
        "question": question,
        "type": "mcq",
        "options": options,
        "answer": answer,
        "accepted_answers": [answer],
        "hint": hint,
        "explanation": explanation,
    }


def _build_science_question(grade: int, local_index: int) -> Dict:
    rng = _rng("science", grade, local_index)
    level = _difficulty(grade)
    if level == "easy":
        bank = [
            ("Which part of the plant makes food using sunlight?", "Leaves", ["Roots", "Stem", "Flower"], "Plant Science"),
            ("Water changes to ice at what temperature (C)?", "0", ["10", "32", "-10"], "Matter"),
            ("Which force pulls objects toward Earth?", "Gravity", ["Magnetism", "Friction", "Pressure"], "Forces"),
            ("Which gas do humans breathe in for respiration?", "Oxygen", ["Carbon dioxide", "Nitrogen", "Hydrogen"], "Human Body"),
        ]
        question, answer, distractors, skill = rng.choice(bank)
        options = _mcq_options(answer, distractors)
        hint = "Think about the basic science concept taught in primary grades."
        explanation = f"The correct answer is {answer}."
    elif level == "medium":
        mode = rng.choice(["density", "speed", "concept"])
        if mode == "density":
            mass = rng.randint(20, 200)
            volume = rng.choice([2, 4, 5, 8, 10, 20])
            density = round(mass / volume, 2)
            answer = str(density)
            question = f"Find density: mass = {mass} g, volume = {volume} cm^3."
            distractors = [str(round(mass * volume, 2)), str(round(volume / mass, 2)), str(round(density + 1, 2))]
            skill = "Physics"
            hint = "Density = mass / volume."
            explanation = f"Density = {mass}/{volume} = {density} g/cm^3."
            options = _mcq_options(answer, distractors)
        elif mode == "speed":
            distance = rng.randint(60, 300)
            time_h = rng.choice([2, 3, 4, 5, 6])
            speed = round(distance / time_h, 2)
            answer = str(speed)
            question = f"A car travels {distance} km in {time_h} hours. What is its speed (km/h)?"
            distractors = [str(distance * time_h), str(round(distance - time_h, 2)), str(round(speed + 5, 2))]
            skill = "Motion"
            hint = "Speed = distance / time."
            explanation = f"Speed = {distance}/{time_h} = {speed} km/h."
            options = _mcq_options(answer, distractors)
        else:
            bank = [
                ("Which organelle is called the powerhouse of the cell?", "Mitochondria", ["Nucleus", "Ribosome", "Vacuole"], "Biology"),
                ("A solution with pH 2 is:", "Acidic", ["Neutral", "Basic", "Salty"], "Chemistry"),
                ("Which layer protects Earth from harmful UV radiation?", "Ozone layer", ["Troposphere", "Core", "Hydrosphere"], "Earth Science"),
            ]
            question, answer, distractors, skill = rng.choice(bank)
            options = _mcq_options(answer, distractors)
            hint = "Recall the textbook definition."
            explanation = f"The correct choice is {answer}."
    else:
        mode = rng.choice(["force", "energy", "biology"])
        if mode == "force":
            mass = rng.randint(2, 20)
            accel = rng.randint(2, 9)
            force = mass * accel
            answer = str(force)
            question = f"Using F = m*a, find force when m = {mass} kg and a = {accel} m/s^2."
            distractors = [str(mass + accel), str(mass * accel + accel), str(max(1, mass * (accel - 1)))]
            skill = "Mechanics"
            hint = "Multiply mass and acceleration."
            explanation = f"F = {mass} x {accel} = {force} N."
            options = _mcq_options(answer, distractors)
        elif mode == "energy":
            voltage = rng.randint(6, 24)
            current = rng.randint(2, 10)
            power = voltage * current
            answer = str(power)
            question = f"Electric power is P = V*I. If V = {voltage} V and I = {current} A, P = ? W"
            distractors = [str(voltage + current), str(voltage - current), str(power + 10)]
            skill = "Electricity"
            hint = "Power equals voltage multiplied by current."
            explanation = f"P = {voltage} x {current} = {power} W."
            options = _mcq_options(answer, distractors)
        else:
            bank = [
                ("In DNA, which base pairs with Adenine?", "Thymine", ["Cytosine", "Guanine", "Uracil"], "Genetics"),
                ("Which process converts glucose to ATP in cells?", "Cellular respiration", ["Photosynthesis", "Diffusion", "Transpiration"], "Biology"),
                ("Which greenhouse gas is most commonly linked to fossil fuel combustion?", "Carbon dioxide", ["Helium", "Argon", "Neon"], "Environment"),
            ]
            question, answer, distractors, skill = rng.choice(bank)
            options = _mcq_options(answer, distractors)
            hint = "Focus on core high-school biology and environmental science facts."
            explanation = f"The correct answer is {answer}."

    rng.shuffle(options)
    return {
        "skill_label": skill,
        "question": question,
        "type": "mcq",
        "options": options,
        "answer": answer,
        "accepted_answers": [answer],
        "hint": hint,
        "explanation": explanation,
    }


def _build_generated_question(subject: str, grade: int, local_index: int) -> Dict:
    if subject == "Mathematics":
        payload = _build_math_question(grade, local_index)
    elif subject == "English":
        payload = _build_english_question(grade, local_index)
    else:
        payload = _build_science_question(grade, local_index)

    code = SUBJECT_CODES[subject]
    skill_label = payload["skill_label"]
    skill_id = f"gen-{code.lower()}-g{grade}-{_slug(skill_label)}"
    qid = f"GEN-{code}-G{grade}-{local_index:06d}"

    return {
        "id": qid,
        "source": "generated",
        "subject": subject,
        "grade": grade,
        "skill_id": skill_id,
        "skill_label": skill_label,
        "difficulty": _difficulty(grade),
        "language": "en",
        "type": payload["type"],
        "question": payload["question"],
        "options": payload["options"],
        "answer": payload["answer"],
        "accepted_answers": payload["accepted_answers"],
        "hint": payload["hint"],
        "explanation": payload["explanation"],
        "media": [],
        "question_images": [],
        "analysis_images": [],
        "has_image_question": False,
        "has_image_analysis": False,
    }


def _target_pairs(subject: Optional[str], grade: Optional[int]) -> List[Tuple[str, int]]:
    subjects = [normalize_subject(subject)] if subject else list(SUBJECTS)
    if any(s is None for s in subjects):
        return []
    grades = [int(grade)] if grade is not None else list(range(GRADE_MIN, GRADE_MAX + 1))
    return [(s, g) for s in subjects for g in grades if GRADE_MIN <= g <= GRADE_MAX]


def generate_procedural_questions(
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    offset: int = 0,
    limit: int = 200,
) -> List[Dict]:
    pairs = _target_pairs(subject, grade)
    if not pairs or limit <= 0:
        return []

    stride = len(pairs)
    out: List[Dict] = []
    for idx in range(max(0, offset), max(0, offset) + limit):
        pair = pairs[idx % stride]
        local_index = idx // stride
        out.append(_build_generated_question(pair[0], pair[1], local_index))
    return out


def get_generated_question_by_id(question_id: str) -> Optional[Dict]:
    qid = str(question_id or "").strip().upper()
    m = re.match(r"^GEN-([A-Z]{3})-G(\d{1,2})-(\d{1,9})$", qid)
    if not m:
        return None

    code = m.group(1)
    grade = int(m.group(2))
    local_index = int(m.group(3))
    subject = SUBJECT_FROM_CODE.get(code)
    if subject is None or not (GRADE_MIN <= grade <= GRADE_MAX):
        return None

    return _build_generated_question(subject, grade, local_index)
