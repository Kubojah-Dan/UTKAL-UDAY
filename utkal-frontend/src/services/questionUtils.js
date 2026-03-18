const NULLISH_VALUES = new Set(["", "null", "none", "n/a", "na", "undefined"]);

const TYPE_ALIASES = {
  mcq: "mcq",
  multiple_choice: "mcq",
  multiple_choice_question: "mcq",
  image_mcq: "image_mcq",
  fill_blank: "fill_blank",
  fill_in_the_blank: "fill_blank",
  short_answer: "short_answer",
  short: "short_answer",
  descriptive: "descriptive",
  essay: "descriptive",
  long_answer: "descriptive",
  subjective: "descriptive",
  text: "short_answer",
  numeric: "short_answer",
};

export const OBJECTIVE_TYPES = new Set(["mcq", "image_mcq", "fill_blank"]);

export function normalizeAnswer(value) {
  return String(value ?? "")
    .replace(/\$\$/g, "")
    .replace(/[“”]/g, '"')
    .replace(/[’]/g, "'")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function cleanText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function cleanList(value) {
  if (!value) return [];
  const raw = Array.isArray(value) ? value : [value];
  const out = [];
  const seen = new Set();
  raw.forEach((item) => {
    const text = cleanText(item);
    if (!text) return;
    const key = text.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    out.push(text);
  });
  return out;
}

function resolveOptionLabelAnswer(answer, options = []) {
  const normalized = normalizeAnswer(answer).replace(/^option\s+/, "").replace(/[.)]$/, "");
  const letterMap = { a: 0, b: 1, c: 2, d: 3, e: 4 };
  if (normalized in letterMap) {
    const idx = letterMap[normalized];
    if (idx < options.length) return options[idx];
  }
  return answer;
}

export function normalizeQuestionType(rawType, options = []) {
  const token = String(rawType ?? "")
    .toLowerCase()
    .replace(/[-\s]+/g, "_")
    .trim();
  const mapped = TYPE_ALIASES[token] || token;
  if (mapped) {
    if ((mapped === "mcq" || mapped === "image_mcq") && (!Array.isArray(options) || options.length < 2)) {
      return "short_answer";
    }
    return mapped;
  }
  if (Array.isArray(options) && options.length >= 2) return "mcq";
  return "short_answer";
}

export function defaultMarksForQuestion(question) {
  const marks = Number(question?.marks || 0);
  if (Number.isFinite(marks) && marks > 0) return marks;
  const type = normalizeQuestionType(question?.type, question?.options);
  if (type === "descriptive") return 5;
  if (type === "short_answer") return 2;
  return 1;
}

export function getAcceptedAnswers(question) {
  const options = Array.isArray(question?.options) ? question.options : [];
  const accepted = cleanList(question?.accepted_answers);
  const answer = cleanText(question?.answer);
  if (answer && !NULLISH_VALUES.has(normalizeAnswer(answer))) {
    accepted.push(resolveOptionLabelAnswer(answer, options));
  }
  return cleanList(accepted);
}

function keywords(text) {
  return normalizeAnswer(text)
    .split(/[^a-z0-9]+/g)
    .filter((token) => token.length >= 4);
}

function scoreExpectedPoints(question, userAnswer) {
  const points = cleanList(question?.expected_points);
  if (!points.length) {
    return { score: 0, matched: 0, total: 0 };
  }

  const normalized = normalizeAnswer(userAnswer);
  let matched = 0;
  points.forEach((point) => {
    const pointKeywords = keywords(point);
    if (!pointKeywords.length) return;
    const hits = pointKeywords.filter((token) => normalized.includes(token)).length;
    const ratio = hits / pointKeywords.length;
    if (ratio >= 0.5 || hits >= 2) {
      matched += 1;
    }
  });

  return {
    score: matched / points.length,
    matched,
    total: points.length,
  };
}

export function evaluateQuestionAnswer(question, userAnswer) {
  const type = normalizeQuestionType(question?.type, question?.options);
  const normalizedUser = normalizeAnswer(userAnswer);
  const acceptedAnswers = getAcceptedAnswers(question);
  const normalizedAccepted = acceptedAnswers.map((item) => normalizeAnswer(item));

  if (!normalizedUser) {
    return {
      correct: false,
      score: 0,
      requiresManualReview: false,
      type,
    };
  }

  if (normalizedAccepted.includes(normalizedUser)) {
    return {
      correct: true,
      score: 1,
      requiresManualReview: false,
      type,
    };
  }

  if (OBJECTIVE_TYPES.has(type)) {
    return {
      correct: false,
      score: 0,
      requiresManualReview: false,
      type,
    };
  }

  const rubric = scoreExpectedPoints(question, userAnswer);
  if (rubric.total > 0) {
    const score = Math.max(0, Math.min(1, rubric.score));
    return {
      correct: score >= 0.5 || rubric.matched >= Math.min(2, rubric.total),
      score,
      requiresManualReview: false,
      type,
    };
  }

  if (normalizedAccepted.some((candidate) => candidate && (normalizedUser.includes(candidate) || candidate.includes(normalizedUser)))) {
    return {
      correct: true,
      score: 0.75,
      requiresManualReview: false,
      type,
    };
  }

  return {
    correct: false,
    score: 0.5,
    requiresManualReview: true,
    type,
  };
}

export function displayAnswer(question) {
  const answer = cleanText(question?.answer);
  if (answer && !NULLISH_VALUES.has(normalizeAnswer(answer))) {
    return answer;
  }
  const points = cleanList(question?.expected_points);
  if (points.length) {
    return points.join("; ");
  }
  return "Answer may vary";
}
