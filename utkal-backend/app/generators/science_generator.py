"""
Template-based Science and Environmental Science (EVS) question generator.
Covers:
  - EVS (Environmental Studies) — Grades 1–5
  - Science — Grades 6–10

All questions are procedurally generated from templates with randomized
variable slots, giving effectively unlimited unique questions offline.
"""
import random
import uuid

BLOOM_LEVELS = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze"}


def _mcq(question, answer, distractors, topic, skill, grade, difficulty="medium", bloom=1, hint="", explanation=""):
    opts = list(distractors[:3]) + [answer]
    random.shuffle(opts)
    return {
        "id": str(uuid.uuid4()),
        "question": question,
        "answer": answer,
        "accepted_answers": [answer],
        "options": opts,
        "type": "mcq",
        "subject": "Science" if grade >= 6 else "Environmental Science",
        "topic": topic,
        "skill_label": skill,
        "grade": grade,
        "difficulty": difficulty,
        "bloom_level": bloom,
        "bloom_label": BLOOM_LEVELS[bloom],
        "hint": hint,
        "explanation": explanation,
    }


# ── EVS Templates (Grades 1–5) ─────────────────────────────────────────────

EVS_ANIMALS = ["dog", "cat", "cow", "elephant", "lion", "rabbit", "parrot", "fish", "frog", "eagle"]
EVS_PLANTS  = ["mango", "banyan", "neem", "rose", "lotus", "coconut", "bamboo", "sunflower", "tulsi"]
EVS_FOODS   = ["rice", "wheat", "dal", "vegetables", "fruits", "milk", "eggs"]
EVS_COMMUNITY = ["doctor", "teacher", "farmer", "police officer", "firefighter", "postman", "nurse"]

def _evs_animal_habitat(grade):
    habitats = {
        "fish": ("water", "river/sea"), "frog": ("land and water", "pond"),
        "eagle": ("land and air", "trees/cliffs"), "lion": ("land", "forest"),
        "dog": ("land", "human homes"), "rabbit": ("land", "burrows"),
        "parrot": ("land and air", "trees"), "elephant": ("land", "forest"),
    }
    animal = random.choice(list(habitats.keys()))
    hab, place = habitats[animal]
    distractors = [h for h in ["water", "land", "air", "desert", "caves"] if h != hab]
    return _mcq(
        f"Where does a {animal} live?", place,
        [f"{d}" for d in distractors[:3]],
        "Animals and Habitats", "Habitats", grade, "easy", 1,
        f"Think about what environment a {animal} needs.",
        f"A {animal} lives in {place} ({hab}).",
    )

def _evs_plant_part(grade):
    parts = {
        "photosynthesis": ("leaf", ["root", "stem", "flower"]),
        "absorbing water": ("root", ["leaf", "stem", "fruit"]),
        "carrying water": ("stem", ["root", "leaf", "seed"]),
        "making seeds": ("flower", ["leaf", "root", "stem"]),
    }
    function, (part, distractors) = random.choice(list(parts.items()))
    return _mcq(
        f"Which part of a plant is responsible for {function}?",
        part, distractors,
        "Plants", "Plant Parts", grade, "easy", 1,
        f"Each plant part has a special job.",
        f"The {part} is responsible for {function}.",
    )

def _evs_water_cycle(grade):
    stages = [
        ("Evaporation", "Water turns into water vapour due to sunlight", ["Condensation", "Precipitation", "Collection"]),
        ("Condensation", "Water vapour cools and forms clouds", ["Evaporation", "Precipitation", "Runoff"]),
        ("Precipitation", "Water falls back to Earth as rain or snow", ["Evaporation", "Condensation", "Infiltration"]),
    ]
    name, desc, distractors = random.choice(stages)
    return _mcq(
        f"Which stage of the water cycle is: '{desc}'?",
        name, distractors,
        "Water Cycle", "Water Cycle", grade, "medium", 2,
        "Remember the four stages: Evaporation → Condensation → Precipitation → Collection.",
        f"{name}: {desc}",
    )

def _evs_community_helper(grade):
    helpers = {
        "doctor": "treats sick people",
        "teacher": "educates children",
        "farmer": "grows food for us",
        "police officer": "maintains law and order",
        "firefighter": "puts out fires",
        "postman": "delivers letters and parcels",
        "nurse": "assists doctors and cares for patients",
    }
    person, job = random.choice(list(helpers.items()))
    distractors = [p for p in helpers if p != person][:3]
    return _mcq(
        f"Who {job}?", person, distractors,
        "Community Helpers", "Community Helpers", grade, "easy", 1,
        "Think about what job each community helper does.",
        f"A {person} {job}.",
    )

def _evs_seasons(grade):
    seasons = {
        "Summer": ("March–June", "hot and dry", ["Winter", "Monsoon", "Spring"]),
        "Monsoon": ("June–September", "rainy", ["Summer", "Winter", "Autumn"]),
        "Winter": ("November–February", "cold", ["Summer", "Monsoon", "Autumn"]),
    }
    season, (months, desc, distractors) = random.choice(list(seasons.items()))
    return _mcq(
        f"Which season is known for being {desc} in India?",
        season, distractors,
        "Seasons", "Seasons", grade, "easy", 1,
        "India has three main seasons: Summer, Monsoon, and Winter.",
        f"{season} season ({months}) is {desc}.",
    )

def _evs_food_source(grade):
    items = [
        ("milk", "cow/buffalo", "animal"),
        ("rice", "paddy plant", "plant"),
        ("eggs", "hen", "animal"),
        ("vegetables", "plants", "plant"),
        ("honey", "bees", "animal"),
        ("wheat", "wheat plant", "plant"),
    ]
    food, source, category = random.choice(items)
    distractors = [s for _, s, _ in items if s != source][:3]
    return _mcq(
        f"Where does {food} come from?",
        source, distractors,
        "Food Sources", "Food Sources", grade, "easy", 1,
        f"Think: do we get {food} from a plant or an animal?",
        f"{food.capitalize()} comes from {source} ({category} source).",
    )


def generate_evs_questions(grade: int, count: int = 100) -> list:
    """Generate EVS questions for Grades 1–5."""
    templates = [
        _evs_animal_habitat,
        _evs_plant_part,
        _evs_water_cycle,
        _evs_community_helper,
        _evs_seasons,
        _evs_food_source,
    ]
    questions = []
    for i in range(count):
        try:
            q = templates[i % len(templates)](grade)
            questions.append(q)
        except Exception:
            continue
    return questions


# ── Science Templates (Grades 6–10) ───────────────────────────────────────

ELEMENTS = {
    "Water":            ("H₂O",  2),
    "Carbon Dioxide":   ("CO₂",  2),
    "Oxygen":           ("O₂",   2),
    "Hydrogen":         ("H₂",   2),
    "Sodium Chloride":  ("NaCl", 2),
    "Ammonia":          ("NH₃",  2),
    "Methane":          ("CH₄",  2),
    "Sulfuric Acid":    ("H₂SO₄",2),
    "Hydrochloric Acid":("HCl",  2),
}

def _sci_formula(grade):
    substances = list(ELEMENTS.keys())
    name = random.choice(substances)
    formula = ELEMENTS[name][0]
    distractors = [ELEMENTS[s][0] for s in substances if s != name][:3]
    return _mcq(
        f"What is the chemical formula of {name}?",
        formula, distractors,
        "Chemical Formulas", "Chemistry Basics", grade, "medium", 1,
        f"Remember: {name} = {formula}",
        f"The chemical formula of {name} is {formula}.",
    )

def _sci_cell(grade):
    facts = [
        ("cell", "the basic unit of life", ["atom", "molecule", "tissue"]),
        ("nucleus", "the control centre of the cell", ["cell wall", "cytoplasm", "mitochondria"]),
        ("mitochondria", "the powerhouse of the cell", ["nucleus", "ribosome", "vacuole"]),
        ("chloroplast", "the site of photosynthesis in plant cells", ["mitochondria", "nucleus", "vacuole"]),
    ]
    organelle, function, distractors = random.choice(facts)
    return _mcq(
        f"Which cell organelle is known as {function}?",
        organelle, distractors,
        "Cell Biology", "Biology", grade, "medium", 1,
        "Review the functions of key cell organelles.",
        f"The {organelle} is {function}.",
    )

def _sci_physics_law(grade):
    # Newton's laws with randomised force/mass/acceleration values
    mass = random.randint(2, 20)
    force = random.randint(4, 40)
    accel = round(force / mass, 2)
    q_type = random.choice(["find_a", "find_f", "find_m"])
    if q_type == "find_a":
        ans = str(accel)
        q = f"A force of {force} N acts on a mass of {mass} kg. What is the acceleration?"
        distractors = [str(round(accel+1,2)), str(round(accel-0.5,2)), str(round(accel*2,2))]
        hint = "Use Newton's 2nd law: F = ma, so a = F/m"
        exp = f"a = {force}/{mass} = {accel} m/s²"
    elif q_type == "find_f":
        ans = str(force)
        q = f"A {mass} kg object accelerates at {accel} m/s². What force acted on it?"
        distractors = [str(force+4), str(force-2), str(force*2)]
        hint = "F = m × a"
        exp = f"F = {mass} × {accel} = {force} N"
    else:
        ans = str(mass)
        q = f"A force of {force} N produces an acceleration of {accel} m/s². What is the mass?"
        distractors = [str(mass+3), str(mass-1), str(mass*2)]
        hint = "m = F / a"
        exp = f"m = {force}/{accel} = {mass} kg"
    distractors = [d for d in distractors if d != ans][:3]
    return _mcq(q, ans, distractors, "Forces and Motion", "Physics", grade, "medium", 3, hint, exp)

def _sci_photosynthesis(grade):
    questions = [
        ("What gas do plants absorb during photosynthesis?", "Carbon dioxide (CO₂)", ["Oxygen (O₂)", "Nitrogen (N₂)", "Hydrogen (H₂)"], "Plants absorb CO₂ and release O₂.", "Plants take in CO₂ for photosynthesis."),
        ("What gas is released by plants during photosynthesis?", "Oxygen (O₂)", ["Carbon dioxide (CO₂)", "Nitrogen (N₂)", "Water vapour"], "Plants release O₂ as a by-product.", "Photosynthesis releases O₂ as a by-product."),
        ("What is the source of energy for photosynthesis?", "Sunlight", ["Wind", "Water", "Soil"], "Photosynthesis needs light energy.", "Sunlight provides the energy for photosynthesis."),
        ("What is the formula for photosynthesis products?", "Glucose + Oxygen", ["CO₂ + Water", "Starch + CO₂", "Protein + Oxygen"], "Think about what plants produce.", "Plants produce glucose and oxygen via photosynthesis."),
    ]
    q, ans, dis, hint, exp = random.choice(questions)
    return _mcq(q, ans, dis, "Photosynthesis", "Biology", grade, "medium", 1, hint, exp)

def _sci_electricity(grade):
    scenarios = [
        ("conductor", ["iron", "copper", "aluminium"], ["rubber", "plastic", "wood"], "allows electricity to flow through it"),
        ("insulator", ["rubber", "plastic", "wood"], ["iron", "copper", "aluminium"], "does not allow electricity to flow through it"),
    ]
    kind, examples, anti_examples, desc = random.choice(scenarios)
    item = random.choice(examples)
    distractors = anti_examples
    return _mcq(
        f"{item.capitalize()} is an example of a/an ___ because it {desc}.",
        kind.capitalize(), [k.capitalize() for k in ["conductor", "insulator", "semiconductor", "resistor"] if k != kind],
        "Electricity", "Physics", grade, "medium", 2,
        "Conductors allow current to flow; insulators block it.",
        f"{item.capitalize()} is a {kind}.",
    )

def _sci_classification(grade):
    kingdoms = [
        ("Monera", "bacteria", ["Fungi", "Plantae", "Animalia"]),
        ("Fungi", "mushrooms and moulds", ["Monera", "Plantae", "Animalia"]),
        ("Plantae", "plants", ["Animalia", "Fungi", "Monera"]),
        ("Animalia", "animals", ["Plantae", "Fungi", "Monera"]),
        ("Protista", "single-celled organisms like amoeba", ["Animalia", "Plantae", "Fungi"]),
    ]
    kingdom, example, distractors = random.choice(kingdoms)
    return _mcq(
        f"To which kingdom do {example} belong?",
        kingdom, distractors,
        "Biological Classification", "Biology", grade, "medium", 1,
        "Review the 5 kingdoms of classification.",
        f"{example.capitalize()} belong to the kingdom {kingdom}.",
    )


def generate_science_questions(grade: int, count: int = 100) -> list:
    """Generate Science questions for Grades 6–10."""
    templates = [
        _sci_formula,
        _sci_cell,
        _sci_physics_law,
        _sci_photosynthesis,
        _sci_electricity,
        _sci_classification,
    ]
    questions = []
    for i in range(count):
        try:
            q = templates[i % len(templates)](grade)
            questions.append(q)
        except Exception:
            continue
    return questions


def generate_questions_for_grade(grade: int, count: int = 150) -> list:
    """Entry point: returns EVS (Gr 1–5) or Science (Gr 6–10) questions."""
    if grade <= 5:
        return generate_evs_questions(grade, count)
    else:
        return generate_science_questions(grade, count)


if __name__ == "__main__":
    import json
    print("Testing Science/EVS Generator (Grade 3)...")
    questions = generate_questions_for_grade(3, count=5)
    print(f"Generated {len(questions)} questions.")
    if questions:
        print(json.dumps(questions[0], indent=2))
