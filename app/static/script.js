document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messages-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const fileUpload = document.getElementById('file-upload');
    const toolSelector = document.getElementById('tool-selector');
    const toolMenu = document.getElementById('tool-menu');
    const toolOptions = document.querySelectorAll('.tool-option');
    const currentToolName = document.getElementById('current-tool-name');
    const currentToolIcon = document.getElementById('current-tool-icon');

    let currentTool = 'chat'; // Default tool

    // Auto-resize textarea
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = '24px'; // specific base height
    });

    // Toggle Tool Menu
    toolSelector.addEventListener('click', (e) => {
        e.stopPropagation();
        toolMenu.classList.toggle('hidden');
    });

    // Close menu when clicking outside
    document.addEventListener('click', () => {
        toolMenu.classList.add('hidden');
    });

    // Select Tool
    toolOptions.forEach(option => {
        option.addEventListener('click', () => {
            if (option.classList.contains('disabled')) return;

            toolOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');

            currentTool = option.dataset.tool;
            currentToolName.textContent = option.querySelector('span:last-child').textContent;
            currentToolIcon.textContent = option.querySelector('.material-icons-round').textContent;
        });
    });

    // Send Message
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // User Message UI
        addMessage(text, 'user');
        userInput.value = '';
        userInput.style.height = 'auto';

        // Loading UI
        const loadingId = addLoadingMessage();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text,
                    tool: currentTool
                })
            });

            const data = await response.json();

            // Remove loading
            removeMessage(loadingId);

            // AI Response UI
            if (response.ok) {
                addMessage(data.response, 'ai', data.sources);
            } else {
                addMessage(`Error: ${data.detail || 'Unknown error'}`, 'ai');
            }

        } catch (error) {
            removeMessage(loadingId);
            addMessage(`Network Error: ${error.message}`, 'ai');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // File Upload
    fileUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        // Show upload started message
        const uploadMsgId = addMessage(`📤 Uploading ${file.name}...`, 'system');

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            // Remove upload message
            removeMessage(uploadMsgId);

            if (response.ok) {
                // Show status based on processing result
                if (data.status === 'success') {
                    addMessage(`✅ ${data.message || 'File uploaded and processed successfully!'}`, 'system');
                    addMessage('💡 You can now switch to "Find Documents" mode to search this file.', 'system');
                } else if (data.status === 'partial') {
                    addMessage(`⚠️ ${data.message || 'File uploaded but processing incomplete.'}`, 'system');
                } else if (data.status === 'failed') {
                    addMessage(`❌ ${data.message || 'Processing failed.'}`, 'system');
                }
            } else {
                addMessage(`❌ Upload failed: ${data.detail}`, 'system');
            }
        } catch (error) {
            removeMessage(uploadMsgId);
            addMessage(`❌ Upload error: ${error.message}`, 'system');
        }

        // Reset file input
        e.target.value = '';
    });

    // UI Helpers
    function addMessage(text, sender, sources = []) {
        const div = document.createElement('div');
        div.className = `message ${sender}-message`;

        let icon = sender === 'user' ?
            '<div class="avatar user-avatar">U</div>' :
            '<div class="avatar"><span class="material-icons-round">auto_awesome</span></div>';

        if (sender === 'system') {
            icon = '<div class="avatar"><span class="material-icons-round">info</span></div>';
        }

        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `<div class="sources"><small>Sources: ${sources.join(', ')}</small></div>`;
        }

        // Basic formatting (replace newlines with <br>)
        const formattedText = text.replace(/\n/g, '<br>');

        div.innerHTML = `
            ${sender !== 'user' ? icon : ''}
            <div class="content">
                <p>${formattedText}</p>
                ${sourcesHtml}
            </div>
            ${sender === 'user' ? icon : ''}
        `;

        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return div.id = 'msg-' + Date.now();
    }

    function addLoadingMessage() {
        const div = document.createElement('div');
        div.className = `message ai-message loading`;
        div.innerHTML = `
            <div class="avatar"><span class="material-icons-round">auto_awesome</span></div>
            <div class="content">
                <p>Thinking...</p>
            </div>
        `;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return div.id = 'loading-' + Date.now();
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
});
