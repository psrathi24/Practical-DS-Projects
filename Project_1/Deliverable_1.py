import requests
import re
from urllib.parse import urlparse
import tldextract
from scispacy.linking import EntityLinker
import spacy
import scholarly
from bs4 import BeautifulSoup
import numpy as np

# Load NLP model for scientific texts
nlp = spacy.load("en_core_sci_md")
linker = EntityLinker(name="umls")
nlp.add_pipe(linker)

# Example ML-based placeholder function
def get_ml_score(url):
    return 0.85  # Placeholder value

# Rule-based scoring function
def get_rule_based_score(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    extracted = tldextract.extract(domain)
    root_domain = f"{extracted.domain}.{extracted.suffix}"
    
    known_trusted_domains = {"nejm.org": 0.98, "thelancet.com": 0.97, "nature.com": 0.95, "sciencedirect.com": 0.94, "nih.gov": 0.99}
    known_untrusted_domains = {"pseudoscience.net": 0.2, "misinfohealth.com": 0.1}
    
    if root_domain in known_trusted_domains:
        return known_trusted_domains[root_domain]
    elif root_domain in known_untrusted_domains:
        return known_untrusted_domains[root_domain]
    else:
        return 0.7  # Default score for unknown sources

# NLP-based content analysis for scientific/medical texts
def get_nlp_score(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            doc = nlp(content)
            entities = [ent.text for ent in doc.ents if ent.label_ in ["DISEASE", "CHEMICAL", "GENE"]]
            return min(1.0, len(entities) / 100)  # Scale credibility score based on number of valid entities
    except requests.RequestException:
        return 0.5  # Default NLP score if content can't be retrieved

# Scholarly citation count-based credibility scoring
def get_citation_score(url):
    try:
        search_query = scholarly.search_pubs(url)
        pub = next(search_query, None)
        if pub and "num_citations" in pub.bib:
            return min(1.0, pub.bib["num_citations"] / 1000)  # Normalize citation count
    except Exception:
        return 0.5  # Default citation score if not found

# Syntax validation
def validate_syntax(url):
    return bool(re.match(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', url))

# Statistical validity (word count analysis)
def check_statistical_validity(content):
    word_count = len(content.split())
    return 1.0 if word_count > 500 else 0.5

# Factual correctness (basic heuristic using trusted references)
def check_factual_correctness(content):
    trusted_terms = ["randomized controlled trial", "peer-reviewed", "systematic review"]
    matches = sum(1 for term in trusted_terms if term in content.lower())
    return min(1.0, matches / len(trusted_terms))

# Hybrid credibility scoring function
def assess_credibility(url):
    if not validate_syntax(url):
        return {"score": 0.0, "explanation": "Invalid URL syntax."}
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {"score": 0.4, "explanation": "Content could not be retrieved successfully."}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text()
        
        ml_score = get_ml_score(url)
        rule_score = get_rule_based_score(url)
        nlp_score = get_nlp_score(url)
        citation_score = get_citation_score(url)
        stat_validity = check_statistical_validity(content)
        factual_correctness = check_factual_correctness(content)
        
        final_score = np.mean([ml_score, rule_score, nlp_score, citation_score, stat_validity, factual_correctness])
        explanation = f"This source has a credibility score of {final_score:.2f} based on ML evaluation, domain reputation, content analysis, citation count, statistical validity, and factual correctness."
        
        return {"score": round(final_score, 2), "explanation": explanation}
    except Exception:
        return {"score": 0.4, "explanation": "Error processing the request."}

if __name__ == "__main__":
    user_url = input("Enter the URL to assess credibility: ")
    result = assess_credibility(user_url)
    print(result)
