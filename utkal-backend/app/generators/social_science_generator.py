"""
Template-based Social Science question generator.
Covers Grades 6–10 NCERT curriculum:
  - History  : key events, dates, rulers, movements
  - Geography : capitals, rivers, mountains, states
  - Civics    : constitutional articles, rights, duties, institutions
"""
import random
import uuid

BLOOM_LEVELS = {1: "Remember", 2: "Understand", 3: "Apply"}


def _mcq(question, answer, distractors, topic, skill, grade,
         difficulty="medium", bloom=1, hint="", explanation=""):
    opts = list(distractors[:3]) + [answer]
    random.shuffle(opts)
    return {
        "id": str(uuid.uuid4()),
        "question": question,
        "answer": answer,
        "accepted_answers": [answer],
        "options": opts,
        "type": "mcq",
        "subject": "Social Science",
        "topic": topic,
        "skill_label": skill,
        "grade": grade,
        "difficulty": difficulty,
        "bloom_level": bloom,
        "bloom_label": BLOOM_LEVELS[bloom],
        "hint": hint,
        "explanation": explanation,
    }


# ── HISTORY ────────────────────────────────────────────────────────────────

HISTORY_FACTS = [
    ("In which year did India gain independence?", "1947",
     ["1945", "1950", "1942"], "India's independence", "History", 7,
     "Think about the year World War II ended and shortly after.",
     "India became independent on August 15, 1947."),

    ("Who gave the slogan 'Do or Die' during the Quit India Movement?", "Mahatma Gandhi",
     ["Jawaharlal Nehru", "Subhas Chandra Bose", "Bhagat Singh"], "Freedom Movement", "History", 8,
     "The slogan was part of the 1942 movement.",
     "Mahatma Gandhi gave the slogan 'Do or Die' in 1942."),

    ("The Battle of Plassey (1757) was fought between the British and ___.", "Nawab Siraj-ud-Daulah",
     ["Tipu Sultan", "Hyder Ali", "Nizam of Hyderabad"], "British Expansion", "History", 8,
     "The battle took place in Bengal.",
     "The Battle of Plassey (1757) was fought between Robert Clive and Siraj-ud-Daulah."),

    ("Who founded the Indian National Congress in 1885?", "A.O. Hume",
     ["Bal Gangadhar Tilak", "Dadabhai Naoroji", "Gopal Krishna Gokhale"], "National Movement", "History", 8,
     "He was a British civil servant.",
     "A.O. Hume (Allan Octavian Hume) founded the Indian National Congress in 1885."),

    ("The Jallianwala Bagh massacre took place in which year?", "1919",
     ["1905", "1915", "1930"], "Colonial History", "History", 8,
     "It happened after the Rowlatt Act was passed.",
     "The Jallianwala Bagh massacre occurred on April 13, 1919, in Amritsar."),

    ("Which Mughal emperor built the Taj Mahal?", "Shah Jahan",
     ["Akbar", "Aurangzeb", "Babur"], "Mughal Empire", "History", 7,
     "He built it as a memorial for his wife Mumtaz Mahal.",
     "Shah Jahan built the Taj Mahal in memory of his wife Mumtaz Mahal."),

    ("In which year was the Indian Constitution adopted?", "1949",
     ["1947", "1950", "1952"], "Constitution", "History", 9,
     "It was adopted on November 26, 1949 and came into effect on January 26, 1950.",
     "The Constitution of India was adopted on November 26, 1949."),

    ("Who was the first Prime Minister of India?", "Jawaharlal Nehru",
     ["Sardar Patel", "Rajendra Prasad", "Mahatma Gandhi"], "Post-Independence", "History", 6,
     "He served from 1947 to 1964.",
     "Jawaharlal Nehru was India's first Prime Minister (1947–1964)."),

    ("The Sepoy Mutiny (First War of Independence) occurred in which year?", "1857",
     ["1847", "1867", "1885"], "Colonial History", "History", 8,
     "It began at Meerut cantonment.",
     "The Revolt of 1857 (Sepoy Mutiny) began on May 10, 1857, at Meerut."),

    ("Who was the founder of the Maratha Empire?", "Shivaji Maharaj",
     ["Balaji Baji Rao", "Sambhaji", "Peshwa Baji Rao"], "Maratha Empire", "History", 7,
     "He established Swaraj (self-rule) in the Deccan region.",
     "Chhatrapati Shivaji Maharaj founded the Maratha Empire in the 17th century."),
]


def _history_question(grade):
    candidates = [f for f in HISTORY_FACTS if f[5] <= grade + 1]
    if not candidates:
        candidates = HISTORY_FACTS
    q, ans, dis, topic, skill, _, hint, exp = random.choice(candidates)
    return _mcq(q, ans, dis, topic, skill, grade, "medium", 1, hint, exp)


# ── GEOGRAPHY ──────────────────────────────────────────────────────────────

CAPITALS = {
    "India": "New Delhi", "France": "Paris", "Japan": "Tokyo",
    "China": "Beijing", "USA": "Washington D.C.", "Russia": "Moscow",
    "UK": "London", "Australia": "Canberra", "Brazil": "Brasília",
    "Canada": "Ottawa", "Germany": "Berlin", "South Africa": "Pretoria",
}

STATE_CAPITALS = {
    "Odisha": "Bhubaneswar", "Tamil Nadu": "Chennai", "Maharashtra": "Mumbai",
    "Karnataka": "Bengaluru", "West Bengal": "Kolkata", "Rajasthan": "Jaipur",
    "Gujarat": "Gandhinagar", "Uttar Pradesh": "Lucknow", "Punjab": "Chandigarh",
    "Kerala": "Thiruvananthapuram",
}

RIVERS = {
    "Ganga": "Uttarakhand (Gangotri Glacier)", "Yamuna": "Yamunotri Glacier",
    "Brahmaputra": "Tibet (Angsi Glacier)", "Godavari": "Maharashtra (Trimbakeshwar)",
    "Krishna": "Maharashtra (Mahabaleshwar)", "Nile": "Uganda/Ethiopia",
    "Amazon": "Peru (Andes Mountains)", "Thames": "Gloucestershire, England",
}

MOUNTAINS = {
    "Mt. Everest": ("8848 m", "Nepal/China border", "world's highest peak"),
    "Kanchenjunga": ("8586 m", "Sikkim/Nepal border", "third highest peak"),
    "K2": ("8611 m", "Pakistan/China border", "second highest peak"),
    "Himalayan Range": ("across India, Nepal, Bhutan", "northern India", "largest mountain range in Asia"),
    "Aravalli Range": ("Rajasthan and Haryana", "northwestern India", "oldest fold mountains in India"),
    "Western Ghats": ("Maharashtra to Kerala", "western coast of India", "UNESCO World Heritage Site"),
}

def _geo_capital(grade):
    if grade >= 8:
        country, capital = random.choice(list(CAPITALS.items()))
        distractors = [c for c, cap in CAPITALS.items() if cap != capital and c != country][:3]
        dis = [CAPITALS[c] for c in distractors]
    else:
        state, capital = random.choice(list(STATE_CAPITALS.items()))
        dis = [c for c in STATE_CAPITALS.values() if c != capital][:3]
        country = state
    ans = capital
    return _mcq(
        f"What is the capital of {country}?", ans, dis,
        "Political Geography", "Geography", grade, "easy", 1,
        f"Think about major cities in {country}.",
        f"The capital of {country} is {ans}.",
    )

def _geo_river(grade):
    river, origin = random.choice(list(RIVERS.items()))
    dis_origins = [o for r, o in RIVERS.items() if r != river][:3]
    return _mcq(
        f"Where does the {river} river originate?",
        origin, dis_origins,
        "Rivers", "Geography", grade, "medium", 1,
        f"Think about the geographical region where {river} starts.",
        f"The {river} river originates in {origin}.",
    )

def _geo_mountain(grade):
    mt, (height, location, desc) = random.choice(list(MOUNTAINS.items()))
    dis = [l for m, (h, l, d) in MOUNTAINS.items() if m != mt][:3]
    return _mcq(
        f"Where is {mt} located?", location, dis,
        "Physical Geography", "Geography", grade, "medium", 1,
        f"{mt} is known as the {desc}.",
        f"{mt} ({height}) is located on the {location}.",
    )


# ── CIVICS ─────────────────────────────────────────────────────────────────

FUNDAMENTAL_RIGHTS = [
    ("Article 14", "Right to Equality", ["Right to Freedom", "Right against Exploitation", "Cultural Rights"]),
    ("Article 19", "Right to Freedom (speech, assembly, movement)", ["Right to Equality", "Right to Education", "Right to Life"]),
    ("Article 21", "Right to Life and Personal Liberty", ["Right to Equality", "Right to Freedom", "Right against Exploitation"]),
    ("Article 21A", "Right to Education (for children 6–14 years)", ["Right to Life", "Right to Equality", "Right to Freedom"]),
    ("Article 32", "Right to Constitutional Remedies (Dr. Ambedkar called it the 'Heart of the Constitution')",
     ["Right to Equality", "Right to Life", "Right to Education"]),
]

DPSP_FACTS = [
    ("Which part of the Constitution contains Directive Principles of State Policy?",
     "Part IV", ["Part II", "Part III", "Part V"],
     "Part III contains Fundamental Rights; Part IV contains DPSPs."),
    ("Directive Principles of State Policy are ___.",
     "non-justiciable (not enforceable by courts)",
     ["justiciable", "fundamental", "legally binding"],
     "Unlike Fundamental Rights, DPSPs cannot be enforced by courts."),
]

INSTITUTIONS = [
    ("Which body is responsible for conducting Lok Sabha elections in India?",
     "Election Commission of India",
     ["Supreme Court", "Parliament", "Cabinet"],
     "The Election Commission is an autonomous constitutional body.",
     "The Election Commission of India conducts all elections to Parliament and State Legislatures."),

    ("Who is the constitutional head of the Government of India?",
     "President of India",
     ["Prime Minister", "Chief Justice", "Speaker of Lok Sabha"],
     "The President is the ceremonial head; the PM is the executive head.",
     "The President of India is the constitutional head of the state."),

    ("Which court is at the apex of the Indian judicial system?",
     "Supreme Court of India",
     ["High Court", "District Court", "Session Court"],
     "The Supreme Court is the highest court in India.",
     "The Supreme Court of India is the apex court and final interpreter of the Constitution."),
]

def _civics_rights(grade):
    article, right, distractors = random.choice(FUNDAMENTAL_RIGHTS)
    return _mcq(
        f"What does {article} of the Indian Constitution guarantee?",
        right, distractors,
        "Fundamental Rights", "Civics", grade, "medium", 1,
        f"Review the Fundamental Rights under Part III of the Constitution.",
        f"{article} guarantees the {right}.",
    )

def _civics_institutions(grade):
    q, ans, dis, hint, exp = random.choice(INSTITUTIONS)
    return _mcq(q, ans, dis, "Government Institutions", "Civics", grade, "medium", 1, hint, exp)

def _civics_local_govt(grade):
    facts = [
        ("Which body governs a village in rural India?", "Gram Panchayat",
         ["Municipality", "Zila Parishad", "City Corporation"],
         "Rural local governance has 3 tiers: Gram Panchayat, Panchayat Samiti, Zila Parishad.",
         "The Gram Panchayat is the lowest tier of rural local governance in India."),
        ("The 73rd Constitutional Amendment Act (1992) gave constitutional status to ___.", "Panchayati Raj Institutions",
         ["Municipalities", "Parliament", "High Courts"],
         "1992 is a landmark year for local self-governance in India.",
         "The 73rd Amendment gave constitutional status to Panchayati Raj institutions."),
        ("Which article of the Constitution relates to the Panchayati Raj system?", "Article 243",
         ["Article 32", "Article 14", "Article 370"],
         "Part IX of the Constitution deals with Panchayats.",
         "Article 243 (Part IX) of the Indian Constitution deals with Panchayati Raj."),
    ]
    q, ans, dis, hint, exp = random.choice(facts)
    return _mcq(q, ans, dis, "Local Governance", "Civics", grade, "medium", 2, hint, exp)


def generate_social_science_questions(grade: int, count: int = 100) -> list:
    """Generate Social Science questions for Grades 6–10."""
    templates = [
        _history_question,
        _geo_capital,
        _geo_river,
        _geo_mountain,
        _civics_rights,
        _civics_institutions,
        _civics_local_govt,
    ]
    questions = []
    for i in range(count):
        try:
            q = templates[i % len(templates)](grade)
            questions.append(q)
        except Exception:
            continue
    return questions


def generate_questions_for_grade(grade: int, count: int = 100) -> list:
    """Entry point: returns Social Science questions for the given grade."""
    return generate_social_science_questions(grade, count)


if __name__ == "__main__":
    import json
    print("Testing Social Science Generator (Grade 9)...")
    questions = generate_questions_for_grade(9, count=5)
    print(f"Generated {len(questions)} questions.")
    if questions:
        print(json.dumps(questions[0], indent=2))
