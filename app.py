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
            }
        }
    }), 200


if __name__ == "__main__":
    # Render supplies its own PORT environment variable.
    port = int(__import__("os").environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
