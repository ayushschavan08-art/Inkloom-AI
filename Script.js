
const analyzeBtn = document.getElementById("analyzeBtn");
const contentInput = document.getElementById("content");
const resultDiv = document.getElementById("result");

analyzeBtn.addEventListener("click", async () => {
    const content = contentInput.value.trim();

    if (!content) {
        resultDiv.innerHTML = "Please enter content first.";
        return;
    }

    resultDiv.innerHTML = "Analyzing content...";
    analyzeBtn.disabled = true;

    try {
        const response = await fetch(
            "http://127.0.0.1:5000/api/content-submission",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    content: content
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Analysis failed");
        }

        resultDiv.textContent = JSON.stringify(data, null, 2);

    } catch (error) {
        resultDiv.textContent =
            "Error: " + error.message +
            ". Please check whether the backend is running.";
    } finally {
        analyzeBtn.disabled = false;
    }
});
