// INKLOOM AI - Advanced Content Analysis

const checkBtn = document.getElementById("checkBtn");
const contentInput = document.getElementById("content");
const resultBox = document.getElementById("result");

checkBtn.addEventListener("click", async function () {
    const text = contentInput.value.trim();

    if (text === "") {
        resultBox.textContent = "Please enter content to analyse.";
        return;
    }
    // Connect to Flask Backend
// Connect to Flask Backend
let issues = [];

try {
    const response = await fetch(
        "https://inkloom-ai-mknr.onrender.com/api/content-submission",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                content: text
            })
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(data.message || "Backend request failed");
    }


    console.log("Backend Connected Successfully:", data);
    // Get analysis results from Flask Backend
issues = data.data?.analysis?.issues || [];

console.log("Backend Analysis:", issues);

} catch (error) {
    resultBox.textContent = "Backend connection failed!";
    console.error("Error:", error);
    return;
}
  
    // Clear previous results
    resultBox.replaceChildren();

    // Report heading
    const heading = document.createElement("h2");
    heading.textContent = "Content Analysis Report";
    resultBox.appendChild(heading);

    // Summary
    const summary = document.createElement("p");
    summary.textContent = issues.length +
        " potential issue(s) detected.";
    resultBox.appendChild(summary);

    if (issues.length === 0) {
        const success = document.createElement("p");
        success.textContent =
            "No issues detected by the current demo rules. Human review is still recommended.";
        resultBox.appendChild(success);
        return;
    }

    // Display issue cards
    issues.forEach(function (issue) {

        const card = document.createElement("div");
        card.className = "issue-card";

        const category = document.createElement("h3");
        category.textContent = issue.category;

        const severity = document.createElement("span");
        severity.className =
            "severity " + issue.severity.toLowerCase();
        severity.textContent = issue.severity + " Severity";

        const problem = document.createElement("p");
        problem.textContent = issue.problem;

        const explanation = document.createElement("p");
        explanation.textContent =
            "Explanation: " + issue.explanation;

        const suggestion = document.createElement("p");
        suggestion.textContent =
            "Suggested correction: " + issue.suggestion;

        card.append(category, severity, problem, explanation, suggestion);

        resultBox.appendChild(card);
    });

    // Human review notice
    const notice = document.createElement("p");
    notice.className = "review-notice";
    notice.textContent =
        "Human review required: An authorised brand manager should make the final approval decision.";

    resultBox.appendChild(notice);

});
