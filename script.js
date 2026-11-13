
// ==========================================
// INKLOOM AI - CONTENT REVIEW SYSTEM
// Frontend to Flask Backend Integration
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    const checkBtn = document.getElementById("checkBtn");
    const contentInput = document.getElementById("content");
    const resultBox = document.getElementById("result");

    const API_URL =
        "https://inkloom-ai-mknr.onrender.com/api/content-submission";

    if (!checkBtn || !contentInput || !resultBox) {
        console.error("Inkloom AI: Required HTML elements not found.");
        return;
    }

    // Safely create and display text elements
    function addText(parent, tag, text, className = "") {
        const element = document.createElement(tag);
        element.textContent = text || "Not provided";

        if (className) {
            element.className = className;
        }

        parent.appendChild(element);
        return element;
    }

    // Display analysis results
    function displayResults(issues, totalIssues) {

        resultBox.replaceChildren();

        addText(resultBox, "h2", "Content Analysis Report");

        addText(
            resultBox,
            "p",
            `${totalIssues} potential issue(s) detected.`
        );

        if (issues.length === 0) {

            addText(
                resultBox,
                "p",
                "No issues detected by the current analysis rules. Human review is still recommended.",
                "success-message"
            );

            return;
        }

        // Create individual issue cards
        issues.forEach(function (issue, index) {

            const card = document.createElement("div");
            card.className = "issue-card";

            addText(
                card,
                "h3",
                `${index + 1}. ${issue.category || "General Issue"}`
            );

            const severity = (
                issue.severity || "Unknown"
            ).toString();

            const severityElement = addText(
                card,
                "span",
                `${severity} Severity`,
                "severity"
            );

            severityElement.classList.add(
                severity.toLowerCase().replace(/[^a-z0-9-]/g, "")
            );

            addText(
                card,
                "p",
                `Problem: ${issue.problem || "Not specified"}`
            );

            addText(
                card,
                "p",
                `Explanation: ${issue.explanation || "No explanation provided."}`
            );

            addText(
                card,
                "p",
                `Suggested correction: ${issue.suggestion || "Please review manually."}`
            );

            resultBox.appendChild(card);
        });

        // Human approval notice
        addText(
            resultBox,
            "p",
            "Human review required: An authorised brand manager should make the final approval decision.",
            "review-notice"
        );
    }

    // Handle Check Content button
    checkBtn.addEventListener("click", async function () {

        const content = contentInput.value.trim();

        if (!content) {
            resultBox.replaceChildren();

            addText(
                resultBox,
                "p",
                "Please enter some content before starting the analysis."
            );

            return;
        }

        checkBtn.disabled = true;
        checkBtn.textContent = "Analysing...";

        resultBox.replaceChildren();

        addText(
            resultBox,
            "h2",
            "Analysis in Progress..."
        );

        addText(
            resultBox,
            "p",
            "Inkloom AI is checking your content against brand guidelines. Please wait."
        );

        try {

            const response = await fetch(API_URL, {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    content: content
                })
            });

            // Read response safely
            const responseText = await response.text();

            let result;

            try {
                result = JSON.parse(responseText);
            } catch (parseError) {
                throw new Error(
                    "Backend returned an invalid response. Please check the Render logs."
                );
            }

            if (!response.ok) {
                throw new Error(
                    result.error ||
                    result.message ||
                    `Server error: ${response.status}`
                );
            }

            console.log("Inkloom AI Backend Response:", result);

            // Support the response structure shown in your screenshot
            const analysisData =
                result.data?.analysis ||
                result.analysis ||
                result.data ||
                result;

            const issues =
                analysisData.issues ||
                [];

            if (!Array.isArray(issues)) {
                throw new Error(
                    "Analysis response does not contain a valid issues list."
                );
            }

            const totalIssues =
                analysisData.total_issues ??
                result.total_issues ??
                issues.length;

            console.log("Detected Issues:", issues);

            // Display formatted results
            displayResults(issues, totalIssues);

        } catch (error) {

            console.error("Inkloom AI Error:", error);

            resultBox.replaceChildren();

            addText(
                resultBox,
                "h2",
                "Analysis Failed"
            );

            addText(
                resultBox,
                "p",
                error.message || "Something went wrong. Please try again."
            );

        } finally {

            checkBtn.disabled = false;
            checkBtn.textContent = "Check Content";

        }

    });

    console.log("Inkloom AI Content Review initialized successfully.");

});
