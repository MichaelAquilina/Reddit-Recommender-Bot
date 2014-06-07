from string import ascii_letters, whitespace, digits

ascii_letters_digits = ascii_letters + digits


def word_tokenize(text, remove_case=False):

    s_buffer = ''

    for c in text:
        if c in whitespace:
            if s_buffer:
                yield s_buffer
            s_buffer = ''
        elif c in ascii_letters_digits:
            if remove_case:
                s_buffer += c.lower()
            else:
                s_buffer += c

        # Ignore punctuation and digits?

    if s_buffer:
        yield s_buffer
