
from flask import Flask, jsonify, request
from flask_cors import CORS 
import json 
import os
import re 
from pathlib import Path

app = Flask(__name__)
CORS(app)

# File used to store brand guidelines
GUIDELINES_FILE = Path(__file__).with_name("brand_guidelines.json")


@app.route("/")
def home():
    return jsonify({
        "project": "Inkloom AI",
        "message": "Backend is running successfully"
    })


# SAVE BRAND GUIDELINES
@app.route("/api/brand-guidelines", methods=["POST"])
def brand_guidelines():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid JSON data"
        }), 400

    if not data.get("brandName", "").strip():
        return jsonify({
            "success": False,
            "message": "Brand name is required"
        }), 400

    try:
        with open(GUIDELINES_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return jsonify({
            "success": True,
            "message": "Brand guidelines saved successfully",
            "data": data
        }), 200

    except OSError:
        return jsonify({
            "success": False,
            "message": "Unable to save brand guidelines"
        }), 500


# RETRIEVE BRAND GUIDELINES
@app.route("/api/brand-guidelines", methods=["GET"])
def get_brand_guidelines():

    if not GUIDELINES_FILE.exists():
        return jsonify({
            "success": True,
            "message": "No brand guidelines found",
            "data": None
        }), 200

    try:
        with open(GUIDELINES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return jsonify({
            "success": True,
            "message": "Brand guidelines retrieved successfully",
            "data": data
        }), 200

    except (OSError, json.JSONDecodeError):
        return jsonify({
            "success": False,
            "message": "Unable to retrieve brand guidelines"
        }), 500


# CONTENT SUBMISSION AND ANALYSIS
@app.route("/api/content-submission", methods=["POST"])
def content_submission():

    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()

    if not content:
        return jsonify({
            "success": False,
            "message": "Content is required"
        }), 400

    # Load saved brand guidelines
    try:
        with open(GUIDELINES_FILE, "r", encoding="utf-8") as file:
            saved_data = json.load(file)
    
        guidelines = saved_data.get("data", saved_data)
    
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({
            "success": False,
            "message": "Brand guidelines not found"
        }), 404
    
    issues = []
    lower_text = content.lower()

    # Extract dynamic brand rules
    restricted_words = guidelines.get("restrictedWords", [])
    approved_claims = guidelines.get("approvedFacts", [])
    approved_offers = guidelines.get("offers", "")
    product_specs = guidelines.get("approvedFacts", "")

    # Convert text fields into lists
    def convert_to_list(value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [
                item.strip()
                for item in value.splitlines()
                if item.strip()
            ]
        return []

    restricted_words = convert_to_list(restricted_words)

    # NORMALISE TEXT FOR FLEXIBLE PHRASE MATCHING
    def normalize_phrase(value):
        value = str(value or "").lower()

        # Convert percentage symbols into words
        value = value.replace("%", " percent ")

        # Replace punctuation and hyphens with spaces
        value = re.sub(r"[^a-z0-9]+", " ", value)

        # Remove unnecessary spaces
        return re.sub(r"\s+", " ", value).strip()

    # RULE 1: Smart Restricted Words Detection
    normalized_content = normalize_phrase(content)
    restricted_matches = set()

    for word in restricted_words:
        normalized_word = normalize_phrase(word)

        if not normalized_word:
            continue
            searchable_content = f" {normalized_content} "
            searchable_word = f" {normalized_word} "

            if searchable_word in searchable_content:
                restricted_matches.add(normalized_word)

                issues.append({
                    "category": "Restricted Word",
                    "severity": "High",
                    "problem": f"Restricted phrase detected: {word}",
                    "explanation": "This phrase violates brand guidelines.",
                    "suggestion": "Replace it with approved brand language."
                })

    # RULE 2: Unverified Product Specifications

    spec_pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:GB|TB|mAh|MP|W|Hz|hours?|hrs?|days?|years?)\b"
    )

    detected_specs = re.findall(spec_pattern, content, re.IGNORECASE)

    for spec in detected_specs:
        if not re.search(re.escape(spec), str(product_specs), re.IGNORECASE):
            issues.append({
                "category": "Unverified Specification",
                "severity": "High",
                "problem": f"Unverified specification: {spec}",
                "explanation": "This specification was not found in approved product information.",
                "suggestion": "Verify it against official product specifications."
            })

    # RULE 3: Promotional Violation

    discounts = re.findall(
        r"\b\d+(?:\.\d+)?\s*%\s*(?:off|discount)\b",
        content,
        re.IGNORECASE
    )

    approved_percentages = re.findall(
        r"\b\d+(?:\.\d+)?\s*%",
        str(approved_offers),
        re.IGNORECASE
    )

    for discount in discounts:
        percentage = re.search(
            r"\d+(?:\.\d+)?\s*%",
            discount
        ).group()

        if percentage not in approved_percentages:
            issues.append({
                "category": "Promotional Violation",
                "severity": "Medium",
                "problem": f"Unapproved discount detected: {discount}",
                "explanation": "Promotional offers must be officially authorised.",
                "suggestion": "Use a discount approved by the brand manager."
            })

    # RULE 4: Unsupported Claims

       claim_patterns = [
    r"\bworld's best\b",
    r"\bnumber one\b",
    r"\bno\.?\s*1\b",
    r"\b100%\s*guaranteed\b",
    r"\b100\s*(?:%|percent)\s+guaranteed\b",
    r"\bbest[-\s]+in[-\s]+india\b",
    r"\bguaranteed results\b",
    r"\bcheapest\b",
    r"\bunbreakable\b",
    r"\bunlimited performance\b"
]
    

    approved_claims_text = " ".join(
        convert_to_list(approved_claims)
    ).lower()

    for pattern in claim_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)

        for match in matches:
            normalized_match = normalize_phrase(match)

            if any(
                normalized_match in phrase or phrase in normalized_match
                for phrase in restricted_matches
            ):
                continue

            if match.lower() not in approved_claims_text:
                issues.append({
                    "category": "Unsupported Claim",
                    "severity": "High",
                    "problem": f"Unsupported claim detected: {match}",
                    "explanation": "This claim requires official brand approval.",
                    "suggestion": "Use verified and authorised marketing claims."
                })

    # RULE 5: Compliance Score

    penalty = 0

    for issue in issues:
        if issue["severity"] == "High":
            penalty += 20
        elif issue["severity"] == "Medium":
            penalty += 10

    compliance_score = max(0, 100 - penalty)

    # FINAL RESPONSE

    return jsonify({
        "success": True,
        "message": "Content analysis completed successfully",
        "data": {
            "content": content,
            "brand": guidelines.get("brandName", ""),
            "compliance_score": compliance_score,
            "analysis": {
                "total_issues": len(issues),
                "issues": issues
            }
        }
    }), 200
  


if __name__ == "__main__":
    app.run(debug=True)
