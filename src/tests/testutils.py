__about__ = """
Contains a bunch of helper methods often used in tests to perform assertions.
"""


def generator_unordered_cmp(gen, list1):
    # Compares a generator to a list for equality
    return unordered_list_cmp(list(gen), list1)


def generator_cmp(gen, list1):
    # Compares a generator to a list for equality
    return list(gen) == list1


def unordered_list_cmp(list1, list2):
    # Check lengths first for slight improvement in performance
    return len(list1) == len(list2) and sorted(list1) == sorted(list2)
