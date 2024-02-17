def number_to_words(amount):
    if amount < 0:
        return "Negative " + number_to_words(-amount)

    if amount == 0:
        return "Zero"

    words = ""
    units = [
        "", "One", "Two", "Three", "Four",
        "Five", "Six", "Seven", "Eight", "Nine"
    ]
    teens = [
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
        "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty",
        "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    ]
    thousands = [
        "", "Thousand", "Million", "Billion", "Trillion",
        "Quadrillion", "Quintillion", "Sextillion", "Septillion",
        "Octillion", "Nonillion", "Decillion"
    ]

    def parse_hundred(hundred):
        result = ""
        if hundred > 99:
            result += units[hundred // 100] + " Hundred "
            hundred %= 100
        if hundred > 19:
            result += tens[hundred // 10] + " "
            hundred %= 10
        if 0 < hundred < 10:
            result += units[hundred] + " "
        elif hundred >= 10:
            result += teens[hundred - 10] + " "
        return result

    def parse_group(number, index):
        return "" if number == 0 else number_to_words(number) + " " + thousands[index] + ", "

    i = 0
    while amount >= 1000:
        words = parse_group(amount % 1000, i) + words
        amount //= 1000
        i += 1
    words = parse_hundred(amount) + words

    return words.strip().rstrip(',')

# Example usage:
print(number_to_words(123456789))

