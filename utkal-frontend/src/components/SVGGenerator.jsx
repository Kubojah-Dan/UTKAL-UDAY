import React, { useState } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';

const SVG_PRESETS = {
  circle: {
    width: 360,
    height: 140,
    viewBox: '0 0 360 140',
    background: '#ffffff',
    circles: [
      { id: 'c1', cx: 70, cy: 70, r: 30, fill: '#ffd166', stroke: '#333333', strokeWidth: 2, label: 'A', label_position: { x: 70, y: 115 } },
      { id: 'c2', cx: 180, cy: 70, r: 40, fill: '#06d6a0', stroke: '#333333', strokeWidth: 2, label: 'B', label_position: { x: 180, y: 125 } },
      { id: 'c3', cx: 290, cy: 70, r: 50, fill: '#118ab2', stroke: '#333333', strokeWidth: 2, label: 'C', label_position: { x: 290, y: 135 } },
    ],
    accessibility: {
      role: 'img',
      ariaLabel: {
        en: 'Three circles labeled A, B, C. C is the largest.',
      },
    },
  },
  rectangle: { width: 80, height: 60, color: '#10b981' },
  triangle: { color: '#f59e0b' },
  square: { size: 70, color: '#ef4444' },
  fraction: { numerator: 3, denominator: 4 },
  number_line: { start: 0, end: 10, marked: 5 },
  bar_chart: { values: [5, 8, 3, 10], labels: ['A', 'B', 'C', 'D'] },
  clock: { hours: 3, minutes: 30 },
};

function toPrettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'visual';
}

function canonicalSubject(value) {
  const token = String(value || '').trim().toLowerCase();
  if (token === 'math' || token === 'maths') return 'Mathematics';
  if (token === 'science' || token === 'sci') return 'Science';
  if (token === 'english') return 'English';
  return String(value || 'Mathematics').trim();
}

function splitOptions(value) {
  if (Array.isArray(value)) return value.map((v) => String(v || '').trim()).filter(Boolean);
  if (typeof value !== 'string') return [];
  return value
    .split(/\n|;/g)
    .map((v) => v.trim())
    .filter(Boolean);
}

function toDataUri(svgMarkup) {
  if (!svgMarkup) return '';
  const encoded = encodeURIComponent(svgMarkup)
    .replace(/'/g, '%27')
    .replace(/"/g, '%22');
  return `data:image/svg+xml;charset=UTF-8,${encoded}`;
}

function extractLangMap(fieldValue) {
  if (!fieldValue || typeof fieldValue !== 'object' || Array.isArray(fieldValue)) return null;
  return fieldValue;
}

function normalizeSvgPayload(svgType, parsedPayload) {
  if (parsedPayload && typeof parsedPayload === 'object' && parsedPayload.svg && typeof parsedPayload.svg === 'object') {
    const nestedType = String(parsedPayload.svg.type || svgType || 'circle').toLowerCase();
    const nestedParams = parsedPayload.svg.parameters && typeof parsedPayload.svg.parameters === 'object'
      ? parsedPayload.svg.parameters
      : parsedPayload;
    return { svgType: nestedType, params: nestedParams };
  }

  return { svgType, params: parsedPayload };
}

export default function SVGGenerator() {
  const { showToast } = useToast();
  const [svgType, setSvgType] = useState('circle');
  const [paramsText, setParamsText] = useState(toPrettyJson(SVG_PRESETS.circle));
  const [svg, setSvg] = useState('');
  const [questionJsonText, setQuestionJsonText] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setError('');
    setSvg('');
    let parsed;
    try {
      parsed = JSON.parse(paramsText);
    } catch {
      setError('Invalid JSON. Please fix the Parameters JSON and try again.');
      return;
    }

    const requestPayload = normalizeSvgPayload(svgType, parsed);
    if (requestPayload.svgType !== svgType) {
      setSvgType(requestPayload.svgType);
    }

    setLoading(true);
    try {
      const res = await api.post('/tools/generate-svg', {
        svg_type: requestPayload.svgType,
        params: requestPayload.params
      });
      setSvg(res.data.svg);
      showToast('SVG generated successfully.', 'success');
    } catch (err) {
      console.error('SVG generation failed:', err);
      setError(err.response?.data?.detail || 'SVG generation failed. Check JSON parameters and try again.');
      showToast('SVG generation failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleTypeChange = (type) => {
    setSvgType(type);
    setParamsText(toPrettyJson(SVG_PRESETS[type] || {}));
    setSvg('');
    setError('');
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(paramsText);
      setParamsText(toPrettyJson(parsed));
      setError('');
    } catch {
      setError('Cannot format because JSON is currently invalid.');
    }
  };

  const buildQuestionObject = () => {
    setError('');
    let parsedInput;
    try {
      parsedInput = JSON.parse(paramsText);
    } catch {
      setError('Please provide valid JSON in Parameters before creating the question object.');
      return;
    }

    const source = parsedInput && typeof parsedInput === 'object' ? parsedInput : {};
    const sourceQuestionMap = extractLangMap(source.question) || {};
    const sourceOptionsMap = extractLangMap(source.options) || {};
    const sourceExplanationMap = extractLangMap(source.explanation) || {};

    const subject = canonicalSubject(source.subject || 'Mathematics');
    const grade = Number(source.grade) > 0 ? Number(source.grade) : 3;
    const topic = String(source.topic || 'Visual Questions').trim();
    const englishQuestion = sourceQuestionMap.en || String(source.question || '').trim() || 'Choose the correct option based on the image.';
    const englishOptions = splitOptions(sourceOptionsMap.en || source.options);
    const finalOptions = englishOptions.length ? englishOptions : ['Option A', 'Option B', 'Option C', 'Option D'];
    const answer = String(source.answer || finalOptions[0] || '').trim();
    const explanationEn = sourceExplanationMap.en || String(source.explanation || '').trim() || null;
    const now = Date.now();
    const id = String(source.id || `visual_${slugify(subject)}_g${grade}_${now}`).trim();

    const svgMarkup =
      svg ||
      source?.svg?.svg_markup ||
      source.svg_markup ||
      '';

    const tags = Array.isArray(source.tags) ? source.tags : ['visual', 'svg', 'image_question'];
    const hint =
      String(source.hint || '')
        .trim() ||
      (explanationEn ? explanationEn.split('.').find(Boolean)?.trim() : '') ||
      null;

    const languageVariants = {};
    const languageKeys = new Set([
      'en',
      ...Object.keys(sourceQuestionMap),
      ...Object.keys(sourceOptionsMap),
      ...Object.keys(sourceExplanationMap),
    ]);

    languageKeys.forEach((lang) => {
      const qText = String(sourceQuestionMap[lang] || (lang === 'en' ? englishQuestion : '')).trim();
      const opts = splitOptions(sourceOptionsMap[lang] || (lang === 'en' ? finalOptions : []));
      const exp = String(sourceExplanationMap[lang] || (lang === 'en' ? explanationEn || '' : '')).trim();
      if (!qText && !opts.length && !exp) return;
      languageVariants[lang] = {
        question: qText || englishQuestion,
        options: opts.length ? opts : finalOptions,
        explanation: exp || explanationEn,
        hint: hint,
      };
    });

    if (!languageVariants.en) {
      languageVariants.en = {
        question: englishQuestion,
        options: finalOptions,
        explanation: explanationEn,
        hint: hint,
      };
    }

    const questionObject = {
      id,
      subject,
      grade,
      type: String(source.type || 'image_mcq').trim() || 'image_mcq',
      marks: Number(source.marks) > 0 ? Number(source.marks) : 1,
      difficulty: String(source.difficulty || 'easy').trim().toLowerCase() || 'easy',
      topic,
      subtopic: source.subtopic || null,
      question: englishQuestion,
      options: finalOptions,
      answer: answer || finalOptions[0],
      accepted_answers: Array.from(new Set([answer || finalOptions[0]].filter(Boolean))),
      explanation: explanationEn,
      hint,
      image: {
        has_image: true,
        suggested_image_query: String(source?.svg?.type || svgType || 'circle'),
        image_license_preference: 'public-domain',
        image_source_url: null,
      },
      question_images: svgMarkup ? [toDataUri(svgMarkup)] : [],
      svg_markup: svgMarkup || null,
      language_variants: languageVariants,
      tags,
      source_doc: source.source_doc || null,
      confidence: Number(source.confidence) > 0 ? Number(source.confidence) : 0.95,
      raw_extracted_snippet: source.raw_extracted_snippet || null,
      parse_notes: source.parse_notes || 'Created via SVG Generator',
      board: source.board || null,
      medium: source.medium || 'en',
      expected_points: Array.isArray(source.expected_points) ? source.expected_points : [],
      passage: source.passage || '',
      instructions: source.instructions || '',
      skill_id: source.skill_id || `skill_${slugify(topic)}`,
      skill_label: source.skill_label || topic,
    };

    setQuestionJsonText(toPrettyJson(questionObject));
    showToast('Question object created. Review and click "Add Question to Database".', 'success');
  };

  const handleSaveQuestion = async () => {
    setError('');
    let payloadQuestion;
    try {
      payloadQuestion = JSON.parse(questionJsonText);
    } catch {
      setError('Invalid Question Object JSON. Fix it before saving.');
      return;
    }

    if (!payloadQuestion.id || !payloadQuestion.question || !payloadQuestion.answer) {
      setError('Question object must include id, question, and answer.');
      return;
    }

    setSaving(true);
    try {
      const res = await api.post('/tools/approve-questions', {
        questions: [payloadQuestion],
        translate_to: [],
      });
      showToast(res.data?.message || 'Question added to database.', 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to add question to database.';
      setError(msg);
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="panel">
      <h4 className="mb-3">SVG Generator for Visual Questions</h4>
      
      <div className="mb-4">
        <label className="block mb-2 font-semibold">SVG Type</label>
        <select 
          value={svgType} 
          onChange={(e) => handleTypeChange(e.target.value)}
          className="select-input"
        >
          <option value="circle">Circle</option>
          <option value="rectangle">Rectangle</option>
          <option value="triangle">Triangle</option>
          <option value="square">Square</option>
          <option value="fraction">Fraction</option>
          <option value="number_line">Number Line</option>
          <option value="bar_chart">Bar Chart</option>
          <option value="clock">Clock</option>
        </select>
      </div>

      <div className="mb-4">
        <label className="block mb-2 font-semibold">Parameters (JSON)</label>
        <p className="text-xs text-gray-500 mb-2">
          You can paste either raw params or full question JSON with <code>svg.type</code> and <code>svg.parameters</code>.
        </p>
        <textarea
          value={paramsText}
          onChange={(e) => setParamsText(e.target.value)}
          className="text-input font-mono text-sm"
          rows={14}
        />
        <div className="mt-2 flex gap-2">
          <button className="btn-outline small" onClick={handleFormatJson} type="button">
            Format JSON
          </button>
        </div>
        {error && <p className="error-text mt-2">{error}</p>}
      </div>

      <button
        className="btn-primary mb-4"
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? 'Generating...' : 'Generate SVG'}
      </button>

      {svg && (
        <div className="border rounded-lg p-4 bg-gray-50">
          <h5 className="font-semibold mb-2">Preview:</h5>
          <div dangerouslySetInnerHTML={{ __html: svg }} />
          <details className="mt-4">
            <summary className="cursor-pointer font-semibold">View SVG Code</summary>
            <pre className="bg-white p-3 rounded mt-2 text-xs overflow-x-auto">{svg}</pre>
          </details>
        </div>
      )}

      <div className="mt-6 border-t pt-4">
        <h5 className="font-semibold mb-2">Auto-create Question Object</h5>
        <p className="text-xs text-gray-500 mb-2">
          This creates a full DB-ready question (including multilingual fields when present in your JSON).
        </p>
        <button
          className="btn-outline mb-3"
          onClick={buildQuestionObject}
          type="button"
        >
          Auto-create Question Object from Current JSON + SVG
        </button>

        <label className="block mb-2 font-semibold">Question Object (DB format)</label>
        <textarea
          value={questionJsonText}
          onChange={(e) => setQuestionJsonText(e.target.value)}
          className="text-input font-mono text-sm"
          rows={18}
          placeholder="Click 'Auto-create Question Object...' to generate this JSON."
        />
        <div className="mt-3">
          <button
            className="btn-primary"
            onClick={handleSaveQuestion}
            disabled={saving || !questionJsonText}
            type="button"
          >
            {saving ? 'Saving...' : 'Add Question to Database'}
          </button>
        </div>
      </div>
    </div>
  );
}
