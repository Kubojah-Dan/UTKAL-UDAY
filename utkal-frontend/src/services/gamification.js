const XP_PER_LEVEL = 120;

const DIFFICULTY_XP = {
  easy: 5,
  medium: 10,
  hard: 15,
};

export function computeXpForAttempt({ correct, difficulty, hintsUsed }) {
  const base = correct ? 20 : 5;
  const difficultyBonus = DIFFICULTY_XP[String(difficulty || "").toLowerCase()] || 8;
  const hintPenalty = Math.min(10, Number(hintsUsed || 0) * 2);
  const noHintBonus = Number(hintsUsed || 0) === 0 ? 5 : 0;
  return Math.max(2, base + difficultyBonus + noHintBonus - hintPenalty);
}

export function levelFromXp(totalXp) {
  return Math.max(1, Math.floor(Math.max(0, Number(totalXp || 0)) / XP_PER_LEVEL) + 1);
}

function xpToReachLevel(level) {
  return Math.max(0, (Math.max(1, level) - 1) * XP_PER_LEVEL);
}

export function progressToNextLevel(totalXp) {
  const level = levelFromXp(totalXp);
  const currentFloor = xpToReachLevel(level);
  const nextFloor = xpToReachLevel(level + 1);
  return {
    level,
    currentXp: Number(totalXp || 0),
    currentFloor,
    nextFloor,
    remainingXp: Math.max(0, nextFloor - Number(totalXp || 0)),
    progressPct: Math.max(0, Math.min(100, ((Number(totalXp || 0) - currentFloor) / XP_PER_LEVEL) * 100)),
  };
}

export function evaluateBadges(interactions = []) {
  const attempts = interactions.length;
  const correctCount = interactions.filter((it) => !!it.outcome).length;
  const avgAccuracy = correctCount / Math.max(1, attempts);
  const fastCorrect = interactions.filter((it) => !!it.outcome && Number(it.time_ms || 0) > 0 && Number(it.time_ms || 0) <= 45000).length;
  const subjects = new Set(interactions.map((it) => String(it.subject || "Unknown")));
  const subjectCorrect = {};
  interactions.forEach((it) => {
    const key = String(it.subject || "Unknown");
    subjectCorrect[key] = subjectCorrect[key] || { attempts: 0, correct: 0 };
    subjectCorrect[key].attempts += 1;
    if (it.outcome) subjectCorrect[key].correct += 1;
  });

  let streak = 0;
  let bestStreak = 0;
  for (const it of interactions.sort((a, b) => Number(a.timestamp || 0) - Number(b.timestamp || 0))) {
    if (it.outcome) {
      streak += 1;
      bestStreak = Math.max(bestStreak, streak);
    } else {
      streak = 0;
    }
  }

  const hardWins = interactions.filter(
    (it) => !!it.outcome && ["hard", "Hard"].includes(String(it.difficulty || ""))
  ).length;
  const totalXp = interactions.reduce((sum, it) => sum + Math.max(0, Number(it.xp_awarded || 0)), 0);
  const level = levelFromXp(totalXp);

  const badges = [
    {
      id: "first-correct",
      title: "First Win",
      icon: "medal",
      description: "Solve your first question correctly.",
      earned: correctCount >= 1,
    },
    {
      id: "ten-attempts",
      title: "Consistency Starter",
      icon: "target",
      description: "Complete 10 attempts.",
      earned: attempts >= 10,
    },
    {
      id: "accuracy-ace",
      title: "Accuracy Ace",
      icon: "shield",
      description: "Maintain 80%+ accuracy over at least 20 attempts.",
      earned: attempts >= 20 && avgAccuracy >= 0.8,
    },
    {
      id: "speed-solver",
      title: "Speed Solver",
      icon: "bolt",
      description: "Answer 5 questions correctly in under 45s each.",
      earned: fastCorrect >= 5,
    },
    {
      id: "subject-explorer",
      title: "Subject Explorer",
      icon: "compass",
      description: "Get correct answers in Mathematics, Science, and English.",
      earned: subjects.size >= 3,
    },
    {
      id: "level-five",
      title: "Level 5 Learner",
      icon: "crown",
      description: "Reach Level 5.",
      earned: level >= 5,
    },
    {
      id: "three-subject-core",
      title: "Tri-Subject Core",
      icon: "globe",
      description: "Attempt Mathematics, English, and Science.",
      earned: ["Mathematics", "English", "Science"].every((s) => subjects.has(s)),
    },
    {
      id: "streak-seven",
      title: "7x Streak",
      icon: "star",
      description: "Get 7 correct answers in a row.",
      earned: bestStreak >= 7,
    },
    {
      id: "math-specialist",
      title: "Math Specialist",
      icon: "book",
      description: "Maintain 75%+ in Mathematics over 20+ attempts.",
      earned:
        (subjectCorrect.Mathematics?.attempts || 0) >= 20 &&
        (subjectCorrect.Mathematics?.correct || 0) / Math.max(1, subjectCorrect.Mathematics?.attempts || 0) >= 0.75,
    },
    {
      id: "science-lab",
      title: "Science Lab Hero",
      icon: "flask",
      description: "Get 15 correct Science answers.",
      earned: (subjectCorrect.Science?.correct || 0) >= 15,
    },
    {
      id: "high-difficulty",
      title: "Challenge Climber",
      icon: "rocket",
      description: "Solve 8 hard quests correctly.",
      earned: hardWins >= 8,
    },
  ];

  return {
    totalXp,
    level,
    attempts,
    correctCount,
    accuracy: avgAccuracy,
    earnedCount: badges.filter((badge) => badge.earned).length,
    badges,
    levelProgress: progressToNextLevel(totalXp),
  };
}
