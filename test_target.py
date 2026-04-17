from target import calculate_average, reverse_string, count_vowels


def test_average_normal():
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0


def test_average_empty():
    try:
        result = calculate_average([])
        assert result == 0
    except ValueError:
        pass


def test_reverse_normal():
    assert reverse_string("hello") == "olleh"


def test_reverse_single():
    assert reverse_string("a") == "a"


def test_vowels_lowercase():
    assert count_vowels("hello") == 2


def test_vowels_uppercase():
    assert count_vowels("HELLO") == 2