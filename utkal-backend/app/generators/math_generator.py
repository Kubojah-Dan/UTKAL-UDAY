"""
Procedural math question generator - unlimited questions, zero cost.
Covers Grades 1-12 with grade-appropriate topics.
"""
import random
import math

GRADE_RANGES = {
    1: (1, 10), 2: (1, 20), 3: (1, 100),
    4: (1, 500), 5: (1, 1000), 6: (1, 5000),
    7: (1, 10000), 8: (1, 50000), 9: (1, 100000),
    10: (1, 1000000), 11: (1, 1000000), 12: (1, 1000000)
}


def calculate_difficulty(grade: int) -> str:
    if grade <= 3: return "easy"
    if grade <= 7: return "medium"
    return "hard"


def generate_mcq_options(correct: int, low: int, high: int) -> list:
    distractors = set()
    offsets = [-2, -1, 1, 2, 5, -5, 10, -10, 3, -3]
    random.shuffle(offsets)
    for offset in offsets:
        d = correct + offset
        if d != correct and d >= 0:
            distractors.add(d)
        if len(distractors) >= 3:
            break
    while len(distractors) < 3:
        distractors.add(correct + random.randint(1, 20))
    options = list(distractors)[:3] + [correct]
    random.shuffle(options)
    return [str(o) for o in options]


def generate_addition_questions(grade: int, count: int = 50) -> list:
    low, high = GRADE_RANGES.get(grade, (1, 100))
    questions = []
    for _ in range(count):
        a = random.randint(low, high)
        b = random.randint(low, high)
        answer = a + b
        questions.append({
            "question": f"What is {a} + {b}?",
            "options": generate_mcq_options(answer, low, high * 2),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Addition",
            "skill_label": "Addition",
            "difficulty": calculate_difficulty(grade),
            "hint": f"Start from {a} and count up {b} more.",
            "explanation": f"{a} + {b} = {answer}"
        })
    return questions


def generate_subtraction_questions(grade: int, count: int = 50) -> list:
    low, high = GRADE_RANGES.get(grade, (1, 100))
    questions = []
    for _ in range(count):
        b = random.randint(low, high)
        a = random.randint(b, high + b)
        answer = a - b
        questions.append({
            "question": f"What is {a} - {b}?",
            "options": generate_mcq_options(answer, 0, high),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Subtraction",
            "skill_label": "Subtraction",
            "difficulty": calculate_difficulty(grade),
            "hint": f"Start from {a} and count down {b}.",
            "explanation": f"{a} - {b} = {answer}"
        })
    return questions


def generate_multiplication_questions(grade: int, count: int = 50) -> list:
    max_factor = min(grade * 3, 20)
    questions = []
    for _ in range(count):
        a = random.randint(2, max_factor)
        b = random.randint(2, max_factor)
        answer = a * b
        questions.append({
            "question": f"What is {a} × {b}?",
            "options": generate_mcq_options(answer, 1, answer * 2),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Multiplication",
            "skill_label": "Multiplication",
            "difficulty": calculate_difficulty(grade),
            "hint": f"Add {a} to itself {b} times.",
            "explanation": f"{a} × {b} = {answer}"
        })
    return questions


def generate_division_questions(grade: int, count: int = 50) -> list:
    max_factor = min(grade * 3, 20)
    questions = []
    for _ in range(count):
        b = random.randint(2, max_factor)
        answer = random.randint(2, max_factor)
        a = b * answer
        questions.append({
            "question": f"What is {a} ÷ {b}?",
            "options": generate_mcq_options(answer, 1, max_factor * 2),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Division",
            "skill_label": "Division",
            "difficulty": calculate_difficulty(grade),
            "hint": f"How many times does {b} fit into {a}?",
            "explanation": f"{a} ÷ {b} = {answer}"
        })
    return questions


def generate_fraction_questions(grade: int, count: int = 30) -> list:
    questions = []
    for _ in range(count):
        den = random.randint(2, 12)
        n1 = random.randint(1, den - 1)
        n2 = random.randint(1, den - 1)
        num = n1 + n2
        g = math.gcd(num, den)
        ans = f"{num // g}/{den // g}" if (num // g) != (den // g) else "1"
        questions.append({
            "question": f"Simplify: {n1}/{den} + {n2}/{den} = ?",
            "options": [ans, f"{num}/{den}", f"{max(1,num//g-1)}/{den//g}", f"{num//g}/{max(1,den//g+1)}"],
            "answer": ans,
            "type": "mcq",
            "topic": "Fractions",
            "skill_label": "Fractions",
            "difficulty": calculate_difficulty(grade),
            "hint": "Add numerators, keep denominator, then simplify.",
            "explanation": f"({n1}+{n2})/{den} = {num}/{den} = {ans}"
        })
    return questions


def generate_percentage_questions(grade: int, count: int = 30) -> list:
    questions = []
    bases = [20, 25, 40, 50, 80, 100, 120, 200, 500]
    pcts = [10, 15, 20, 25, 30, 40, 50, 60, 75]
    for _ in range(count):
        base = random.choice(bases)
        pct = random.choice(pcts)
        answer = int(base * pct / 100)
        questions.append({
            "question": f"What is {pct}% of {base}?",
            "options": generate_mcq_options(answer, 1, base),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Percentages",
            "skill_label": "Percentages",
            "difficulty": calculate_difficulty(grade),
            "hint": f"Multiply {base} by {pct}/100.",
            "explanation": f"{pct}% of {base} = {base} × {pct}/100 = {answer}"
        })
    return questions


def generate_algebra_questions(grade: int, count: int = 30) -> list:
    questions = []
    for _ in range(count):
        x = random.randint(1, 20)
        a = random.randint(2, 10)
        b = random.randint(1, 30)
        c = a * x + b
        questions.append({
            "question": f"Solve for x: {a}x + {b} = {c}",
            "options": generate_mcq_options(x, 1, 30),
            "answer": str(x),
            "type": "mcq",
            "topic": "Algebra",
            "skill_label": "Linear Equations",
            "difficulty": calculate_difficulty(grade),
            "hint": f"Subtract {b} from both sides, then divide by {a}.",
            "explanation": f"{a}x = {c} - {b} = {c-b}, so x = {c-b}/{a} = {x}"
        })
    return questions


def generate_geometry_questions(grade: int, count: int = 30) -> list:
    questions = []
    shapes = [
        ("rectangle", lambda: (random.randint(3, 20), random.randint(3, 20))),
        ("square", lambda: (random.randint(3, 20), None)),
        ("triangle", lambda: (random.randint(3, 20), random.randint(3, 20))),
        ("circle", lambda: (random.randint(2, 15), None)),
    ]
    for _ in range(count):
        shape, dims_fn = random.choice(shapes)
        d1, d2 = dims_fn()
        if shape == "rectangle":
            area = d1 * d2
            q = f"Find the area of a rectangle with length {d1} cm and width {d2} cm."
            ans = str(area)
            hint = "Area = length × width"
            exp = f"Area = {d1} × {d2} = {area} cm²"
        elif shape == "square":
            area = d1 * d1
            q = f"Find the area of a square with side {d1} cm."
            ans = str(area)
            hint = "Area = side × side"
            exp = f"Area = {d1}² = {area} cm²"
        elif shape == "triangle":
            area = round(0.5 * d1 * d2, 1)
            q = f"Find the area of a triangle with base {d1} cm and height {d2} cm."
            ans = str(area)
            hint = "Area = ½ × base × height"
            exp = f"Area = 0.5 × {d1} × {d2} = {area} cm²"
        else:
            area = round(3.14 * d1 * d1, 2)
            q = f"Using π = 3.14, find the area of a circle with radius {d1} cm."
            ans = str(area)
            hint = "Area = π × r²"
            exp = f"Area = 3.14 × {d1}² = {area} cm²"

        questions.append({
            "question": q,
            "options": generate_mcq_options(int(float(ans)), 1, int(float(ans)) * 3),
            "answer": ans,
            "type": "mcq",
            "topic": "Geometry",
            "skill_label": "Geometry",
            "difficulty": calculate_difficulty(grade),
            "hint": hint,
            "explanation": exp
        })
    return questions


def generate_questions_for_grade(grade: int, count_per_topic: int = 20) -> list:
    """Generate a full set of questions for a grade"""
    all_questions = []

    if grade <= 3:
        all_questions += generate_addition_questions(grade, count_per_topic)
        all_questions += generate_subtraction_questions(grade, count_per_topic)
        if grade >= 2:
            all_questions += generate_multiplication_questions(grade, count_per_topic)
    elif grade <= 6:
        all_questions += generate_addition_questions(grade, count_per_topic // 2)
        all_questions += generate_subtraction_questions(grade, count_per_topic // 2)
        all_questions += generate_multiplication_questions(grade, count_per_topic)
        all_questions += generate_division_questions(grade, count_per_topic)
        all_questions += generate_fraction_questions(grade, count_per_topic)
        all_questions += generate_percentage_questions(grade, count_per_topic)
    else:
        all_questions += generate_multiplication_questions(grade, count_per_topic // 2)
        all_questions += generate_division_questions(grade, count_per_topic // 2)
        all_questions += generate_fraction_questions(grade, count_per_topic)
        all_questions += generate_percentage_questions(grade, count_per_topic)
        all_questions += generate_algebra_questions(grade, count_per_topic)
        all_questions += generate_geometry_questions(grade, count_per_topic)

    random.shuffle(all_questions)
    return all_questions
