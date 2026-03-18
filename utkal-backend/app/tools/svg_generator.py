"""SVG Image Generator for Visual Questions"""
import math
import re
from html import escape
from typing import Any, Dict, List

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _safe_color(value: Any, default: str) -> str:
    token = str(value or "").strip()
    if COLOR_RE.match(token):
        return token
    return default


def _safe_attr(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def _safe_text(value: Any) -> str:
    return escape(str(value or ""))


def _num(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _extract_aria_label(accessibility: Dict[str, Any]) -> str:
    label = accessibility.get("ariaLabel")
    if isinstance(label, dict):
        if "en" in label and str(label["en"]).strip():
            return str(label["en"]).strip()
        for candidate in label.values():
            if str(candidate or "").strip():
                return str(candidate).strip()
        return "Visual question"
    if isinstance(label, str) and label.strip():
        return label.strip()
    return "Visual question"


def _generate_multi_circle_svg(params: Dict[str, Any]) -> str:
    width = _to_int(params.get("width"), 360)
    height = _to_int(params.get("height"), 140)
    view_box = str(params.get("viewBox") or f"0 0 {width} {height}")
    background = _safe_color(params.get("background"), "#ffffff")

    accessibility = params.get("accessibility")
    if not isinstance(accessibility, dict):
        accessibility = {}
    role = _safe_attr(accessibility.get("role") or "img")
    aria_label = _safe_attr(_extract_aria_label(accessibility))

    circles = params.get("circles")
    if not isinstance(circles, list):
        circles = []
    interaction = params.get("interaction")
    if not isinstance(interaction, dict):
        interaction = {}
    hotspot_map = interaction.get("hotspotToOption")
    if not isinstance(hotspot_map, dict):
        hotspot_map = {}

    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{_safe_attr(view_box)}" role="{role}" aria-label="{aria_label}">',
        f'<rect width="100%" height="100%" fill="{background}"/>',
    ]

    for index, raw in enumerate(circles):
        if not isinstance(raw, dict):
            continue

        circle_id = _safe_attr(raw.get("id") or f"circle_{index + 1}")
        cx = _to_float(raw.get("cx"), 60 + index * 80)
        cy = _to_float(raw.get("cy"), height / 2)
        radius = max(1.0, _to_float(raw.get("r"), 30))
        fill = _safe_color(raw.get("fill"), "#3b82f6")
        stroke = _safe_color(raw.get("stroke"), "#333333")
        stroke_width = max(0.5, _to_float(raw.get("strokeWidth"), 2))

        hotspot_option = hotspot_map.get(raw.get("id"))
        data_option_attr = ""
        if hotspot_option is not None and str(hotspot_option).strip():
            data_option_attr = f' data-option="{_safe_attr(hotspot_option)}"'
        parts.append(
            f'<circle id="{circle_id}" cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(radius)}" fill="{fill}" stroke="{stroke}" stroke-width="{_num(stroke_width)}"{data_option_attr}/>'
        )

        label = raw.get("label")
        if label is None or str(label).strip() == "":
            continue

        label_position = raw.get("label_position")
        if isinstance(label_position, dict):
            lx = _to_float(label_position.get("x"), cx)
            ly = _to_float(label_position.get("y"), cy + radius + 20)
        else:
            lx = cx
            ly = cy + radius + 20

        label_fill = _safe_color(raw.get("label_fill"), "#111111")
        label_size = max(8, _to_int(raw.get("label_size"), 14))
        parts.append(
            f'<text x="{_num(lx)}" y="{_num(ly)}" font-size="{label_size}" text-anchor="middle" fill="{label_fill}">{_safe_text(label)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def generate_svg_shape(shape_type: str, params: dict) -> str:
    """Generate SVG for geometric shapes"""
    
    if shape_type == "circle":
        if isinstance(params.get("circles"), list):
            return _generate_multi_circle_svg(params)

        radius = max(1, _to_int(params.get("radius"), 50))
        color = _safe_color(params.get("color"), "#3b82f6")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circle shape">
  <circle cx="60" cy="60" r="{radius}" fill="{color}" stroke="#1e40af" stroke-width="2" />
</svg>'''
    
    elif shape_type == "rectangle":
        width = max(1, _to_int(params.get("width"), 80))
        height = max(1, _to_int(params.get("height"), 60))
        color = _safe_color(params.get("color"), "#10b981")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="30" width="{width}" height="{height}" fill="{color}" stroke="#065f46" stroke-width="2" />
</svg>'''
    
    elif shape_type == "triangle":
        color = _safe_color(params.get("color"), "#f59e0b")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <polygon points="60,20 100,100 20,100" fill="{color}" stroke="#92400e" stroke-width="2" />
</svg>'''
    
    elif shape_type == "square":
        size = max(1, _to_int(params.get("size"), 70))
        color = _safe_color(params.get("color"), "#ef4444")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <rect x="25" y="25" width="{size}" height="{size}" fill="{color}" stroke="#991b1b" stroke-width="2" />
</svg>'''
    
    return ""


def generate_svg_fraction(numerator: int, denominator: int) -> str:
    """Generate SVG for fraction visualization"""
    parts = []
    denominator = max(1, int(denominator))
    numerator = max(0, min(int(numerator), denominator))
    filled = numerator
    
    for i in range(denominator):
        y = 20 + (i * 80 / denominator)
        height = 80 / denominator - 2
        color = "#3b82f6" if i < filled else "#e5e7eb"
        parts.append(f'<rect x="20" y="{y}" width="80" height="{height}" fill="{color}" stroke="#1e40af" stroke-width="1"/>')
    
    return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  {''.join(parts)}
  <text x="60" y="110" text-anchor="middle" font-size="14" font-weight="bold">{numerator}/{denominator}</text>
</svg>'''


def generate_svg_number_line(start: int, end: int, marked: int) -> str:
    """Generate SVG for number line"""
    if end <= start:
        end = start + 1
    width = 300
    padding = 40
    line_width = width - 2 * padding
    
    ticks = []
    for i in range(start, end + 1):
        x = padding + ((i - start) / (end - start)) * line_width
        is_marked = (i == marked)
        tick_height = 15 if is_marked else 10
        color = "#ef4444" if is_marked else "#64748b"
        
        ticks.append(f'<line x1="{x}" y1="50" x2="{x}" y2="{50 + tick_height}" stroke="{color}" stroke-width="2"/>')
        ticks.append(f'<text x="{x}" y="75" text-anchor="middle" font-size="12" fill="{color}">{i}</text>')
    
    return f'''<svg width="{width}" height="100" xmlns="http://www.w3.org/2000/svg">
  <line x1="{padding}" y1="50" x2="{width - padding}" y2="50" stroke="#1e293b" stroke-width="3"/>
  {''.join(ticks)}
</svg>'''


def generate_svg_bar_chart(values: list, labels: list) -> str:
    """Generate SVG bar chart"""
    if not isinstance(values, list) or not values:
        values = [1, 2, 3]
    if not isinstance(labels, list) or len(labels) != len(values):
        labels = [f"Item {i+1}" for i in range(len(values))]

    cleaned_values = []
    for item in values:
        cleaned_values.append(max(0.0, _to_float(item, 0)))

    width = 300
    height = 200
    padding = 40
    max_val = max(cleaned_values) if cleaned_values else 1
    if max_val <= 0:
        max_val = 1
    
    bars = []
    bar_width = (width - 2 * padding) / len(cleaned_values) - 10
    
    for i, (val, label) in enumerate(zip(cleaned_values, labels)):
        x = padding + i * ((width - 2 * padding) / len(cleaned_values))
        bar_height = (val / max_val) * (height - 2 * padding)
        y = height - padding - bar_height
        
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
        color = colors[i % len(colors)]
        
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}"/>')
        bars.append(f'<text x="{x + bar_width/2}" y="{height - 20}" text-anchor="middle" font-size="10">{label}</text>')
        bars.append(f'<text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" font-size="10" font-weight="bold">{val}</text>')
    
    return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#1e293b" stroke-width="2"/>
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="#1e293b" stroke-width="2"/>
  {''.join(bars)}
</svg>'''


def generate_svg_clock(hours: int, minutes: int) -> str:
    """Generate SVG clock face"""
    hours = _to_int(hours, 3)
    minutes = _to_int(minutes, 30) % 60
    hour_angle = (hours % 12) * 30 + (minutes / 60) * 30 - 90
    minute_angle = minutes * 6 - 90
    
    hour_x = 60 + 25 * math.cos(math.radians(hour_angle))
    hour_y = 60 + 25 * math.sin(math.radians(hour_angle))
    minute_x = 60 + 35 * math.cos(math.radians(minute_angle))
    minute_y = 60 + 35 * math.sin(math.radians(minute_angle))
    
    return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="50" fill="white" stroke="#1e293b" stroke-width="3"/>
  <circle cx="60" cy="60" r="3" fill="#1e293b"/>
  <line x1="60" y1="60" x2="{hour_x}" y2="{hour_y}" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
  <line x1="60" y1="60" x2="{minute_x}" y2="{minute_y}" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
  <text x="60" y="25" text-anchor="middle" font-size="12" font-weight="bold">12</text>
  <text x="95" y="65" text-anchor="middle" font-size="12" font-weight="bold">3</text>
  <text x="60" y="100" text-anchor="middle" font-size="12" font-weight="bold">6</text>
  <text x="25" y="65" text-anchor="middle" font-size="12" font-weight="bold">9</text>
</svg>'''
