import openai
import requests
import spacy
from spacy.matcher import PhraseMatcher
from dubai_vasp_rules import dubai_vasp_rules

def extract_text(pdf_path, api_key):
    url = "https://api.pdf.co/v1/pdf/convert/to/text"
    
    if pdf_path.startswith("http"):
        payload = {"url": pdf_path}
        files = None
    else:
        files = {"file": open(pdf_path, "rb")}
        payload = None
        
    headers = {"x-api-key": api_key}
    response = requests.post(url, data=payload, files=files, headers=headers)
    return response.json().get('body', '') if response.status_code == 200 else ''

def initialize_matcher():
    nlp = spacy.load("en_core_web_sm")
    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp.make_doc(keyword) for rule in dubai_vasp_rules for keyword in rule["keywords"]]
    matcher.add("VASP_RULES", patterns)
    return nlp, matcher

def gpt_gap_analysis(text, rule, openai_key):
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "You are a Dubai VASP compliance expert"},
            {"role": "user", "content": f"Document excerpt: {text[:12000]}\n\nRule: {rule['requirement']}\n\nSpecific question: {rule['gpt_prompt']}"}
        ],
        max_tokens=500
    )
    return response.choices[0].message['content'].strip()

def analyze_document(pdf_path, pdfco_key, openai_key):
    # Extract text
    text = extract_text(pdf_path, pdfco_key)
    if not text:
        return {"error": "Text extraction failed"}
    
    # Initialize NLP
    nlp, matcher = initialize_matcher()
    doc = nlp(text)
    matches = matcher(doc)
    
    # Identify matched rules
    matched_rule_ids = set()
    for match_id, start, end in matches:
        rule_idx = match_id  # Since we have one match group
        if rule_idx < len(dubai_vasp_rules):
            matched_rule_ids.add(dubai_vasp_rules[rule_idx]["id"])
    
    # Analyze gaps
    gaps = []
    for rule in dubai_vasp_rules:
        if rule["id"] not in matched_rule_ids:
            analysis = gpt_gap_analysis(text, rule, openai_key)
            gaps.append({
                "id": rule["id"],
                "requirement": rule["requirement"],
                "criticality": rule["criticality"],
                "analysis": analysis,
                "reference": rule["reference"]
            })
    
    return {
        "summary": f"{len(gaps)} compliance gaps found",
        "gaps": gaps,
        "matched_rules": [r["id"] for r in dubai_vasp_rules if r["id"] in matched_rule_ids]
    }
