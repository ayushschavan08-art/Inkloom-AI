from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import re
import os
from pathlib import Path
from google import genai
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)
app = Flask(__name__)
CORS(app)

# JSON file used to store the brand guidelines.
GUIDELINES_FILE = Path(__file__).with_name("brand_guidelines.json")


def to_list(value):
    """Convert a list or newline-separated string into a clean list of strings."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.splitlines() if item.strip()]
    if value is None:
        return []
    return [str(value).strip()] if str(value).strip() else []


def normalize_phrase(value):
    """Normalize text so punctuation, hyphens and case do not prevent matching."""
    value = str(value or "").lower()
    value = value.replace("%", " percent ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def load_guidelines():
    """Load guidelines saved by the brand-guidelines endpoint."""
    if not GUIDELINES_FILE.exists():
        return None

    try:
        with GUIDELINES_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    # Support both a plain guidelines object and the wrapped {data: ...} shape.
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]

    return data if isinstance(data, dict) else None
def analyze_with_gemini(content, guidelines):
    prompt = f"""
You are an expert Brand Governance AI Analyst.

Analyze the submitted content using these brand guidelines.

BRAND GUIDELINES:
{json.dumps(guidelines, indent=2)}

SUBMITTED CONTENT:
{content}

Identify:
1. Restricted words or phrases.
2. Unsupported marketing claims.
3. Unverified product specifications.
4. Unapproved promotional offers.
5. Tone and brand messaging inconsistencies.
6. Accessibility or clarity concerns.

Return a clear, structured analysis with:
- Overall assessment
- Identified issues
- Severity (High, Medium, Low)
- Explanation
- Suggested correction

Do not invent brand rules or product facts.
If no issues are found, clearly state that.
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash",
        contents=prompt
    )

    return response.text

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "project": "Inkloom AI",
        "message": "Backend is running successfully"
    }), 200


@app.route("/api/brand-guidelines", methods=["POST"])
def save_brand_guidelines():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid JSON data. Please send a JSON object."
        }), 400

    brand_name = data.get("brandName", "")
    if not isinstance(brand_name, str) or not brand_name.strip():
        return jsonify({
            "success": False,
            "message": "Brand name is required."
        }), 400

    try:
        with GUIDELINES_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except OSError:
        app.logger.exception("Could not save brand guidelines")
        return jsonify({
            "success": False,
            "message": "Unable to save brand guidelines."
        }), 500

    return jsonify({
        "success": True,
        "message": "Brand guidelines saved successfully.",
        "data": data
    }), 200


@app.route("/api/brand-guidelines", methods=["GET"])
def get_brand_guidelines():
    if not GUIDELINES_FILE.exists():
        return jsonify({
            "success": True,
            "message": "No brand guidelines found.",
            "data": None
        }), 200

    try:
        with GUIDELINES_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        app.logger.exception("Could not read brand guidelines")
        return jsonify({
            "success": False,
            "message": "Unable to retrieve brand guidelines."
        }), 500

    return jsonify({
        "success": True,
        "message": "Brand guidelines retrieved successfully.",
        "data": data
    }), 200


@app.route("/api/content-submission", methods=["POST"])
def content_submission():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request. Please send JSON containing content."
        }), 400

    content = data.get("content", "")
    if not isinstance(content, str) or not content.strip():
        return jsonify({
            "success": False,
            "message": "Content is required."
        }), 400

    content = content.strip()
    guidelines = load_guidelines()

    if guidelines is None:
        return jsonify({
            "success": False,
            "message": "Brand guidelines not found. Please save brand guidelines first."
        }), 404
            # AI-powered analysis using Google Gemini
    try:
        gemini_analysis = analyze_with_gemini(content, guidelines)
    except Exception as e:
        app.logger.exception("Gemini analysis failed")
        gemini_analysis = "AI analysis is temporarily unavailable."

    issues = []
    normalized_content = normalize_phrase(content)

    # Read the rule fields. The fallback keys allow common naming variations.
    restricted_words = to_list(guidelines.get("restrictedWords", []))
    approved_facts = to_list(guidelines.get("approvedFacts", []))
    approved_claims = to_list(
        guidelines.get("approvedClaims", guidelines.get("approvedFacts", []))
    )
    approved_offers = guidelines.get("offers", "")
    product_specs = to_list(
        guidelines.get(
            "productSpecs",
            guidelines.get("productSpecifications", guidelines.get("approvedFacts", []))
        )
    )

    # RULE 1: Restricted words and phrases
    restricted_matches = set()

    for word in restricted_words:
        normalized_word = normalize_phrase(word)
        if not normalized_word:
            continue

        if f" {normalized_word} " in f" {normalized_content} ":
            restricted_matches.add(normalized_word)
            issues.append({
                "category": "Restricted Word",
                "severity": "High",
                "problem": f"Restricted phrase detected: {word}",
                "explanation": "This phrase violates the brand guidelines.",
                "suggestion": "Replace it with approved brand language."
            })

    # RULE 2: Unverified product specifications
    spec_pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:GB|TB|mAh|MP|W|Hz|hours?|hrs?|days?|years?)\b"
    )
    detected_specs = re.findall(spec_pattern, content, re.IGNORECASE)
    approved_specs_text = " ".join(product_specs + approved_facts)

    for spec in detected_specs:
        if not re.search(re.escape(spec), approved_specs_text, re.IGNORECASE):
            issues.append({
                "category": "Unverified Specification",
                "severity": "High",
                "problem": f"Unverified specification: {spec}",
                "explanation": "This specification was not found in the approved product information.",
                "suggestion": "Verify it against the official product specifications."
            })

    # RULE 3: Promotional violations
    discounts = re.findall(
        r"\b\d+(?:\.\d+)?\s*%\s*(?:off|discount)\b",
        content,
        re.IGNORECASE
    )
    approved_percentages = {
        normalize_phrase(match).replace(" percent", "").strip()
        for match in re.findall(
            r"\b\d+(?:\.\d+)?\s*%",
            " ".join(to_list(approved_offers)),
            re.IGNORECASE
        )
    }

    for discount in discounts:
        percentage_match = re.search(r"\d+(?:\.\d+)?", discount)
        percentage = percentage_match.group() if percentage_match else ""

        if percentage not in approved_percentages:
            issues.append({
                "category": "Promotional Violation",
                "severity": "Medium",
                "problem": f"Unapproved discount detected: {discount}",
                "explanation": "Promotional offers must be officially authorised.",
                "suggestion": "Use a discount approved by the brand manager."
            })

    # RULE 4: Unsupported marketing claims
    claim_patterns = [
        r"\bworld['’]s best\b",
        r"\bnumber one\b",
        r"\bno\.?\s*1\b",
        r"\b100\s*%\s*guaranteed\b",
        r"\b100\s*percent\s+guaranteed\b",
        r"\bbest[-\s]+in[-\s]+india\b",
        r"\bguaranteed results\b",
        r"\bcheapest\b",
        r"\bunbreakable\b",
        r"\bunlimited performance\b"
    ]

    approved_claims_text = normalize_phrase(" ".join(approved_claims))

    for pattern in claim_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)

        for match in matches:
            normalized_match = normalize_phrase(match)

            # A phrase already flagged as a restricted word should not be
            # duplicated as an unsupported-claim issue.
            if any(
                normalized_match in restricted_phrase
                or restricted_phrase in normalized_match
                for restricted_phrase in restricted_matches
            ):
                continue

            if normalized_match not in approved_claims_text:
                issues.append({
                    "category": "Unsupported Claim",
                    "severity": "High",
                    "problem": f"Unsupported claim detected: {match}",
                    "explanation": "This claim requires official brand approval.",
                    "suggestion": "Use verified and authorised marketing claims."
                })

    # RULE 5: Compliance score
    penalty = sum(
        20 if issue["severity"] == "High" else 10
        for issue in issues
    )
    compliance_score = max(0, 100 - penalty)

    return jsonify({
        "success": True,
        "message": "Content analysis completed successfully.",
        "data": {
            "content": content,
            "brand": guidelines.get("brandName", ""),
            "compliance_score": compliance_score,
           "analysis": {
    "total_issues": len(issues),
    "issues": issues
},
"gemini_analysis": gemini_analysis
        }
    }), 200


if __name__ == "__main__":
    # Render supplies its own PORT environment variable.
    port = int(__import__("os").environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
