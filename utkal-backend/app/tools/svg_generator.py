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

    # All 12 hour labels
    hour_labels = []
    for h in range(1, 13):
        angle = h * 30 - 90
        lx = 60 + 42 * math.cos(math.radians(angle))
        ly = 60 + 42 * math.sin(math.radians(angle)) + 4
        hour_labels.append(f'<text x="{_num(lx)}" y="{_num(ly)}" text-anchor="middle" font-size="9" font-weight="bold">{h}</text>')

    return f'<svg width="140" height="140" xmlns="http://www.w3.org/2000/svg"><circle cx="70" cy="70" r="60" fill="white" stroke="#1e293b" stroke-width="3"/><circle cx="70" cy="70" r="3" fill="#1e293b"/>{"".join(hour_labels)}<line x1="70" y1="70" x2="{_num(60 + 25 * math.cos(math.radians(hour_angle)) + 10 * (math.cos(math.radians(hour_angle))))  }" y2="{_num(60 + 25 * math.sin(math.radians(hour_angle)) + 10 * math.sin(math.radians(hour_angle)))}" stroke="#1e293b" stroke-width="5" stroke-linecap="round"/><line x1="70" y1="70" x2="{_num(70 + 45 * math.cos(math.radians(minute_angle)))}" y2="{_num(70 + 45 * math.sin(math.radians(minute_angle)))}" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/></svg>'


def generate_svg_pie_chart(values: list, labels: list, colors: list = None) -> str:
    """Generate SVG pie chart"""
    if not isinstance(values, list) or not values:
        values = [3, 2, 1]
    if not isinstance(labels, list) or len(labels) != len(values):
        labels = [f"Part {i+1}" for i in range(len(values))]
    default_colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
    if not isinstance(colors, list) or len(colors) < len(values):
        colors = default_colors

    total = sum(max(0.0, _to_float(v, 0)) for v in values)
    if total <= 0:
        total = 1
    cx, cy, r = 100, 100, 80
    parts = []
    start_angle = -math.pi / 2
    for i, (val, label) in enumerate(zip(values, labels)):
        frac = max(0.0, _to_float(val, 0)) / total
        sweep = frac * 2 * math.pi
        end_angle = start_angle + sweep
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        large = 1 if sweep > math.pi else 0
        color = _safe_color(colors[i % len(colors)], default_colors[i % len(default_colors)])
        parts.append(f'<path d="M{_num(cx)},{_num(cy)} L{_num(x1)},{_num(y1)} A{r},{r} 0 {large},1 {_num(x2)},{_num(y2)} Z" fill="{color}" stroke="white" stroke-width="1"/>')
        mid_angle = start_angle + sweep / 2
        lx = cx + (r * 0.65) * math.cos(mid_angle)
        ly = cy + (r * 0.65) * math.sin(mid_angle)
        parts.append(f'<text x="{_num(lx)}" y="{_num(ly)}" text-anchor="middle" font-size="11" fill="white" font-weight="bold">{_safe_text(label)}</text>')
        start_angle = end_angle
    return f'<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">{"" .join(parts)}</svg>'


def generate_svg_ruler(length_cm: int = 10) -> str:
    """Generate SVG ruler"""
    length_cm = max(1, min(_to_int(length_cm, 10), 30))
    px_per_cm = 30
    width = length_cm * px_per_cm + 40
    ticks = []
    for mm in range(0, length_cm * 10 + 1):
        x = 20 + mm * px_per_cm / 10
        if mm % 10 == 0:
            ticks.append(f'<line x1="{_num(x)}" y1="20" x2="{_num(x)}" y2="50" stroke="#1e293b" stroke-width="2"/>')
            ticks.append(f'<text x="{_num(x)}" y="65" text-anchor="middle" font-size="11" font-weight="bold">{mm // 10}</text>')
        elif mm % 5 == 0:
            ticks.append(f'<line x1="{_num(x)}" y1="28" x2="{_num(x)}" y2="50" stroke="#64748b" stroke-width="1"/>')
        else:
            ticks.append(f'<line x1="{_num(x)}" y1="38" x2="{_num(x)}" y2="50" stroke="#94a3b8" stroke-width="1"/>')
    return f'<svg width="{width}" height="80" xmlns="http://www.w3.org/2000/svg"><rect x="20" y="20" width="{length_cm * px_per_cm}" height="30" fill="#fef9c3" stroke="#1e293b" stroke-width="2" rx="2"/>{"".join(ticks)}</svg>'


def generate_svg_angle(degrees: int = 60, label: str = "") -> str:
    """Generate SVG angle diagram"""
    degrees = max(1, min(_to_int(degrees, 60), 359))
    cx, cy, arm = 100, 120, 80
    rad = math.radians(degrees)
    x2 = cx + arm * math.cos(-rad)
    y2 = cy + arm * math.sin(-rad)
    arc_r = 30
    ax = cx + arc_r * math.cos(-rad / 2)
    ay = cy + arc_r * math.sin(-rad / 2)
    large = 1 if degrees > 180 else 0
    arc_x2 = cx + arc_r * math.cos(0)
    arc_y2 = cy
    arc_x1 = cx + arc_r * math.cos(-rad)
    arc_y1 = cy + arc_r * math.sin(-rad)
    lbl = label or f"{degrees}°"
    return (f'<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="{cx}" y1="{cy}" x2="{cx + arm}" y2="{cy}" stroke="#1e293b" stroke-width="2"/>'
            f'<line x1="{cx}" y1="{cy}" x2="{_num(x2)}" y2="{_num(y2)}" stroke="#1e293b" stroke-width="2"/>'
            f'<path d="M{_num(arc_x2)},{_num(arc_y2)} A{arc_r},{arc_r} 0 {large},0 {_num(arc_x1)},{_num(arc_y1)}" fill="none" stroke="#3b82f6" stroke-width="2"/>'
            f'<text x="{_num(ax + 10)}" y="{_num(ay - 5)}" font-size="13" fill="#3b82f6" font-weight="bold">{_safe_text(lbl)}</text>'
            f'</svg>')


def generate_svg_thermometer(temperature: int = 37, min_temp: int = 0, max_temp: int = 100, unit: str = "°C") -> str:
    """Generate SVG thermometer"""
    temperature = _to_int(temperature, 37)
    min_temp = _to_int(min_temp, 0)
    max_temp = _to_int(max_temp, 100)
    if max_temp <= min_temp:
        max_temp = min_temp + 1
    temperature = max(min_temp, min(temperature, max_temp))
    tube_h = 160
    frac = (temperature - min_temp) / (max_temp - min_temp)
    fill_h = frac * tube_h
    fill_y = 20 + tube_h - fill_h
    ticks = []
    for t in range(min_temp, max_temp + 1, max(1, (max_temp - min_temp) // 5)):
        frac_t = (t - min_temp) / (max_temp - min_temp)
        ty = 20 + tube_h - frac_t * tube_h
        ticks.append(f'<line x1="55" y1="{_num(ty)}" x2="70" y2="{_num(ty)}" stroke="#64748b" stroke-width="1"/>')
        ticks.append(f'<text x="75" y="{_num(ty + 4)}" font-size="10" fill="#1e293b">{t}{_safe_text(unit)}</text>')
    return (f'<svg width="130" height="220" xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="45" y="20" width="20" height="{tube_h}" rx="10" fill="#e2e8f0" stroke="#1e293b" stroke-width="2"/>'
            f'<rect x="45" y="{_num(fill_y)}" width="20" height="{_num(fill_h)}" rx="10" fill="#ef4444"/>'
            f'<circle cx="55" cy="{20 + tube_h + 15}" r="15" fill="#ef4444" stroke="#1e293b" stroke-width="2"/>'
            f'{"".join(ticks)}'
            f'<text x="55" y="{20 + tube_h + 50}" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">{temperature}{_safe_text(unit)}</text>'
            f'</svg>')


def generate_svg_place_value(number: int = 345) -> str:
    """Generate SVG place value chart"""
    number = max(0, min(_to_int(number, 345), 9999))
    digits = []
    n = number
    place_names = ["Ones", "Tens", "Hundreds", "Thousands"]
    while n > 0:
        digits.append(n % 10)
        n //= 10
    if not digits:
        digits = [0]
    digits.reverse()
    cols = len(digits)
    col_w = 70
    width = cols * col_w + 20
    parts = []
    for i, (d, pname) in enumerate(zip(digits, place_names[cols - 1::-1])):
        x = 10 + i * col_w
        parts.append(f'<rect x="{x}" y="10" width="{col_w - 4}" height="50" fill="#dbeafe" stroke="#3b82f6" stroke-width="2" rx="4"/>')
        parts.append(f'<text x="{x + (col_w - 4) // 2}" y="42" text-anchor="middle" font-size="22" font-weight="bold" fill="#1e40af">{d}</text>')
        parts.append(f'<text x="{x + (col_w - 4) // 2}" y="80" text-anchor="middle" font-size="10" fill="#64748b">{pname}</text>')
    return f'<svg width="{width}" height="95" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def generate_svg_venn_diagram(set_a_label: str = "A", set_b_label: str = "B", intersection_label: str = "A∩B") -> str:
    """Generate SVG Venn diagram (two sets)"""
    return (f'<svg width="260" height="160" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="95" cy="80" r="65" fill="#bfdbfe" fill-opacity="0.6" stroke="#3b82f6" stroke-width="2"/>'
            f'<circle cx="165" cy="80" r="65" fill="#bbf7d0" fill-opacity="0.6" stroke="#10b981" stroke-width="2"/>'
            f'<text x="65" y="85" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e40af">{_safe_text(set_a_label)}</text>'
            f'<text x="195" y="85" text-anchor="middle" font-size="14" font-weight="bold" fill="#065f46">{_safe_text(set_b_label)}</text>'
            f'<text x="130" y="85" text-anchor="middle" font-size="11" fill="#374151">{_safe_text(intersection_label)}</text>'
            f'</svg>')


def generate_svg_coins(coins: list = None) -> str:
    """Generate SVG Indian coins (1, 2, 5, 10 rupee)"""
    if not isinstance(coins, list) or not coins:
        coins = [1, 2, 5, 10]
    coin_colors = {1: "#d1d5db", 2: "#d1d5db", 5: "#fbbf24", 10: "#fbbf24"}
    parts = []
    x = 30
    for val in coins[:8]:
        v = _to_int(val, 1)
        color = coin_colors.get(v, "#d1d5db")
        parts.append(f'<circle cx="{x}" cy="50" r="22" fill="{color}" stroke="#78716c" stroke-width="2"/>')
        parts.append(f'<text x="{x}" y="55" text-anchor="middle" font-size="13" font-weight="bold" fill="#1c1917">₹{v}</text>')
        x += 55
    width = x
    return f'<svg width="{width}" height="100" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def generate_svg_food_chain(organisms: list = None) -> str:
    """Generate SVG food chain diagram with arrows"""
    if not isinstance(organisms, list) or not organisms:
        organisms = ["Grass", "Grasshopper", "Frog", "Snake", "Eagle"]
    organisms = [str(o) for o in organisms[:6]]
    n = len(organisms)
    box_w, box_h, gap = 90, 36, 30
    total_w = n * box_w + (n - 1) * gap + 20
    colors = ["#bbf7d0", "#fef08a", "#fed7aa", "#fecaca", "#e9d5ff", "#bfdbfe"]
    defs = '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#374151"/></marker></defs>'
    parts = []
    for i, org in enumerate(organisms):
        x = 10 + i * (box_w + gap)
        y = 20
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="6" fill="{colors[i % len(colors)]}" stroke="#374151" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + box_w // 2}" y="{y + 23}" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">{_safe_text(org)}</text>')
        if i < n - 1:
            ax = x + box_w + 2
            ay = y + box_h // 2
            parts.append(f'<line x1="{ax}" y1="{ay}" x2="{ax + gap - 4}" y2="{ay}" stroke="#374151" stroke-width="2" marker-end="url(#arr)"/>')
    return f'<svg width="{total_w}" height="76" xmlns="http://www.w3.org/2000/svg">{defs}{"" .join(parts)}</svg>'


def generate_svg_plant_parts(labeled: bool = True) -> str:
    """Generate SVG diagram of a plant with labeled parts"""
    parts = [
        '<rect x="0" y="200" width="260" height="60" fill="#92400e" opacity="0.4"/>',
        '<line x1="130" y1="200" x2="100" y2="240" stroke="#78350f" stroke-width="3"/>',
        '<line x1="130" y1="200" x2="130" y2="250" stroke="#78350f" stroke-width="3"/>',
        '<line x1="130" y1="200" x2="160" y2="240" stroke="#78350f" stroke-width="3"/>',
        '<line x1="100" y1="240" x2="80" y2="255" stroke="#78350f" stroke-width="2"/>',
        '<line x1="160" y1="240" x2="180" y2="255" stroke="#78350f" stroke-width="2"/>',
        '<rect x="122" y="80" width="16" height="120" fill="#16a34a"/>',
        '<ellipse cx="90" cy="130" rx="38" ry="18" fill="#22c55e" transform="rotate(-30 90 130)"/>',
        '<ellipse cx="170" cy="110" rx="38" ry="18" fill="#22c55e" transform="rotate(30 170 110)"/>',
        '<circle cx="130" cy="55" r="25" fill="#fbbf24" stroke="#f59e0b" stroke-width="2"/>',
        '<circle cx="130" cy="55" r="10" fill="#f97316"/>',
    ]
    if labeled:
        parts += [
            '<text x="160" y="52" font-size="11" fill="#1e293b" font-weight="bold">Flower</text>',
            '<line x1="155" y1="55" x2="158" y2="52" stroke="#64748b" stroke-width="1" stroke-dasharray="3"/>',
            '<text x="185" y="115" font-size="11" fill="#1e293b" font-weight="bold">Leaf</text>',
            '<text x="142" y="145" font-size="11" fill="#1e293b" font-weight="bold">Stem</text>',
            '<text x="155" y="235" font-size="11" fill="#1e293b" font-weight="bold">Root</text>',
        ]
    return f'<svg width="260" height="265" xmlns="http://www.w3.org/2000/svg">{"" .join(parts)}</svg>'


def generate_svg_water_cycle(labeled: bool = True) -> str:
    """Generate SVG water cycle diagram"""
    defs = '<defs><marker id="earr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#374151"/></marker></defs>'
    parts = [
        '<rect width="320" height="220" fill="#e0f2fe"/>',
        '<rect x="0" y="185" width="320" height="35" fill="#3b82f6" opacity="0.5"/>',
        '<circle cx="280" cy="40" r="28" fill="#fbbf24" stroke="#f59e0b" stroke-width="2"/>',
        '<ellipse cx="120" cy="45" rx="45" ry="22" fill="white" stroke="#94a3b8" stroke-width="1.5"/>',
        '<ellipse cx="95" cy="55" rx="30" ry="18" fill="white" stroke="#94a3b8" stroke-width="1.5"/>',
        '<ellipse cx="148" cy="55" rx="30" ry="18" fill="white" stroke="#94a3b8" stroke-width="1.5"/>',
        '<line x1="100" y1="72" x2="95" y2="88" stroke="#3b82f6" stroke-width="2"/>',
        '<line x1="118" y1="72" x2="113" y2="88" stroke="#3b82f6" stroke-width="2"/>',
        '<line x1="136" y1="72" x2="131" y2="88" stroke="#3b82f6" stroke-width="2"/>',
        '<path d="M220,185 Q240,130 260,80" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="5" marker-end="url(#earr)"/>',
        '<path d="M165,60 Q185,80 200,100" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="5" marker-end="url(#earr)"/>',
    ]
    if labeled:
        parts += [
            '<text x="222" y="125" font-size="10" fill="#dc2626" font-weight="bold">Evaporation</text>',
            '<text x="168" y="95" font-size="10" fill="#7c3aed" font-weight="bold">Condensation</text>',
            '<text x="82" y="100" font-size="10" fill="#1d4ed8" font-weight="bold">Precipitation</text>',
            '<text x="10" y="180" font-size="10" fill="#1e293b" font-weight="bold">Water Body</text>',
        ]
    return f'<svg width="320" height="220" xmlns="http://www.w3.org/2000/svg">{defs}{"" .join(parts)}</svg>'


def generate_svg_cell(cell_type: str = "animal") -> str:
    """Generate SVG animal or plant cell diagram"""
    is_plant = str(cell_type).lower() == "plant"
    parts = []
    if is_plant:
        parts += [
            '<rect x="20" y="20" width="260" height="200" rx="8" fill="#bbf7d0" stroke="#15803d" stroke-width="4"/>',
            '<rect x="30" y="30" width="240" height="180" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>',
            '<ellipse cx="70" cy="80" rx="22" ry="12" fill="#4ade80" stroke="#15803d" stroke-width="1"/>',
            '<ellipse cx="230" cy="150" rx="22" ry="12" fill="#4ade80" stroke="#15803d" stroke-width="1"/>',
            '<ellipse cx="160" cy="120" rx="55" ry="45" fill="#a5f3fc" stroke="#0891b2" stroke-width="1.5"/>',
            '<circle cx="100" cy="130" r="28" fill="#fde68a" stroke="#d97706" stroke-width="2"/>',
            '<circle cx="100" cy="130" r="12" fill="#f59e0b"/>',
            '<text x="148" y="15" font-size="10" fill="#15803d" font-weight="bold">Cell Wall</text>',
            '<text x="48" y="62" font-size="10" fill="#15803d">Chloroplast</text>',
            '<text x="138" y="118" font-size="10" fill="#0891b2">Vacuole</text>',
            '<text x="72" y="128" font-size="10" fill="#92400e">Nucleus</text>',
        ]
    else:
        parts += [
            '<ellipse cx="150" cy="120" rx="130" ry="100" fill="#fef9c3" stroke="#ca8a04" stroke-width="3"/>',
            '<circle cx="150" cy="120" r="40" fill="#fde68a" stroke="#d97706" stroke-width="2"/>',
            '<circle cx="150" cy="120" r="16" fill="#f59e0b"/>',
            '<ellipse cx="60" cy="80" rx="22" ry="12" fill="#fca5a5" stroke="#dc2626" stroke-width="1.5"/>',
            '<ellipse cx="240" cy="160" rx="22" ry="12" fill="#fca5a5" stroke="#dc2626" stroke-width="1.5"/>',
            '<text x="100" y="118" font-size="10" fill="#92400e">Nucleus</text>',
            '<text x="28" y="68" font-size="10" fill="#dc2626">Mitochondria</text>',
            '<text x="95" y="215" font-size="10" fill="#ca8a04">Cell Membrane</text>',
        ]
    return f'<svg width="300" height="240" xmlns="http://www.w3.org/2000/svg">{"" .join(parts)}</svg>'


def generate_svg_magnet(poles_labeled: bool = True) -> str:
    """Generate SVG horseshoe magnet with field lines"""
    parts = [
        '<path d="M60,40 Q60,160 110,160 Q160,160 160,40" fill="none" stroke="#dc2626" stroke-width="28" stroke-linecap="round"/>',
        '<rect x="46" y="28" width="28" height="32" rx="4" fill="#3b82f6"/>',
        '<rect x="146" y="28" width="28" height="32" rx="4" fill="#ef4444"/>',
    ]
    if poles_labeled:
        parts += [
            '<text x="60" y="50" text-anchor="middle" font-size="13" font-weight="bold" fill="white">N</text>',
            '<text x="160" y="50" text-anchor="middle" font-size="13" font-weight="bold" fill="white">S</text>',
            '<path d="M60,65 Q110,90 160,65" fill="none" stroke="#6366f1" stroke-width="1.5" stroke-dasharray="4"/>',
            '<path d="M60,82 Q110,115 160,82" fill="none" stroke="#6366f1" stroke-width="1.5" stroke-dasharray="4"/>',
            '<text x="110" y="185" text-anchor="middle" font-size="11" fill="#374151">Magnetic Field Lines</text>',
        ]
    return f'<svg width="220" height="200" xmlns="http://www.w3.org/2000/svg">{"" .join(parts)}</svg>'


def generate_svg_states_of_matter(state: str = "all") -> str:
    """Generate SVG showing particle arrangement for states of matter"""
    import random
    random.seed(42)
    state = str(state).lower()
    states_to_show = ["solid", "liquid", "gas"] if state == "all" else [state]
    colors = {"solid": "#3b82f6", "liquid": "#06b6d4", "gas": "#f59e0b"}
    box_w, box_h, gap = 90, 90, 20
    total_w = len(states_to_show) * (box_w + gap) + gap
    parts = []
    for idx, s in enumerate(states_to_show):
        ox = gap + idx * (box_w + gap)
        oy = 30
        parts.append(f'<rect x="{ox}" y="{oy}" width="{box_w}" height="{box_h}" rx="6" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5"/>')
        parts.append(f'<text x="{ox + box_w // 2}" y="{oy + box_h + 18}" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">{s.capitalize()}</text>')
        color = colors.get(s, "#64748b")
        r = 7
        if s == "solid":
            positions = [(ox + 15 + j * 20, oy + 15 + i * 20) for i in range(4) for j in range(4)]
        elif s == "liquid":
            positions = [(ox + 10 + j * 22 + random.randint(-4, 4), oy + 10 + i * 22 + random.randint(-4, 4)) for i in range(4) for j in range(4)]
        else:
            positions = [(ox + random.randint(10, 80), oy + random.randint(10, 80)) for _ in range(10)]
        for px, py in positions:
            if ox + r < px < ox + box_w - r and oy + r < py < oy + box_h - r:
                parts.append(f'<circle cx="{px}" cy="{py}" r="{r}" fill="{color}" opacity="0.8"/>')
    return f'<svg width="{total_w}" height="{30 + box_h + 30}" xmlns="http://www.w3.org/2000/svg">{"" .join(parts)}</svg>'


def generate_svg_shapes_grid(shapes: list = None) -> str:
    """Generate a grid of labeled shapes for identification questions"""
    if not isinstance(shapes, list) or not shapes:
        shapes = ["circle", "square", "triangle", "rectangle"]
    defs = {
        "circle": lambda x, y: f'<circle cx="{x+30}" cy="{y+30}" r="25" fill="#bfdbfe" stroke="#3b82f6" stroke-width="2"/>',
        "square": lambda x, y: f'<rect x="{x+5}" y="{y+5}" width="50" height="50" fill="#bbf7d0" stroke="#10b981" stroke-width="2"/>',
        "triangle": lambda x, y: f'<polygon points="{x+30},{y+5} {x+55},{y+55} {x+5},{y+55}" fill="#fef08a" stroke="#ca8a04" stroke-width="2"/>',
        "rectangle": lambda x, y: f'<rect x="{x+2}" y="{y+15}" width="56" height="30" fill="#fecaca" stroke="#ef4444" stroke-width="2"/>',
        "pentagon": lambda x, y: f'<polygon points="{x+30},{y+5} {x+55},{y+22} {x+46},{y+52} {x+14},{y+52} {x+5},{y+22}" fill="#e9d5ff" stroke="#7c3aed" stroke-width="2"/>',
        "hexagon": lambda x, y: f'<polygon points="{x+30},{y+5} {x+53},{y+17} {x+53},{y+43} {x+30},{y+55} {x+7},{y+43} {x+7},{y+17}" fill="#fed7aa" stroke="#ea580c" stroke-width="2"/>',
    }
    cols = min(len(shapes), 4)
    rows = math.ceil(len(shapes) / cols)
    cell = 80
    parts = []
    for i, shape in enumerate(shapes[:8]):
        col = i % cols
        row = i // cols
        x = col * cell + 5
        y = row * cell + 5
        fn = defs.get(str(shape).lower())
        if fn:
            parts.append(fn(x, y))
        parts.append(f'<text x="{x + 30}" y="{y + 72}" text-anchor="middle" font-size="10" fill="#374151">{_safe_text(shape)}</text>')
    return f'<svg width="{cols * cell + 10}" height="{rows * cell + 10}" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'
