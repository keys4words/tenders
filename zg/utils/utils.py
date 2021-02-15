def get_keywords(filename):
    keywords = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            keywords.append(line.strip())
        return keywords