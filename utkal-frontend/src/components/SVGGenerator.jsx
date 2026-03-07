import React, { useState } from 'react';
import { api } from '../services/api';

export default function SVGGenerator() {
  const [svgType, setSvgType] = useState('circle');
  const [params, setParams] = useState({});
  const [svg, setSvg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await api.post('/tools/generate-svg', {
        svg_type: svgType,
        params: params
      });
      setSvg(res.data.svg);
    } catch (err) {
      console.error('SVG generation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const presets = {
    circle: { radius: 50, color: '#3b82f6' },
    rectangle: { width: 80, height: 60, color: '#10b981' },
    triangle: { color: '#f59e0b' },
    square: { size: 70, color: '#ef4444' },
    fraction: { numerator: 3, denominator: 4 },
    number_line: { start: 0, end: 10, marked: 5 },
    bar_chart: { values: [5, 8, 3, 10], labels: ['A', 'B', 'C', 'D'] },
    clock: { hours: 3, minutes: 30 }
  };

  const handleTypeChange = (type) => {
    setSvgType(type);
    setParams(presets[type] || {});
    setSvg('');
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
        <textarea
          value={JSON.stringify(params, null, 2)}
          onChange={(e) => {
            try {
              setParams(JSON.parse(e.target.value));
            } catch {}
          }}
          className="text-input font-mono text-sm"
          rows={6}
        />
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
    </div>
  );
}
