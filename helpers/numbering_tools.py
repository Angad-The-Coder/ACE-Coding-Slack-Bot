def num_to_letter(n):
    """
    Convert number to corresponding letter(s).
        ex. 1 => a, 2 => b ... 27 => aa, 28 => ab
    """
    letter_combo = ""
    while n > 0:
        n -= 1
        letter_combo += chr(97 + n % 26)
        n //= 26
    return letter_combo[::-1] + "."

def int_to_roman(n):
    """
    Convert a Hindu-Arabic numeral to a Roman numeral.
    (Source: https://www.w3resource.com/python-exercises/class-exercises/python-class-exercise-1.php)
    """
    val = [
        1000, 900, 500, 400,
         100,  90,  50,  40,
          10,   9,   5,   4,
           1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ""
    i = 0
    while  n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num.lower() + "."

numbering_dict = {
    "ordered": [lambda x: str(x) + ".",
                num_to_letter,
                int_to_roman,
                lambda x: str(x) + ".",
                num_to_letter],
    "bullet": [lambda x: "●",
               lambda x: "○",
               lambda x: "■",
               lambda x: "●",
               lambda x: "○"]
}

def get_numbering(num, style, indent):
    return numbering_dict.get(style)[indent](num)