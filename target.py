def calculate_average(numbers):
    if not numbers:
        return 0.0
    total = sum(numbers)
    return total / len(numbers)

def count_vowels(s):
    vowels = "aeiouAEIOU"
    count = 0
    for char in s:
        if char in vowels:
            count += 1
    return count

def reverse_string(s):
    result = ""
    for i in range(len(s) - 1, -1, -1):
        result += s[i]
    return result