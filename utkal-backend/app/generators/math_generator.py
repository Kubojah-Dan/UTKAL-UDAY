"""
Procedural math question generator - unlimited questions, zero cost.
Covers Grades 1-12 with grade-appropriate topics, word problems,
spiral curriculum, and Bloom's taxonomy tagging.
"""
import random
import math

GRADE_RANGES = {
    1: (1, 10), 2: (1, 20), 3: (1, 100),
    4: (1, 500), 5: (1, 1000), 6: (1, 5000),
    7: (1, 10000), 8: (1, 50000), 9: (1, 100000),
    10: (1, 1000000), 11: (1, 1000000), 12: (1, 1000000)
}

BLOOM_LEVELS = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}


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
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
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
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
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
            "question": f"What is {a} x {b}?",
            "options": generate_mcq_options(answer, 1, answer * 2),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Multiplication",
            "skill_label": "Multiplication",
            "difficulty": calculate_difficulty(grade),
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
            "hint": f"Add {a} to itself {b} times.",
            "explanation": f"{a} x {b} = {answer}"
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
            "question": f"What is {a} / {b}?",
            "options": generate_mcq_options(answer, 1, max_factor * 2),
            "answer": str(answer),
            "type": "mcq",
            "topic": "Division",
            "skill_label": "Division",
            "difficulty": calculate_difficulty(grade),
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
            "hint": f"How many times does {b} fit into {a}?",
            "explanation": f"{a} / {b} = {answer}"
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
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
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
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
            "hint": f"Multiply {base} by {pct}/100.",
            "explanation": f"{pct}% of {base} = {base} x {pct}/100 = {answer}"
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
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
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
            hint = "Area = length x width"
            exp = f"Area = {d1} x {d2} = {area} cm2"
        elif shape == "square":
            area = d1 * d1
            q = f"Find the area of a square with side {d1} cm."
            ans = str(area)
            hint = "Area = side x side"
            exp = f"Area = {d1}^2 = {area} cm2"
        elif shape == "triangle":
            area = round(0.5 * d1 * d2, 1)
            q = f"Find the area of a triangle with base {d1} cm and height {d2} cm."
            ans = str(area)
            hint = "Area = 1/2 x base x height"
            exp = f"Area = 0.5 x {d1} x {d2} = {area} cm2"
        else:
            area = round(3.14 * d1 * d1, 2)
            q = f"Using pi = 3.14, find the area of a circle with radius {d1} cm."
            ans = str(area)
            hint = "Area = pi x r^2"
            exp = f"Area = 3.14 x {d1}^2 = {area} cm2"

        questions.append({
            "question": q,
            "options": generate_mcq_options(int(float(ans)), 1, int(float(ans)) * 3),
            "answer": ans,
            "type": "mcq",
            "topic": "Geometry",
            "skill_label": "Geometry",
            "difficulty": calculate_difficulty(grade),
            "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
            "hint": hint,
            "explanation": exp
        })
    return questions


# ── Word Problems (cross-subject: Math + Real Life / Science) ──────────────

def _market_problem(grade: int) -> dict:
    items = ["mangoes", "pens", "books", "apples", "notebooks"]
    item = random.choice(items)
    price = random.randint(2, 20) * 5
    qty = random.randint(2, 10)
    total = price * qty
    return {
        "question": f"Ravi buys {qty} {item} at Rs. {price} each. How much does he pay in total?",
        "options": generate_mcq_options(total, 1, total * 2),
        "answer": str(total),
        "type": "mcq", "topic": "Word Problems", "skill_label": "Word Problems",
        "difficulty": calculate_difficulty(grade),
        "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
        "cross_subject": "Math + Real Life",
        "hint": "Multiply price by quantity.",
        "explanation": f"{qty} x Rs.{price} = Rs.{total}",
    }


def _speed_problem(grade: int) -> dict:
    speed = random.choice([40, 50, 60, 80, 100])
    time_h = random.randint(2, 5)
    distance = speed * time_h
    return {
        "question": f"A train travels at {speed} km/h for {time_h} hours. What is the total distance?",
        "options": generate_mcq_options(distance, 1, distance * 2),
        "answer": str(distance),
        "type": "mcq", "topic": "Word Problems", "skill_label": "Word Problems",
        "difficulty": calculate_difficulty(grade),
        "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
        "cross_subject": "Math + Science",
        "hint": "Distance = Speed x Time",
        "explanation": f"Distance = {speed} x {time_h} = {distance} km",
    }


def _sharing_problem(grade: int) -> dict:
    people = random.randint(2, 10)
    each = random.randint(3, 20)
    total = people * each
    return {
        "question": f"{total} sweets are shared equally among {people} children. How many does each child get?",
        "options": generate_mcq_options(each, 1, total),
        "answer": str(each),
        "type": "mcq", "topic": "Word Problems", "skill_label": "Division",
        "difficulty": calculate_difficulty(grade),
        "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
        "cross_subject": "Math + Real Life",
        "hint": "Divide total by number of people.",
        "explanation": f"{total} / {people} = {each}",
    }


def _measurement_problem(grade: int) -> dict:
    length_m = random.randint(2, 20)
    width_m = random.randint(2, 15)
    area = length_m * width_m
    return {
        "question": f"A rectangular field is {length_m} m long and {width_m} m wide. What is its area?",
        "options": generate_mcq_options(area, 1, area * 2),
        "answer": str(area),
        "type": "mcq", "topic": "Measurement", "skill_label": "Geometry",
        "difficulty": calculate_difficulty(grade),
        "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
        "cross_subject": "Math + Science",
        "hint": "Area = length x width",
        "explanation": f"Area = {length_m} x {width_m} = {area} m2",
    }


def _profit_loss_problem(grade: int) -> dict:
    cost = random.randint(50, 500)
    sell = cost + random.randint(10, 100)
    profit = sell - cost
    return {
        "question": f"A shopkeeper buys an item for Rs. {cost} and sells it for Rs. {sell}. What is the profit?",
        "options": generate_mcq_options(profit, 1, profit * 3),
        "answer": str(profit),
        "type": "mcq", "topic": "Word Problems", "skill_label": "Percentages",
        "difficulty": calculate_difficulty(grade),
        "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
        "cross_subject": "Math + Real Life",
        "hint": "Profit = Selling Price - Cost Price",
        "explanation": f"Profit = {sell} - {cost} = {profit}",
    }


def generate_word_problems(grade: int, count: int = 50) -> list:
    """Real-life context word problems (cross-subject)"""
    templates = [_market_problem, _speed_problem, _sharing_problem, _measurement_problem, _profit_loss_problem]
    questions = []
    for i in range(count):
        q = templates[i % len(templates)](grade)
        if q:
            questions.append(q)
    return questions


# ── Bloom's Taxonomy tagged questions ─────────────────────────────────────

def generate_bloom_questions(grade: int, count: int = 30) -> list:
    questions = []
    per_level = max(1, count // 5)

    # Level 1: Remember
    for _ in range(per_level):
        questions.append({
            "question": "What is the formula for the area of a rectangle?",
            "options": ["length x width", "length + width", "2 x (length + width)", "length x length"],
            "answer": "length x width",
            "type": "mcq", "topic": "Geometry", "skill_label": "Geometry",
            "difficulty": "easy", "bloom_level": 1, "bloom_label": BLOOM_LEVELS[1],
            "hint": "Think about what fills the inside of a rectangle.",
            "explanation": "Area = length x width",
        })

    # Level 2: Understand
    for _ in range(per_level):
        a, b = random.randint(5, 9), random.randint(5, 9)
        questions.append({
            "question": f"Why do we carry over when adding {a} + {b} in the ones column?",
            "options": ["Because the sum is 10 or more", "Because the numbers are odd",
                        "Because we always carry over", "Because the sum is less than 10"],
            "answer": "Because the sum is 10 or more",
            "type": "mcq", "topic": "Addition", "skill_label": "Addition",
            "difficulty": "easy", "bloom_level": 2, "bloom_label": BLOOM_LEVELS[2],
            "hint": "Think about place value.",
            "explanation": "We carry over when the digit sum reaches 10 or more.",
        })

    # Level 4: Analyze - find the error
    for _ in range(per_level):
        x = random.randint(2, 10)
        a = random.randint(2, 8)
        b = random.randint(1, 20)
        c = a * x + b
        wrong = x + 1
        questions.append({
            "question": f"A student solved {a}x + {b} = {c} and got x = {wrong}. What is the error?",
            "options": [
                f"They forgot to subtract {b} from both sides first",
                "They divided correctly", "There is no error", f"They should have added {b}"
            ],
            "answer": f"They forgot to subtract {b} from both sides first",
            "type": "mcq", "topic": "Algebra", "skill_label": "Linear Equations",
            "difficulty": "medium", "bloom_level": 4, "bloom_label": BLOOM_LEVELS[4],
            "hint": "Check each step of the solution.",
            "explanation": f"Correct: {a}x = {c}-{b} = {c-b}, x = {x}",
        })

    # Level 5: Evaluate
    for _ in range(per_level):
        questions.append({
            "question": "Which method is most efficient to solve 25 x 4?",
            "options": [
                "Think of it as 100 (25 is a quarter of 100)",
                "Add 25 four times", "Use long multiplication", "Use a calculator"
            ],
            "answer": "Think of it as 100 (25 is a quarter of 100)",
            "type": "mcq", "topic": "Multiplication", "skill_label": "Multiplication",
            "difficulty": "medium", "bloom_level": 5, "bloom_label": BLOOM_LEVELS[5],
            "hint": "Think about number relationships.",
            "explanation": "25 x 4 = 100 because 4 x 25 = 100 (mental math shortcut).",
        })

    # Level 6: Create
    for _ in range(per_level):
        ans = random.randint(10, 50)
        questions.append({
            "question": f"Create a word problem whose answer is {ans}.",
            "options": [
                f"If you have {ans} apples and give away 0, how many remain?",
                f"If you have {ans+5} apples and give away 5, how many remain?",
                f"If you have {ans*2} apples and give away {ans}, how many remain?",
                "All of the above"
            ],
            "answer": "All of the above",
            "type": "mcq", "topic": "Word Problems", "skill_label": "Word Problems",
            "difficulty": "hard", "bloom_level": 6, "bloom_label": BLOOM_LEVELS[6],
            "hint": "Any operation that results in the target number works.",
            "explanation": f"Multiple valid problems can have {ans} as the answer.",
        })

    random.shuffle(questions)
    return questions


# ── Spiral Curriculum ──────────────────────────────────────────────────────

def generate_spiral_questions(grade: int, count: int = 30) -> list:
    """Revisit multiplication topic with increasing complexity across grades"""
    questions = []
    if grade <= 3:
        for _ in range(count):
            a, b = random.randint(2, 9), random.randint(2, 9)
            questions.append({
                "question": f"What is {a} x {b}?",
                "options": generate_mcq_options(a * b, 1, 100),
                "answer": str(a * b), "type": "mcq",
                "topic": "Multiplication", "skill_label": "Multiplication",
                "difficulty": "easy", "spiral_level": "single-digit",
                "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
                "hint": f"Add {a} to itself {b} times.",
                "explanation": f"{a} x {b} = {a * b}",
            })
    elif grade == 4:
        for _ in range(count):
            a, b = random.randint(10, 99), random.randint(10, 99)
            questions.append({
                "question": f"What is {a} x {b}?",
                "options": generate_mcq_options(a * b, 1, a * b * 2),
                "answer": str(a * b), "type": "mcq",
                "topic": "Multiplication", "skill_label": "Multiplication",
                "difficulty": "medium", "spiral_level": "multi-digit",
                "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
                "hint": "Use long multiplication.",
                "explanation": f"{a} x {b} = {a * b}",
            })
    elif grade == 5:
        for _ in range(count):
            a = round(random.uniform(1.1, 9.9), 1)
            b = round(random.uniform(1.1, 4.9), 1)
            ans = round(a * b, 2)
            questions.append({
                "question": f"What is {a} x {b}?",
                "options": [str(ans), str(round(ans + 0.5, 2)), str(round(max(0.1, ans - 0.5), 2)), str(round(ans * 2, 2))],
                "answer": str(ans), "type": "mcq",
                "topic": "Multiplication", "skill_label": "Decimals",
                "difficulty": "medium", "spiral_level": "decimal",
                "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
                "hint": "Multiply as integers, then place the decimal point.",
                "explanation": f"{a} x {b} = {ans}",
            })
    else:
        for _ in range(count):
            a, b = random.randint(2, 8), random.randint(2, 8)
            questions.append({
                "question": f"Simplify: {a}x * {b}x",
                "options": [f"{a*b}x2", f"{a+b}x", f"{a*b}x", f"{a+b}x2"],
                "answer": f"{a*b}x2",
                "type": "mcq", "topic": "Algebra", "skill_label": "Algebra",
                "difficulty": "medium", "spiral_level": "algebraic",
                "bloom_level": 3, "bloom_label": BLOOM_LEVELS[3],
                "hint": "Multiply coefficients and add exponents.",
                "explanation": f"{a}x * {b}x = {a*b}x^2",
            })
    return questions


def generate_questions_for_grade(grade: int, count_per_topic: int = 20) -> list:
    """Generate 2000+ questions for a grade across all topics"""
    all_questions = []

    if grade <= 3:
        all_questions += generate_addition_questions(grade, count_per_topic * 2)
        all_questions += generate_subtraction_questions(grade, count_per_topic * 2)
        if grade >= 2:
            all_questions += generate_multiplication_questions(grade, count_per_topic)
        all_questions += generate_word_problems(grade, count_per_topic * 2)
        all_questions += generate_bloom_questions(grade, count_per_topic)
        all_questions += generate_spiral_questions(grade, count_per_topic)
    elif grade <= 6:
        all_questions += generate_addition_questions(grade, count_per_topic)
        all_questions += generate_subtraction_questions(grade, count_per_topic)
        all_questions += generate_multiplication_questions(grade, count_per_topic * 2)
        all_questions += generate_division_questions(grade, count_per_topic * 2)
        all_questions += generate_fraction_questions(grade, count_per_topic * 2)
        all_questions += generate_percentage_questions(grade, count_per_topic * 2)
        all_questions += generate_word_problems(grade, count_per_topic * 2)
        all_questions += generate_spiral_questions(grade, count_per_topic)
        all_questions += generate_bloom_questions(grade, count_per_topic)
    else:
        all_questions += generate_multiplication_questions(grade, count_per_topic)
        all_questions += generate_division_questions(grade, count_per_topic)
        all_questions += generate_fraction_questions(grade, count_per_topic * 2)
        all_questions += generate_percentage_questions(grade, count_per_topic * 2)
        all_questions += generate_algebra_questions(grade, count_per_topic * 2)
        all_questions += generate_geometry_questions(grade, count_per_topic * 2)
        all_questions += generate_word_problems(grade, count_per_topic * 2)
        all_questions += generate_spiral_questions(grade, count_per_topic)
        all_questions += generate_bloom_questions(grade, count_per_topic)

    random.shuffle(all_questions)
    return all_questions
