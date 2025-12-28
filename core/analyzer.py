import re
import spacy

nlp = spacy.load("en_core_web_sm")

def analyze_text(text: str):
    doc = nlp(text)
    obligations = []
    penalties = []
    entities = set()
    dates = set()

    for sent in doc.sents:
        sentence = sent.text.strip()
        if re.search(r'\b(must|shall|are obligated to|required to|have to|should)\b', sentence, re.IGNORECASE):
            obligations.append(sentence)
        if re.search(r'\b(penalt(y|ies)|fine(s)?|revocation|sanction|punishment)\b', sentence, re.IGNORECASE):
            penalties.append(sentence)

    for ent in doc.ents:
        if ent.label_ in ["ORG", "PERSON", "GPE"]:
            entities.add(ent.text)
        elif ent.label_ == "DATE":
            dates.add(ent.text)

    return {
        "obligations": obligations,
        "penalties": penalties,
        "entities": list(entities),
        "dates": list(dates)
    }