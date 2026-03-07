document.addEventListener('DOMContentLoaded', () => {
    const wsStatusSpan = document.getElementById('ws-status');
    const toggleLedBtn = document.getElementById('btn-toggle-led');
    const logContainer = document.getElementById('log-container');

    // Automatically determine WS URL based on current host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // e.g., 127.0.0.1:8080 or the ESP32's local IP
    const wsUrl = `${protocol}//${host}/ws`;

    let socket = null;

    function addLog(message, direction = 'in') {
        const time = new Date().toLocaleTimeString();
        const div = document.createElement('div');
        div.className = 'log-entry';

        let dirIcon = direction === 'out' ? '↗️ ' : '↙️ ';
        let dirClass = direction === 'out' ? 'log-direction-out' : 'log-direction-in';

        div.innerHTML = `<span class="log-time">[${time}]</span> <span class="${dirClass}">${dirIcon} ${message}</span>`;
        logContainer.appendChild(div);

        // Auto-scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    function connectWebSocket() {
        addLog(`Connecting to ${wsUrl}...`, 'out');
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            wsStatusSpan.textContent = 'Connected';
            wsStatusSpan.className = 'status-connected';
            toggleLedBtn.disabled = false;
            addLog('WebSocket connection established.');
        };

        socket.onmessage = (event) => {
            const data = event.data;
            addLog(`Received: ${data}`, 'in');
        };

        socket.onclose = () => {
            wsStatusSpan.textContent = 'Disconnected';
            wsStatusSpan.className = 'status-disconnected';
            toggleLedBtn.disabled = true;
            addLog('WebSocket connection closed.', 'in');

            // Reconnect after 3 seconds
            setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (error) => {
            addLog(`WebSocket Error occurred.`, 'in');
            console.error('WebSocket Error:', error);
        };
    }

    // Toggle LED Button Handler
    toggleLedBtn.addEventListener('click', () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const command = "LED_TOGGLE";
            socket.send(command);
            addLog(`Sent command: ${command}`, 'out');
        } else {
            addLog('Cannot send command. WebSocket is not open.', 'in');
        }
    });

    // Start Connection
    connectWebSocket();
});
