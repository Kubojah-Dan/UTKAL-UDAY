import React, { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { saveStudyCardsLocally, getLocalStudyCards } from "../db/database";
import { Volume2, VolumeX, BookOpen, Zap, ChevronRight } from "lucide-react";
import SyncStatusBanner from "../components/SyncStatusBanner";

const SUBJECTS = ["Mathematics", "Science", "Environmental Science", "Social Science", "English"];

function TTSButton({ text }) {
  const [speaking, setSpeaking] = useState(false);
  const utterRef = useRef(null);

  const toggle = () => {
    if (!("speechSynthesis" in window)) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate  = 0.9;
    utt.pitch = 1;
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    utterRef.current = utt;
    window.speechSynthesis.speak(utt);
    setSpeaking(true);
  };

  return (
    <button className={`tts-btn ${speaking ? "speaking" : ""}`} onClick={toggle} title="Listen">
      {speaking ? <VolumeX size={13} /> : <Volume2 size={13} />}
      {speaking ? "Stop" : "Listen"}
    </button>
  );
}

function ConceptCard({ card, onPractice, subject }) {
  const [flipped, setFlipped] = useState(false);

  const ttsText = [
    card.title,
    card.definition && `Definition: ${card.definition}`,
    card.example && `Example: ${card.example}`,
    card.formula && `Formula: ${card.formula}`,
    card.tip && `Tip: ${card.tip}`,
  ].filter(Boolean).join(". ");

  const themeClass = subject === "Mathematics" ? "card-theme-math" 
                   : subject === "Science" ? "card-theme-science"
                   : subject === "Social Science" ? "card-theme-social"
                   : subject === "English" ? "card-theme-english"
                   : "card-theme-science";

  return (
    <div 
      className={`concept-card-container ${flipped ? "flipped" : ""} ${themeClass}`}
      onClick={() => setFlipped(!flipped)}
    >
      <div className="concept-card-inner">
        {/* Front */}
        <div className="concept-card-front">
          <div className="concept-card-title">{card.title}</div>
          <div className="concept-card-hint">Tap to flip 🔄</div>
        </div>

        {/* Back */}
        <div className="concept-card-back" onClick={(e) => e.stopPropagation()}>
          <div className="concept-card-title" style={{ fontSize: "1.1rem", borderBottom: "1px solid #e2e8f0", paddingBottom: 8 }}>
            {card.title}
          </div>
          
          {card.definition && (
            <div className="concept-card-def">{card.definition}</div>
          )}

          {card.formula && (
            <div className="concept-card-detail">
              <strong>Formula</strong>
              {card.formula}
            </div>
          )}

          {card.example && (
            <div className="concept-card-detail">
              <strong>Example</strong>
              {card.example}
            </div>
          )}

          {card.tip && (
            <div className="concept-card-detail" style={{ borderLeftColor: "#7c3aed" }}>
              <strong>Memory Tip</strong>
              {card.tip}
            </div>
          )}

          <div className="concept-card-actions">
            <TTSButton text={ttsText} />
            <button className="btn-outline small" onClick={() => setFlipped(false)}>
              Back ↩️
            </button>
            {onPractice && (
              <button
                className="btn-primary small"
                onClick={() => onPractice(card)}
                style={{ fontSize: "0.78rem", padding: "5px 10px", marginLeft: "auto" }}
              >
                <Zap size={12} style={{ marginRight: 4 }} />
                Practice
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function FormulaSheet({ subject, grade }) {
  const [formulas, setFormulas] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!subject || !grade) return;
    setLoading(true);
    
    // Map Science to Physics/Chemistry if needed
    const targetSubject = subject === "Science" ? "Physics" : subject;
    
    api.get(`/notes/formula-sheet/${targetSubject}/${grade}`)
      .then((res) => {
        let forms = res.data?.formulas || [];
        if (forms.length === 0 && subject === "Science") {
           // Try Chemistry if Physics had none
           return api.get(`/notes/formula-sheet/Chemistry/${grade}`);
        }
        setFormulas(forms);
      })
      .then(chemRes => {
        if (chemRes) setFormulas(chemRes.data?.formulas || []);
      })
      .catch(() => setFormulas([]))
      .finally(() => setLoading(false));
  }, [subject, grade]);

  if (!formulas.length) return null;

  return (
    <div className="formula-sheet-panel">
      <h3 style={{ margin: "0 0 12px", color: "#fde68a" }}>
        📐 Formula Sheet — {subject} Grade {grade}
      </h3>
      {loading && <p style={{ color: "#94a3b8" }}>Loading…</p>}
      {formulas.map((f, i) => (
        <div key={i} className="formula-row">
          <span className="formula-name">{f.name}</span>
          <code className="formula-expr">{f.formula}</code>
        </div>
      ))}
    </div>
  );
}

export default function StudyNotes() {
  const { user } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();

  const [subject, setSubject]   = useState("Mathematics");
  const [grade, setGrade]       = useState(user?.class_grade || 8);
  const [chapter, setChapter]   = useState("");
  const [chapters, setChapters] = useState([]);
  const [cards, setCards]       = useState([]);
  const [loading, setLoading]   = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  // Load chapters
  useEffect(() => {
    if (!subject || !grade) return;
    api.get(`/notes/chapters/${subject}/${grade}`)
      .then((res) => {
        const ch = res.data?.chapters || [];
        setChapters(ch);
        if (ch.length) setChapter(ch[0]);
      })
      .catch(() => setChapters([]));
  }, [subject, grade]);

  // Load cards — online first, fall back to IndexedDB
  const loadCards = useCallback(async () => {
    setLoading(true);
    setIsOffline(false);
    try {
      const res = await api.get("/notes", {
        params: { subject, grade, chapter: chapter || undefined, limit: 50 },
      });
      const serverCards = res.data?.cards || [];
      if (serverCards.length) {
        // Cache to IndexedDB for offline use
        await saveStudyCardsLocally(serverCards.map((c) => ({ ...c, synced: 1 })));
      }
      setCards(serverCards);
    } catch {
      // Offline fallback
      setIsOffline(true);
      const localCards = await getLocalStudyCards({ subject, grade: Number(grade), chapter: chapter || undefined });
      setCards(localCards);
    } finally {
      setLoading(false);
    }
  }, [subject, grade, chapter]);

  useEffect(() => { loadCards(); }, [loadCards]);

  const handlePractice = (card) => {
    navigate("/quest", { state: { subject, grade, topic: card.title } });
  };

  const showFormulaSheet = ["Mathematics", "Physics", "Chemistry"].includes(subject) && grade >= 8;

  return (
    <div className="container notes-page">
      <SyncStatusBanner />

      {/* Header */}
      <div className="panel" style={{ marginTop: 0, background: "linear-gradient(135deg, #ecfdf5, #f0fdf9)", border: "1px solid #a7f3d0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <BookOpen size={22} color="var(--brand)" />
          <h2 style={{ margin: 0 }}>Study Notes</h2>
        </div>
        <p className="muted">
          NCERT-aligned concept cards for every chapter. Tap 🔊 to listen (works offline).
        </p>
        {isOffline && (
          <p style={{ color: "#b45309", background: "#fffbeb", padding: "6px 10px", borderRadius: 8, fontSize: "0.82rem", marginTop: 8 }}>
            📴 Offline mode — showing cached notes
          </p>
        )}
      </div>

      {/* Filters */}
      <div className="panel" style={{ padding: "14px 18px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
          {/* Subject */}
          <div className="notes-nav">
            {SUBJECTS.map((s) => (
              <button
                key={s}
                className={`notes-nav-btn ${subject === s ? "active" : ""}`}
                onClick={() => { setSubject(s); setChapter(""); }}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Grade */}
          <select
            value={grade}
            onChange={(e) => setGrade(Number(e.target.value))}
            className="select-input"
            style={{ width: "auto", marginTop: 0 }}
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map((g) => (
              <option key={g} value={g}>Grade {g}</option>
            ))}
          </select>

          {/* Chapter */}
          {chapters.length > 0 && (
            <select
              value={chapter}
              onChange={(e) => setChapter(e.target.value)}
              className="select-input"
              style={{ width: "auto", marginTop: 0 }}
            >
              <option value="">All Chapters</option>
              {chapters.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Formula sheet (Grade 8+ Math/Physics/Chemistry) */}
      {showFormulaSheet && (
        <div className="panel">
          <FormulaSheet subject={subject} grade={grade} />
        </div>
      )}

      {/* Cards */}
      {loading && <div className="panel"><p className="muted">Loading notes…</p></div>}

      {!loading && cards.length === 0 && (
        <div className="panel" style={{ textAlign: "center" }}>
          <BookOpen size={36} style={{ color: "#cbd5e1", marginBottom: 10 }} />
          <p className="muted">No concept cards available yet for this selection.</p>
          <p className="muted" style={{ fontSize: "0.82rem" }}>
            Your teacher can generate cards by pasting chapter text in the Teacher Dashboard.
          </p>
        </div>
      )}

      {!loading && cards.length > 0 && (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 4px 4px 0" }}>
            <p className="muted">{cards.length} concept cards</p>
            <button
              className="btn-outline small"
              onClick={() => navigate("/quest", { state: { subject, grade } })}
            >
              Practice All <ChevronRight size={14} />
            </button>
          </div>
          <div className="concept-cards-grid">
            {cards.map((card) => (
              <ConceptCard key={card.id} card={card} onPractice={handlePractice} subject={subject} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
