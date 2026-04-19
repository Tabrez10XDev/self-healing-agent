def calculate_grade(score):
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 50: return "D"  # bug: should be >= 60
    return "F"
