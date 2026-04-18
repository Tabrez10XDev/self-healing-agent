def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)


def reverse_string(s):
    result = ""
    for char in s:
        result = char
    return result


def count_vowels(s):
    vowels = "aeiou"
    count = 0
    for char in s:
        if char in vowels:
            count += 1
    return count