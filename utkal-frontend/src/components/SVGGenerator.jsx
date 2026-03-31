import React, { useState } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';

const SVG_TYPES = [
  // Mathematics
  { value: 'circle',        label: 'Circle(s)',          subject: 'Mathematics' },
  { value: 'rectangle',     label: 'Rectangle',          subject: 'Mathematics' },
  { value: 'triangle',      label: 'Triangle',           subject: 'Mathematics' },
  { value: 'square',        label: 'Square',             subject: 'Mathematics' },
  { value: 'fraction',      label: 'Fraction',           subject: 'Mathematics' },
  { value: 'number_line',   label: 'Number Line',        subject: 'Mathematics' },
  { value: 'bar_chart',     label: 'Bar Chart',          subject: 'Mathematics' },
  { value: 'pie_chart',     label: 'Pie Chart',          subject: 'Mathematics' },
  { value: 'clock',         label: 'Clock',              subject: 'Mathematics' },
  { value: 'ruler',         label: 'Ruler',              subject: 'Mathematics' },
  { value: 'angle',         label: 'Angle',              subject: 'Mathematics' },
  { value: 'place_value',   label: 'Place Value Chart',  subject: 'Mathematics' },
  { value: 'venn_diagram',  label: 'Venn Diagram',       subject: 'Mathematics' },
  { value: 'coins',         label: 'Coins (₹)',          subject: 'Mathematics' },
  { value: 'shapes_grid',   label: 'Shapes Grid',        subject: 'Mathematics' },
  // Science
  { value: 'thermometer',   label: 'Thermometer',        subject: 'Science' },
  { value: 'food_chain',    label: 'Food Chain',         subject: 'Science' },
  { value: 'plant_parts',   label: 'Plant Parts',        subject: 'Science' },
  { value: 'water_cycle',   label: 'Water Cycle',        subject: 'Science' },
  { value: 'cell',          label: 'Cell Diagram',       subject: 'Science' },
  { value: 'magnet',        label: 'Magnet',             subject: 'Science' },
  { value: 'states_of_matter', label: 'States of Matter', subject: 'Science' },
];

const SVG_PRESETS = {
  circle:           { width: 360, height: 140, viewBox: '0 0 360 140', background: '#ffffff', circles: [{ id: 'c1', cx: 70, cy: 70, r: 30, fill: '#ffd166', stroke: '#333333', strokeWidth: 2, label: 'A', label_position: { x: 70, y: 115 } }, { id: 'c2', cx: 180, cy: 70, r: 40, fill: '#06d6a0', stroke: '#333333', strokeWidth: 2, label: 'B', label_position: { x: 180, y: 125 } }, { id: 'c3', cx: 290, cy: 70, r: 50, fill: '#118ab2', stroke: '#333333', strokeWidth: 2, label: 'C', label_position: { x: 290, y: 135 } }], accessibility: { role: 'img', ariaLabel: { en: 'Three circles labeled A, B, C. C is the largest.' } } },
  rectangle:        { width: 80, height: 60, color: '#10b981' },
  triangle:         { color: '#f59e0b' },
  square:           { size: 70, color: '#ef4444' },
  fraction:         { numerator: 3, denominator: 4 },
  number_line:      { start: 0, end: 10, marked: 5 },
  bar_chart:        { values: [5, 8, 3, 10], labels: ['Mon', 'Tue', 'Wed', 'Thu'] },
  pie_chart:        { values: [4, 3, 2, 1], labels: ['A', 'B', 'C', 'D'] },
  clock:            { hours: 3, minutes: 30 },
  ruler:            { length_cm: 10 },
  angle:            { degrees: 60, label: '60°' },
  place_value:      { number: 345 },
  venn_diagram:     { set_a_label: 'Even', set_b_label: 'Prime', intersection_label: '2' },
  coins:            { coins: [1, 2, 5, 10] },
  shapes_grid:      { shapes: ['circle', 'square', 'triangle', 'rectangle', 'pentagon', 'hexagon'] },
  thermometer:      { temperature: 37, min_temp: 0, max_temp: 100, unit: '°C' },
  food_chain:       { organisms: ['Grass', 'Grasshopper', 'Frog', 'Snake', 'Eagle'] },
  plant_parts:      { labeled: true },
  water_cycle:      { labeled: true },
  cell:             { cell_type: 'animal' },
  magnet:           { poles_labeled: true },
  states_of_matter: { state: 'all' },
};

function buildSmartQuestion(svgType, params, grade) {
  const g = Number(grade) || 3;
  switch (svgType) {
    case 'clock': {
      const h = Number(params.hours ?? 3);
      const m = Number(params.minutes ?? 30);
      const pad = (n) => String(n).padStart(2, '0');
      const correct = `${h}:${pad(m)}`;
      const wrongs = [`${h === 12 ? 1 : h + 1}:${pad(m)}`, `${h}:${pad(m === 0 ? 30 : 0)}`, `${h === 1 ? 12 : h - 1}:${pad(m)}`];
      return { question: 'What time does the clock show?', options: shuffle([correct, ...wrongs]).slice(0, 4), answer: correct, explanation: `The hour hand points to ${h} and the minute hand shows ${m} minutes, so the time is ${correct}.`, hint: 'The short hand shows hours, the long hand shows minutes.', topic: 'Telling Time', difficulty: g <= 2 ? 'easy' : g <= 4 ? 'medium' : 'hard' };
    }
    case 'fraction': {
      const num = Number(params.numerator ?? 1);
      const den = Number(params.denominator ?? 2);
      const correct = `${num}/${den}`;
      return { question: 'What fraction of the shape is shaded?', options: shuffle([correct, `${num + 1}/${den}`, `${num}/${den + 1}`, `${den - num}/${den}`]).slice(0, 4), answer: correct, explanation: `${num} out of ${den} equal parts are shaded, so the fraction is ${correct}.`, hint: 'Count the shaded parts and total parts.', topic: 'Fractions', difficulty: 'easy' };
    }
    case 'number_line': {
      const marked = Number(params.marked ?? 5);
      const start = Number(params.start ?? 0);
      const end = Number(params.end ?? 10);
      return { question: 'Which number is marked on the number line?', options: shuffle([String(marked), String(marked + 1), String(marked - 1), String(Math.floor((start + end) / 2))]).slice(0, 4), answer: String(marked), explanation: `The marked point is at ${marked} on the number line from ${start} to ${end}.`, hint: 'Count the steps from the starting number.', topic: 'Number Line', difficulty: 'easy' };
    }
    case 'bar_chart': {
      const values = Array.isArray(params.values) ? params.values : [5, 8, 3, 10];
      const labels = Array.isArray(params.labels) ? params.labels : ['A', 'B', 'C', 'D'];
      const maxIdx = values.indexOf(Math.max(...values));
      const correct = String(labels[maxIdx] ?? 'A');
      return { question: 'Which item has the highest value in the bar chart?', options: shuffle(labels.map(String)).slice(0, 4), answer: correct, explanation: `${correct} has the tallest bar with a value of ${values[maxIdx]}.`, hint: 'Look for the tallest bar.', topic: 'Data Handling', difficulty: 'easy' };
    }
    case 'pie_chart': {
      const values = Array.isArray(params.values) ? params.values : [4, 3, 2, 1];
      const labels = Array.isArray(params.labels) ? params.labels : ['A', 'B', 'C', 'D'];
      const maxIdx = values.indexOf(Math.max(...values));
      const correct = String(labels[maxIdx] ?? 'A');
      return { question: 'Which part is the largest in the pie chart?', options: shuffle(labels.map(String)).slice(0, 4), answer: correct, explanation: `${correct} is the largest sector in the pie chart.`, hint: 'The largest slice represents the biggest part.', topic: 'Data Handling', difficulty: 'easy' };
    }
    case 'ruler': {
      const len = Number(params.length_cm ?? 10);
      return { question: 'What is the length shown on the ruler?', options: shuffle([`${len} cm`, `${len + 2} cm`, `${len - 1} cm`, `${len + 5} cm`]).slice(0, 4), answer: `${len} cm`, explanation: `The ruler measures ${len} centimetres.`, hint: 'Read the last number marked on the ruler.', topic: 'Measurement', difficulty: 'easy' };
    }
    case 'angle': {
      const deg = Number(params.degrees ?? 60);
      const type = deg < 90 ? 'acute' : deg === 90 ? 'right' : deg < 180 ? 'obtuse' : 'reflex';
      return { question: 'What type of angle is shown in the diagram?', options: shuffle(['acute', 'right', 'obtuse', 'reflex']), answer: type, explanation: `An angle of ${deg}° is a ${type} angle.`, hint: 'Acute < 90°, Right = 90°, Obtuse is between 90° and 180°, Reflex > 180°.', topic: 'Geometry', difficulty: g <= 4 ? 'easy' : 'medium' };
    }
    case 'place_value': {
      const num = Number(params.number ?? 345);
      const placeNames = ['ones', 'tens', 'hundreds', 'thousands'];
      const digits = String(num).split('').reverse();
      const places = digits.map((d, i) => `${d} ${placeNames[i]}`).reverse().join(', ');
      return { question: `How many hundreds are in the number ${num}?`, options: shuffle([String(Math.floor(num / 100) % 10), String(Math.floor(num / 10) % 10), String(num % 10), String(Math.floor(num / 1000) % 10)]).slice(0, 4), answer: String(Math.floor(num / 100) % 10), explanation: `${num} has ${places}.`, hint: 'Look at the hundreds column in the place value chart.', topic: 'Place Value', difficulty: 'easy' };
    }
    case 'venn_diagram': {
      const a = params.set_a_label ?? 'A';
      const b = params.set_b_label ?? 'B';
      return { question: 'What does the overlapping region of the Venn diagram represent?', options: shuffle([`Elements in both ${a} and ${b}`, `Only ${a}`, `Only ${b}`, `Neither ${a} nor ${b}`]), answer: `Elements in both ${a} and ${b}`, explanation: `The intersection contains elements that belong to both sets ${a} and ${b}.`, hint: 'The overlapping part belongs to both circles.', topic: 'Sets', difficulty: 'medium' };
    }
    case 'coins': {
      const coins = Array.isArray(params.coins) ? params.coins : [1, 2, 5, 10];
      const total = coins.reduce((s, c) => s + Number(c), 0);
      return { question: 'What is the total value of the coins shown?', options: shuffle([`₹${total}`, `₹${total + 1}`, `₹${total - 1}`, `₹${total + 3}`]).slice(0, 4), answer: `₹${total}`, explanation: `${coins.map((c) => `₹${c}`).join(' + ')} = ₹${total}.`, hint: 'Add the value of each coin.', topic: 'Money', difficulty: 'easy' };
    }
    case 'shapes_grid': {
      const shapes = Array.isArray(params.shapes) ? params.shapes : ['circle', 'square', 'triangle', 'rectangle'];
      return { question: 'How many shapes are shown in the image?', options: shuffle([String(shapes.length), String(shapes.length + 1), String(shapes.length - 1), String(shapes.length + 2)]).slice(0, 4), answer: String(shapes.length), explanation: `There are ${shapes.length} shapes: ${shapes.join(', ')}.`, hint: 'Count each shape carefully.', topic: 'Shapes', difficulty: 'easy' };
    }
    // Science types
    case 'thermometer': {
      const temp = Number(params.temperature ?? 37);
      const unit = params.unit ?? '°C';
      return { question: 'What temperature does the thermometer show?', options: shuffle([`${temp}${unit}`, `${temp + 5}${unit}`, `${temp - 3}${unit}`, `${temp + 10}${unit}`]).slice(0, 4), answer: `${temp}${unit}`, explanation: `The mercury level shows ${temp}${unit}.`, hint: 'Read the level where the red mercury stops.', topic: 'Heat and Temperature', difficulty: 'easy' };
    }
    case 'food_chain': {
      const organisms = Array.isArray(params.organisms) ? params.organisms : ['Grass', 'Grasshopper', 'Frog', 'Snake', 'Eagle'];
      const producer = organisms[0];
      const topPredator = organisms[organisms.length - 1];
      return { question: `In the food chain shown, which organism is the producer?`, options: shuffle([producer, organisms[1] ?? 'Grasshopper', topPredator, organisms[Math.floor(organisms.length / 2)] ?? 'Frog']).slice(0, 4), answer: producer, explanation: `${producer} is the producer because it makes its own food through photosynthesis. The chain ends with ${topPredator} as the top predator.`, hint: 'The producer is always the first organism in a food chain — it makes its own food.', topic: 'Food Chain', difficulty: g <= 4 ? 'easy' : 'medium' };
    }
    case 'plant_parts': {
      return { question: 'Which part of the plant absorbs water and minerals from the soil?', options: shuffle(['Root', 'Stem', 'Leaf', 'Flower']), answer: 'Root', explanation: 'Roots absorb water and minerals from the soil and anchor the plant.', hint: 'This part is found underground.', topic: 'Parts of a Plant', difficulty: 'easy' };
    }
    case 'water_cycle': {
      return { question: 'What is the process called when water from rivers and oceans turns into water vapour?', options: shuffle(['Evaporation', 'Condensation', 'Precipitation', 'Transpiration']), answer: 'Evaporation', explanation: 'Evaporation is when liquid water is heated by the sun and turns into water vapour that rises into the atmosphere.', hint: 'The sun heats the water surface causing this process.', topic: 'Water Cycle', difficulty: g <= 4 ? 'easy' : 'medium' };
    }
    case 'cell': {
      const cellType = params.cell_type ?? 'animal';
      const isPlant = cellType === 'plant';
      const correct = isPlant ? 'Cell wall' : 'Cell membrane';
      const wrong1 = isPlant ? 'Cell membrane' : 'Cell wall';
      return { question: `Which structure is found in a ${cellType} cell but NOT in the other type?`, options: shuffle([correct, wrong1, 'Nucleus', 'Cytoplasm']), answer: correct, explanation: isPlant ? 'Plant cells have a rigid cell wall made of cellulose, which animal cells do not have.' : 'Animal cells have only a cell membrane (no cell wall), while plant cells have both.', hint: isPlant ? 'Plant cells have an extra rigid outer layer.' : 'Animal cells lack the rigid outer layer found in plant cells.', topic: 'Cell Structure', difficulty: g <= 6 ? 'medium' : 'hard' };
    }
    case 'magnet': {
      return { question: 'Which poles of a magnet attract each other?', options: shuffle(['North and South', 'North and North', 'South and South', 'Both same poles']), answer: 'North and South', explanation: 'Unlike poles (North and South) attract each other, while like poles (N-N or S-S) repel each other.', hint: 'Opposite poles attract, same poles repel.', topic: 'Magnetism', difficulty: 'easy' };
    }
    case 'states_of_matter': {
      return { question: 'In which state of matter do particles have a fixed position and cannot move freely?', options: shuffle(['Solid', 'Liquid', 'Gas', 'Plasma']), answer: 'Solid', explanation: 'In a solid, particles are tightly packed in fixed positions and can only vibrate. Liquids flow and gases spread out freely.', hint: 'Think about which state has the most tightly packed particles.', topic: 'States of Matter', difficulty: g <= 4 ? 'easy' : 'medium' };
    }
    default:
      return { question: 'What do you observe in the image?', options: ['Option A', 'Option B', 'Option C', 'Option D'], answer: 'Option A', explanation: null, hint: null, topic: 'Visual Questions', difficulty: 'easy' };
  }
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function toPrettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function slugify(value) {
  return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'visual';
}

function canonicalSubject(value) {
  const token = String(value || '').trim().toLowerCase();
  if (token === 'math' || token === 'maths' || token === 'mathematics') return 'Mathematics';
  if (token === 'science' || token === 'sci') return 'Science';
  return String(value || 'Mathematics').trim();
}

function toDataUri(svgMarkup) {
  if (!svgMarkup) return '';
  try {
    return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgMarkup)))}`;
  } catch {
    return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svgMarkup)}`;
  }
}

const DEFAULT_MATH_TYPE = 'clock';
const DEFAULT_SCIENCE_TYPE = 'thermometer';

export default function SVGGenerator() {
  const { showToast } = useToast();
  const [subject, setSubject] = useState('Mathematics');
  const [svgType, setSvgType] = useState(DEFAULT_MATH_TYPE);
  const [grade, setGrade] = useState(3);
  const [paramsText, setParamsText] = useState(toPrettyJson(SVG_PRESETS[DEFAULT_MATH_TYPE]));
  const [svg, setSvg] = useState('');
  const [questionJsonText, setQuestionJsonText] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const filteredTypes = SVG_TYPES.filter((t) => t.subject === subject);

  const handleSubjectChange = (newSubject) => {
    setSubject(newSubject);
    setSvg('');
    setError('');
    setQuestionJsonText('');
    const defaultType = newSubject === 'Science' ? DEFAULT_SCIENCE_TYPE : DEFAULT_MATH_TYPE;
    setSvgType(defaultType);
    setParamsText(toPrettyJson(SVG_PRESETS[defaultType] || {}));
  };

  const handleTypeChange = (type) => {
    setSvgType(type);
    setParamsText(toPrettyJson(SVG_PRESETS[type] || {}));
    setSvg('');
    setError('');
    setQuestionJsonText('');
  };

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
    setLoading(true);
    try {
      const res = await api.post('/tools/generate-svg', { svg_type: svgType, params: parsed });
      setSvg(res.data.svg);
      showToast('SVG generated successfully.', 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'SVG generation failed.';
      setError(msg);
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const buildQuestionObject = () => {
    setError('');
    let params;
    try {
      params = JSON.parse(paramsText);
    } catch {
      setError('Please provide valid JSON in Parameters before creating the question object.');
      return;
    }
    const smart = buildSmartQuestion(svgType, params, grade);
    const canonSubject = canonicalSubject(subject);
    const topic = smart.topic || 'Visual Questions';
    const id = `visual_${slugify(canonSubject)}_g${grade}_${Date.now()}`;
    const svgMarkup = svg || '';
    const questionObject = {
      id,
      subject: canonSubject,
      grade: Number(grade),
      type: 'image_mcq',
      marks: 1,
      difficulty: smart.difficulty || 'easy',
      topic,
      subtopic: null,
      question: smart.question,
      options: smart.options,
      answer: smart.answer,
      accepted_answers: [smart.answer],
      explanation: smart.explanation || null,
      hint: smart.hint || null,
      image: { has_image: true, suggested_image_query: svgType, image_license_preference: 'public-domain', image_source_url: null },
      question_images: svgMarkup ? [toDataUri(svgMarkup)] : [],
      svg_markup: svgMarkup || null,
      language_variants: { en: { question: smart.question, options: smart.options, explanation: smart.explanation || null, hint: smart.hint || null } },
      tags: ['visual', 'svg', svgType],
      source_doc: null,
      confidence: 0.95,
      raw_extracted_snippet: null,
      parse_notes: 'Created via SVG Generator',
      board: null,
      medium: 'en',
      expected_points: [],
      passage: '',
      instructions: '',
      skill_id: `skill_${slugify(topic)}`,
      skill_label: topic,
      approved: true,
      status: 'active',
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
      const res = await api.post('/tools/approve-questions', { questions: [payloadQuestion], translate_to: [] });
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

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div>
          <label className="block mb-1 font-semibold text-sm">Grade</label>
          <select value={grade} onChange={(e) => setGrade(Number(e.target.value))} className="select-input">
            {Array.from({ length: 12 }, (_, i) => i + 1).map((g) => (
              <option key={g} value={g}>Grade {g}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block mb-1 font-semibold text-sm">Subject</label>
          <select value={subject} onChange={(e) => handleSubjectChange(e.target.value)} className="select-input">
            <option value="Mathematics">Mathematics</option>
            <option value="Science">Science</option>
          </select>
        </div>
        <div>
          <label className="block mb-1 font-semibold text-sm">SVG Type</label>
          <select value={svgType} onChange={(e) => handleTypeChange(e.target.value)} className="select-input">
            {filteredTypes.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-4">
        <label className="block mb-2 font-semibold">Parameters (JSON)</label>
        <textarea
          value={paramsText}
          onChange={(e) => setParamsText(e.target.value)}
          className="text-input font-mono text-sm"
          rows={10}
        />
        <div className="mt-2 flex gap-2">
          <button
            className="btn-outline small"
            onClick={() => { try { setParamsText(toPrettyJson(JSON.parse(paramsText))); setError(''); } catch { setError('Cannot format: invalid JSON.'); } }}
            type="button"
          >
            Format JSON
          </button>
        </div>
        {error && <p className="error-text mt-2">{error}</p>}
      </div>

      <button className="btn-primary mb-4" onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate SVG'}
      </button>

      {svg && (
        <div className="border rounded-lg p-4 bg-gray-50 mb-4">
          <h5 className="font-semibold mb-2">Preview:</h5>
          <div dangerouslySetInnerHTML={{ __html: svg }} />
          <details className="mt-4">
            <summary className="cursor-pointer font-semibold text-sm">View SVG Code</summary>
            <pre className="bg-white p-3 rounded mt-2 text-xs overflow-x-auto">{svg}</pre>
          </details>
        </div>
      )}

      <div className="border-t pt-4">
        <h5 className="font-semibold mb-2">Auto-create Question Object</h5>
        <p className="text-xs text-gray-500 mb-2">
          Generates a DB-ready question with correct question text, options, and answer for the selected SVG type.
          <strong> Generate SVG first, then click below.</strong>
        </p>
        <button className="btn-outline mb-3" onClick={buildQuestionObject} type="button" disabled={!svg}>
          Auto-create Question Object from Current SVG
        </button>

        <label className="block mb-2 font-semibold">Question Object (DB format)</label>
        <textarea
          value={questionJsonText}
          onChange={(e) => setQuestionJsonText(e.target.value)}
          className="text-input font-mono text-sm"
          rows={18}
          placeholder="Generate SVG first, then click 'Auto-create Question Object'."
        />
        <div className="mt-3">
          <button className="btn-primary" onClick={handleSaveQuestion} disabled={saving || !questionJsonText} type="button">
            {saving ? 'Saving...' : 'Add Question to Database'}
          </button>
        </div>
      </div>
    </div>
  );
}
