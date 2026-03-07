"""SVG Image Generator for Visual Questions"""

def generate_svg_shape(shape_type: str, params: dict) -> str:
    """Generate SVG for geometric shapes"""
    
    if shape_type == "circle":
        radius = params.get("radius", 50)
        color = params.get("color", "#3b82f6")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="{radius}" fill="{color}" stroke="#1e40af" stroke-width="2"/>
</svg>'''
    
    elif shape_type == "rectangle":
        width = params.get("width", 80)
        height = params.get("height", 60)
        color = params.get("color", "#10b981")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="30" width="{width}" height="{height}" fill="{color}" stroke="#065f46" stroke-width="2"/>
</svg>'''
    
    elif shape_type == "triangle":
        color = params.get("color", "#f59e0b")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <polygon points="60,20 100,100 20,100" fill="{color}" stroke="#92400e" stroke-width="2"/>
</svg>'''
    
    elif shape_type == "square":
        size = params.get("size", 70)
        color = params.get("color", "#ef4444")
        return f'''<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <rect x="25" y="25" width="{size}" height="{size}" fill="{color}" stroke="#991b1b" stroke-width="2"/>
</svg>'''
    
    return ""


def generate_svg_fraction(numerator: int, denominator: int) -> str:
    """Generate SVG for fraction visualization"""
    parts = []
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
    width = 300
    height = 200
    padding = 40
    max_val = max(values) if values else 1
    
    bars = []
    bar_width = (width - 2 * padding) / len(values) - 10
    
    for i, (val, label) in enumerate(zip(values, labels)):
        x = padding + i * ((width - 2 * padding) / len(values))
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
    hour_angle = (hours % 12) * 30 + (minutes / 60) * 30 - 90
    minute_angle = minutes * 6 - 90
    
    import math
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
