class ChatBot {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.mediaRecorder;
        this.chunks = [];
        this.history = [];
        
        this.initUI();
        this.initWebSocket();
    }

    async initWebSocket() {
        this.ws = new WebSocket("ws://localhost:8000/ws");
        
        this.ws.onmessage = (event) => {
            this.playAudio(event.data);
            this.updateHistory('bot', new Blob([event.data]));
        };
    }

    async startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        
        this.mediaRecorder.ondataavailable = (e) => {
            this.chunks.push(e.data);
        };
        
        this.mediaRecorder.onstop = async () => {
            const blob = new Blob(this.chunks, { type: 'audio/wav' });
            this.ws.send(await blob.arrayBuffer());
            this.updateHistory('user', blob);
            this.chunks = [];
        };
        
        this.mediaRecorder.start();
    }

    playAudio(audioData) {
        const source = this.audioContext.createBufferSource();
        this.audioContext.decodeAudioData(audioData, (buffer) => {
            source.buffer = buffer;
            source.connect(this.audioContext.destination);
            source.start(0);
        });
    }

    updateHistory(role, content) {
        const historyElement = document.getElementById('chat-history');
        const entry = document.createElement('div');
        entry.className = `message ${role}`;
        entry.textContent = role === 'user' ? 'You: ' : 'Bot: ';
        
        if(content instanceof Blob) {
            const audioURL = URL.createObjectURL(content);
            const audioElement = new Audio(audioURL);
            entry.appendChild(audioElement);
        } else {
            entry.textContent += content;
        }
        
        historyElement.appendChild(entry);
    }
}
