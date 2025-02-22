!pip install tldextract
!pip install scholarly
!pip install sentence-transformers
!pip install transformers

import requests
import re
from urllib.parse import urlparse
import tldextract 
import scholarly
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# Load Semantic Similarity Model
semantic_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

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
        return known_trusted_domains[root_domain] * 100
    elif root_domain in known_untrusted_domains:
        return known_untrusted_domains[root_domain] * 100
    else:
        return 70  # Default score for unknown sources

# Content relevance using semantic similarity
def get_content_relevance(user_query, page_text):
    similarity_score = util.pytorch_cos_sim(semantic_model.encode(user_query), semantic_model.encode(page_text)).item() * 100
    return similarity_score

# Fact-checking placeholder function
def check_facts(text):
    return 50  # Default uncertainty score

# Bias detection using sentiment analysis
def check_bias(content):
    sentiment_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment")
    sentiment_result = sentiment_pipeline(content[:512])[0]  # Process first 512 characters
    return 100 if sentiment_result["label"] == "POSITIVE" else 50 if sentiment_result["label"] == "NEUTRAL" else 30

# Citation count placeholder function
def check_citations(url):
    return 0  # Default to no citations found

# Fetch Google Cache version of a URL
def get_google_cache_url(url):
    return f"https://webcache.googleusercontent.com/search?q=cache:{url}"

def fetch_from_google_cache(url):
    cache_url = get_google_cache_url(url)
    try:
        response = requests.get(cache_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = " ".join([p.text for p in soup.find_all("p")])
    except Exception as e:
        return {"error": f"Failed to fetch from Google Cache: {str(e)}"}
    
    return page_text

# Main function to assess URL validity
def rate_url_validity(user_query: str, url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        # Attempt to fetch the URL directly
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes (e.g., 404)
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = " ".join([p.text for p in soup.find_all("p")])
    except requests.exceptions.RequestException as e:
        # If direct fetch fails, try Google Cache
        if "404" in str(e):
            print(f"Direct fetch failed, trying Google Cache...")
            page_text = fetch_from_google_cache(url)
            if isinstance(page_text, dict) and "error" in page_text:
                return page_text  # Return the error if Google Cache also fails
        else:
            return {"error": f"Failed to fetch content: {str(e)}"}
    
    domain_trust = get_rule_based_score(url)
    content_relevance = get_content_relevance(user_query, page_text)
    fact_check_score = check_facts(page_text)
    bias_score = check_bias(page_text)
    citation_score = check_citations(url)
    
    final_score = (
        (0.3 * domain_trust) +
        (0.3 * content_relevance) +
        (0.2 * fact_check_score) +
        (0.1 * bias_score) +
        (0.1 * citation_score)
    )
    
    return {
        "Domain Trust": domain_trust,
        "Content Relevance": content_relevance,
        "Fact-Check Score": fact_check_score,
        "Bias Score": bias_score,
        "Citation Score": citation_score,
        "Final Validity Score": final_score
    }

if __name__ == "__main__":
    user_prompt = "Is it safe to take a newborn on a plane?"
    url_to_check = "https://www.mayoclinic.org/healthy-lifestyle/infant-and-toddler-health/in-depth/traveling-with-children/art-20044531"
    result = rate_url_validity(user_prompt, url_to_check)
    print(result)

# Test case: 
user_prompt = "Is it safe to take a newborn on a plane?"
url_to_check = "https://www.mayoclinic.org/healthy-lifestyle/infant-and-toddler-health/in-depth/traveling-with-children/art-20044531"

result = rate_url_validity(user_prompt, url_to_check)
print(result)
