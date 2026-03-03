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
        1: { label: "Level: 1 (Uncooperative)", desc: "Negative and unwilling to help.", color: "linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)" }, // Deep Red
        2: { label: "Level: 2", desc: "Very reluctant, complaining but gives tiny hints.", color: "linear-gradient(135deg, #431407 0%, #7c2d12 100%)" }, // Orange-Red
        3: { label: "Level: 3 (Suggestive)", desc: "Friendly, suggests working on it together.", color: "linear-gradient(135deg, #172554 0%, #1d4ed8 100%)" }, // Friendly Blue
        4: { label: "Level: 4", desc: "Helpful but leaves the final decision up to you.", color: "linear-gradient(135deg, #0f172a 0%, #3b82f6 100%)" },
        5: { label: "Level: 5 (Commander)", desc: "Takes over. Gives direct, authoritative step-by-step commands.", color: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)" }, // Dark Indigo
        6: { label: "Level: 6", desc: "Helpful and educational, explains the 'why'.", color: "linear-gradient(135deg, #064e3b 0%, #047857 100%)" }, // Emerald 
        7: { label: "Level: 7", desc: "Polite and extremely detailed assistant.", color: "linear-gradient(135deg, #14532d 0%, #16a34a 100%)" }, // Green
        8: { label: "Level: 8", desc: "Overly eager, does things very quickly for you.", color: "linear-gradient(135deg, #065f46 0%, #10b981 100%)" }, // Mint Green
        9: { label: "Level: 9", desc: "Proactive expert, anticipates future errors.", color: "linear-gradient(135deg, #022c22 0%, #34d399 100%)" }, // Bright Sea Green
        10: { label: "Level: 10 (Ultra Cooperative)", desc: "Limitless. Designs everything for you instantly with immense joy.", color: "linear-gradient(135deg, #064e3b 0%, #84cc16 100%)" } // Extreme Neon Green
    };

    // Update Slider UI
    slider.addEventListener("input", (e) => {
        const val = e.target.value;
        currentLevelLabel.textContent = levelMapping[val].label;
        levelDescription.textContent = levelMapping[val].desc;
        // Dynamically update the background
        document.body.style.background = levelMapping[val].color;
    });

    // Initialize with level 5
    document.body.style.background = levelMapping[slider.value].color;

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

        // Add thinking class for pulse animation
        document.body.classList.add("thinking");

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
            document.body.classList.remove("thinking");
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    });
});
