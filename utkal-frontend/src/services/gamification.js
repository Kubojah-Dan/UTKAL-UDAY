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

  // Daily Streak Calculation
  const uniqueDates = new Set(
    interactions.map(it => new Date(Number(it.timestamp || 0)).toDateString())
  );
  const sortedDates = Array.from(uniqueDates)
    .map(d => new Date(d))
    .sort((a, b) => a - b);

  let currentDailyStreak = 0;
  let bestDailyStreak = 0;
  if (sortedDates.length > 0) {
    currentDailyStreak = 1;
    bestDailyStreak = 1;
    for (let i = 1; i < sortedDates.length; i++) {
      const diff = (sortedDates[i] - sortedDates[i-1]) / (1000 * 60 * 60 * 24);
      if (diff <= 1.1) { // Same day or next day
        currentDailyStreak += 1;
        bestDailyStreak = Math.max(bestDailyStreak, currentDailyStreak);
      } else {
        currentDailyStreak = 1;
      }
    }
  }

   const hardWins = interactions.filter(
    (it) => !!it.outcome && ["hard", "Hard"].includes(String(it.difficulty || ""))
  ).length;

  // Best Streak (consecutive correct answers)
  let currentStreak = 0;
  let bestStreak = 0;
  interactions.forEach((it) => {
    if (it.outcome) {
      currentStreak += 1;
      bestStreak = Math.max(bestStreak, currentStreak);
    } else {
      currentStreak = 0;
    }
  });

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
      title: "7x Answer Streak",
      icon: "star",
      description: "Get 7 correct answers in a row.",
      earned: bestStreak >= 7,
    },
    {
      id: "daily-50",
      title: "50 Days Badge",
      icon: "flame",
      description: "Maintain a daily learning streak for 50 days.",
      earned: bestDailyStreak >= 50,
      isPremium: true
    },
    {
      id: "daily-100",
      title: "100 Days Badge",
      icon: "trophy",
      description: "Maintain a daily learning streak for 100 days.",
      earned: bestDailyStreak >= 100,
      isPremium: true
    },
    {
      id: "daily-200",
      title: "200 Days Badge",
      icon: "crown",
      description: "Maintain a daily learning streak for 200 days.",
      earned: bestDailyStreak >= 200,
      isPremium: true
    },
    {
      id: "daily-365",
      title: "One Year Badge",
      icon: "award",
      description: "Maintain a daily learning streak for 365 days.",
      earned: bestDailyStreak >= 365,
      isPremium: true
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
