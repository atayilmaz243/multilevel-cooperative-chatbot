document.addEventListener("DOMContentLoaded", () => {
    const slider = document.getElementById("coopSlider");
    const currentLevelLabel = document.getElementById("currentLevel");
    const levelDescription = document.getElementById("levelDescription");
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const chatHistory = document.getElementById("chatHistory");
    const sendBtn = document.getElementById("sendBtn");

    // Mapping levels to description texts and labels
    const levelMapping = {
        1: { label: "Level: 1 (Uncooperative)", desc: "Negative and unwilling to help." },
        2: { label: "Level: 2", desc: "Very reluctant, complaining but gives tiny hints." },
        3: { label: "Level: 3 (Suggestive)", desc: "Friendly, suggests working on it together." },
        4: { label: "Level: 4", desc: "Helpful but leaves the final decision up to you." },
        5: { label: "Level: 5 (Commander)", desc: "Takes over. Gives direct, authoritative step-by-step commands." },
        6: { label: "Level: 6", desc: "Helpful and educational, explains the 'why'." },
        7: { label: "Level: 7", desc: "Polite and extremely detailed assistant." },
        8: { label: "Level: 8", desc: "Overly eager, does things very quickly for you." },
        9: { label: "Level: 9", desc: "Proactive expert, anticipates future errors." },
        10: { label: "Level: 10 (Ultra Cooperative)", desc: "Limitless. Designs everything for you instantly with immense joy." }
    };

    // Update Slider UI
    slider.addEventListener("input", (e) => {
        const val = e.target.value;
        currentLevelLabel.textContent = levelMapping[val].label;
        levelDescription.textContent = levelMapping[val].desc;
    });

    // Helper to append a message to the UI
    const appendMessage = (sender, text) => {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender === "user" ? "user-message" : "ai-message"}`;

        const avatarDiv = document.createElement("div");
        avatarDiv.className = `avatar ${sender === "user" ? "user-avatar" : "ai-avatar"}`;
        avatarDiv.textContent = sender === "user" ? "U" : "AI";

        const bubbleDiv = document.createElement("div");
        bubbleDiv.className = "bubble";

        // simple text replacement for line breaks (if any)
        const p = document.createElement("p");
        p.textContent = text;
        bubbleDiv.appendChild(p);

        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);

        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };

    // Helper to show/hide loading animation
    let loadingDiv = null;
    const showLoading = () => {
        loadingDiv = document.createElement("div");
        loadingDiv.className = "message ai-message";
        loadingDiv.innerHTML = `
            <div class="avatar ai-avatar">AI</div>
            <div class="bubble typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        chatHistory.appendChild(loadingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };

    const removeLoading = () => {
        if (loadingDiv) {
            chatHistory.removeChild(loadingDiv);
            loadingDiv = null;
        }
    };

    // Handle Form Submit
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        const level = parseInt(slider.value, 10);

        // Display User Message
        appendMessage("user", text);
        userInput.value = "";

        // Disable input while fetching
        userInput.disabled = true;
        sendBtn.disabled = true;

        showLoading();

        try {
            // Adjust the URL if your backend is hosted elsewhere
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text, level: level })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Error from server");
            }

            const data = await response.json();
            removeLoading();
            appendMessage("ai", data.reply);

        } catch (error) {
            removeLoading();
            appendMessage("ai", `Error: ${error.message}`);
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    });
});
