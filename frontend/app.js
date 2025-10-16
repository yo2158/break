/**
 * BREAK - AI Debate Platform
 * Frontend JavaScript with API Integration
 */

// ============================================================================
// Utility Functions (from gui_mock_v2.html)
// ============================================================================

/**
 * Show toast notification.
 * Play error sound if type is 'error'.
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Play error sound for error notifications
    if (type === 'error') {
        playSound('error.mp3');
    }

    setTimeout(() => toast.classList.add('active'), 100);
    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Sound settings
let soundEnabled = true;

/**
 * Play sound effect.
 */
function playSound(filename) {
    if (!soundEnabled) return; // Skip if sound is disabled

    try {
        const audio = new Audio(`/sound/${filename}`);
        audio.volume = 0.8; // Set volume to 80%
        audio.play().catch(error => {
            console.warn(`Failed to play sound ${filename}:`, error);
        });
    } catch (error) {
        console.warn(`Error loading sound ${filename}:`, error);
    }
}

/**
 * Toggle sound on/off.
 */
function toggleSound() {
    soundEnabled = !soundEnabled;
    const soundIcon = document.getElementById('soundIcon');
    if (soundEnabled) {
        soundIcon.textContent = '🔊';
    } else {
        soundIcon.textContent = '🔇';
    }
}

// ============================================================================
// DOM Element References
// ============================================================================

const startButton = document.getElementById('startButton');
const topicInput = document.getElementById('topicInput');
const sections = document.querySelectorAll('.page-section');

// Cut-in overlays
const axisCutin = document.getElementById('axisCutin');
const axisDisplay = document.getElementById('axisDisplay');
const roundCutin = document.getElementById('roundCutin');
const roundCutinTitle = document.getElementById('roundCutinTitle');
const roundCutinSubtitle = document.getElementById('roundCutinSubtitle');
const objectionCutin = document.getElementById('objectionCutin');
const breakshotCutin = document.getElementById('breakshotCutin');
const judgmentCutin = document.getElementById('judgmentCutin');
const winnerCutin = document.getElementById('winnerCutin');
const winnerCutinText = document.getElementById('winnerCutinText');

// Loading indicator
const loadingIndicator = document.getElementById('loadingIndicator');
const loadingText = document.getElementById('loadingText');

// Round display control
let currentRoundWaitTimer = null;
let currentRoundSkipCallback = null;
let isWaitingForRound = false;

// Stop button
const stopButton = document.getElementById('stopButton');

// Fixed action buttons
const fullReportButton = document.getElementById('fullReportButton');
const copyButton = document.getElementById('copyButton');
const backToTop = document.getElementById('backToTop');

// Top control buttons
const historyButton = document.getElementById('historyButton');
const configButton = document.getElementById('configButton');
const apiButton = document.getElementById('apiButton');
const testButton = document.getElementById('testButton');

// Modals
const testModal = document.getElementById('testModal');
const testClose = document.getElementById('testClose');
const configModal = document.getElementById('configModal');
const configClose = document.getElementById('configClose');
const apiModal = document.getElementById('apiModal');
const apiClose = document.getElementById('apiClose');
const historyModal = document.getElementById('historyModal');
const historyClose = document.getElementById('historyClose');

// Font size control
const fontSizeSlider = document.getElementById('fontSizeSlider');

// ============================================================================
// Engine and Model Configuration (Task 25)
// ============================================================================

const ENGINE_OPTIONS = [
    { value: 'API_Gemini', label: 'Gemini API' },
    { value: 'API_OpenRouter', label: 'OpenRouter' },
    { value: 'API_Ollama', label: 'Ollama (Local)' },
    { value: 'ChatGPT', label: 'ChatGPT (Codex CLI)' },
    { value: 'Gemini', label: 'Gemini (GEMINI CLI)' },
    { value: 'Claude', label: 'Claude (Claude Code)' }
];

const MODEL_OPTIONS = {
    'API_Gemini': [
        { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
        { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
        { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' }
    ],
    'API_OpenRouter': [
        { value: 'openai/gpt-5', label: 'GPT-5' },
        { value: 'openai/gpt-5-nano', label: 'GPT-5 Nano' },
        { value: 'google/gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
        { value: 'deepseek/deepseek-chat-v3.1', label: 'DeepSeek V3.1' },
        { value: 'anthropic/claude-sonnet-4.5', label: 'Claude Sonnet 4.5' },
        { value: 'anthropic/claude-haiku-4.5', label: 'Claude Haiku 4.5' },
        { value: 'x-ai/grok-code-fast-1', label: 'Grok Code Fast' },
        { value: 'openai/gpt-oss-20b:free', label: 'GPT-OSS 20B (Free)' },
        { value: 'google/gemma-3-27b-it:free', label: 'Gemma 3 27B (Free)' }
    ],
    'API_Ollama': [
        { value: 'gemma3:12b', label: 'Gemma 3 12B' },
        { value: 'gemma3:27b', label: 'Gemma 3 27B' },
        { value: 'gpt-oss:latest', label: 'GPT-OSS Latest' }
    ],
    'Claude': [
        { value: 'claude-sonnet-4.5', label: 'Claude Sonnet 4.5 (Default)' }
    ],
    'Gemini': [
        { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (Default)' }
    ],
    'ChatGPT': [
        { value: 'gpt-5-codex', label: 'GPT-5 Codex (Default)' }
    ]
};

// Current configuration state
let currentConfig = {
    ai_a: { engine: 'API_Gemini', model: 'gemini-2.5-flash' },
    ai_b: { engine: 'API_Gemini', model: 'gemini-2.5-flash' },
    judge: { engine: 'API_Gemini', model: 'gemini-2.5-flash' }
};

/**
 * Get display name for engine/model combination.
 * For API engines, returns the model label (e.g., "GPT-5").
 * For CLI engines, returns the engine name (e.g., "Claude").
 */
function getDisplayName(engine, model) {
    // For CLI engines, return engine name
    if (engine === 'Claude' || engine === 'Gemini' || engine === 'ChatGPT') {
        return engine;
    }

    // For API engines, find the model label
    const models = MODEL_OPTIONS[engine] || [];
    const modelInfo = models.find(m => m.value === model);

    if (modelInfo) {
        // Return label, but remove "(Default)" suffix if present
        return modelInfo.label.replace(/\s*\(Default\)$/, '');
    }

    // Fallback to engine name
    return engine.replace('API_', '');
}

// Current debate data (for copy functionality)
let currentDebateData = null;

// Store Round 1 and Round 2 data for COPY function
let round1Data = null;
let round2Data = null;

// EventSource for debate SSE (global for stop functionality)
let currentEventSource = null;

// Session ID for ADVANCE flow control
let currentSid = null;
let debateCompleted = false; // Flag to prevent unnecessary ADVANCE requests after debate completion

// Pending payload buffers for phased waits
const pendingPayloads = {
    round2: null,
    judgment: null
};

// Resolver hooks injected by waitFor45SecondsWithEarlyExit
const waitPayloadResolvers = {
    round2: null,
    judgment: null
};

// New wait and loading control state variables
let nextRoundReady = false;        // Next round data received flag
let waitingFor45Seconds = false;   // 45-second wait in progress
let current45SecondTimer = null;   // 45-second timer reference
let current45SecondCountdown = null; // Countdown interval reference
let continueButtonHandler = null;  // CONTINUE button click handler reference
let currentWaitRemainingSeconds = 0; // Current remaining seconds in wait

// ============================================================================
// Configuration Management (Task 25, 26)
// ============================================================================

/**
 * Send ADVANCE signal to backend to proceed to next phase.
 */
async function advancePhase() {
    if (!currentSid) {
        console.warn('advancePhase: No currentSid available');
        return;
    }

    // Skip if debate already completed
    if (debateCompleted) {
        return;
    }

    try {
        const response = await fetch('/api/debate/advance', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ sid: currentSid })
        });

        if (!response.ok) {
            // 404 is expected when session is already cleaned up (normal completion)
            if (response.status === 404) {
                return; // Silently return, no error
            }

            // Other errors are unexpected
            const error = await response.json().catch(() => ({}));
            console.error('[ADVANCE] Unexpected error:', response.status, error);
        }
    } catch (e) {
        // Network errors or other exceptions
        console.warn('[ADVANCE] Request failed:', e.message);
    }
}

/**
 * Load configuration from backend API.
 */
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (!response.ok) throw new Error('Failed to load config');

        const config = await response.json();
        currentConfig = config;

        // Populate dropdowns
        populateEngineDropdowns();

    } catch (error) {
        console.error('Failed to load config:', error);
        showToast('Failed to load configuration', 'error');
    }
}

/**
 * Populate engine and model dropdowns.
 */
function populateEngineDropdowns() {
    const aiAEngine = document.getElementById('aiAEngine');
    const aiBEngine = document.getElementById('aiBEngine');
    const judgeEngine = document.getElementById('judgeEngine');

    // Set current engine values
    aiAEngine.value = currentConfig.ai_a.engine;
    aiBEngine.value = currentConfig.ai_b.engine;
    judgeEngine.value = currentConfig.judge.engine;

    // Update model dropdowns
    updateModelDropdown('aiA', currentConfig.ai_a.engine, currentConfig.ai_a.model);
    updateModelDropdown('aiB', currentConfig.ai_b.engine, currentConfig.ai_b.model);
    updateModelDropdown('judge', currentConfig.judge.engine, currentConfig.judge.model);
}

/**
 * Update model dropdown based on selected engine.
 */
function updateModelDropdown(role, engine, selectedModel = null) {
    const modelSelect = document.getElementById(`${role}Model`);
    const modelSection = document.getElementById(`${role}ModelSection`);

    // Get models for selected engine
    const models = MODEL_OPTIONS[engine] || [];

    // Hide model section for CLI engines with single model
    if (models.length === 1) {
        modelSection.style.display = 'none';
    } else {
        modelSection.style.display = 'flex';
    }

    // Clear and populate model dropdown
    modelSelect.innerHTML = '';
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.value;
        option.textContent = model.label;
        modelSelect.appendChild(option);
    });

    // Set selected model
    if (selectedModel) {
        modelSelect.value = selectedModel;
    } else if (models.length > 0) {
        modelSelect.value = models[0].value;
    }
}

/**
 * Save configuration to backend API.
 */
async function saveConfig() {
    try {
        const config = {
            ai_a: {
                engine: document.getElementById('aiAEngine').value,
                model: document.getElementById('aiAModel').value
            },
            ai_b: {
                engine: document.getElementById('aiBEngine').value,
                model: document.getElementById('aiBModel').value
            },
            judge: {
                engine: document.getElementById('judgeEngine').value,
                model: document.getElementById('judgeModel').value
            }
        };

        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) throw new Error('Failed to save config');

        currentConfig = config;
        showToast('Configuration saved successfully', 'success');
        configModal.classList.remove('show');

    } catch (error) {
        console.error('Failed to save config:', error);
        showToast('Failed to save configuration', 'error');
    }
}

/**
 * Test connection to AI engines with countdown and progressive updates (Task 26).
 */
async function testConnection() {
    const testResults = document.getElementById('testResults');
    const resultAiA = document.getElementById('testResultAiA');
    const resultAiB = document.getElementById('testResultAiB');
    const resultJudge = document.getElementById('testResultJudge');

    testResults.style.display = 'block';

    // Start countdown timers for each engine
    const countdownIntervals = {
        ai_a: null,
        ai_b: null,
        judge: null
    };

    const startCountdown = (elementId, role) => {
        let remaining = 30;
        const element = document.getElementById(elementId);

        const updateDisplay = () => {
            element.innerHTML = `<div style="font-family: monospace; font-size: 0.85rem; color: #ffa500;">Testing... ${remaining}s</div>`;
        };

        updateDisplay();
        countdownIntervals[role] = setInterval(() => {
            remaining--;
            if (remaining >= 0) {
                updateDisplay();
            }
        }, 1000);
    };

    const stopCountdown = (role) => {
        if (countdownIntervals[role]) {
            clearInterval(countdownIntervals[role]);
            countdownIntervals[role] = null;
        }
    };

    const testSingleEngine = async (engine, model, role, resultElement) => {
        try {
            const response = await fetch('/api/test-engine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ engine, model })
            });

            if (!response.ok) throw new Error('Engine test failed');

            const result = await response.json();

            stopCountdown(role);
            resultElement.innerHTML = formatTestResult(result);

        } catch (error) {
            console.error(`Test error for ${role}:`, error);

            stopCountdown(role);
            resultElement.innerHTML = `
                <div style="font-family: monospace; font-size: 0.85rem;">
                    <div style="color: #ff3333;">✗ ERROR</div>
                    <div style="color: #d0d0d0;">${error.message}</div>
                </div>
            `;
        }
    };

    // Start all countdowns
    startCountdown('testResultAiA', 'ai_a');
    startCountdown('testResultAiB', 'ai_b');
    startCountdown('testResultJudge', 'judge');

    // Execute tests in parallel, but each updates individually when complete
    Promise.all([
        testSingleEngine(currentConfig.ai_a.engine, currentConfig.ai_a.model, 'ai_a', resultAiA),
        testSingleEngine(currentConfig.ai_b.engine, currentConfig.ai_b.model, 'ai_b', resultAiB),
        testSingleEngine(currentConfig.judge.engine, currentConfig.judge.model, 'judge', resultJudge)
    ]);
}

/**
 * Load environment variables and mask API keys (MAGIN-style).
 */
async function loadEnv() {
    try {
        const response = await fetch('/api/env');
        if (!response.ok) throw new Error('Failed to load env');

        const env = await response.json();

        // Display masked keys (show ●●●●●●●● if key exists)
        const geminiInput = document.getElementById('geminiApiKey');
        const openrouterInput = document.getElementById('openrouterApiKey');
        const ollamaInput = document.getElementById('ollamaUrl');

        // Mask Gemini API key if exists
        if (env.GEMINI_API_KEY === true) {
            geminiInput.value = '●●●●●●●●';
            geminiInput.dataset.hasKey = 'true';
        } else {
            geminiInput.value = '';
            geminiInput.dataset.hasKey = 'false';
        }

        // Mask OpenRouter API key if exists
        if (env.OPENROUTER_API_KEY === true) {
            openrouterInput.value = '●●●●●●●●';
            openrouterInput.dataset.hasKey = 'true';
        } else {
            openrouterInput.value = '';
            openrouterInput.dataset.hasKey = 'false';
        }

        // Ollama URL is always shown
        if (env.OLLAMA_URL) {
            ollamaInput.value = env.OLLAMA_URL;
        }

    } catch (error) {
        console.error('Failed to load env:', error);
        showToast('Failed to load API settings', 'error');
    }
}

/**
 * Format test result for display.
 */
function formatTestResult(result) {
    const color = result.success ? '#00ff00' : '#ff3333';
    const icon = result.success ? '✓' : '✗';
    const status = result.success ? 'SUCCESS' : 'FAILED';

    let html = `
        <div style="font-family: monospace; font-size: 0.85rem;">
            <div style="color: ${color}; margin-bottom: 5px;">${icon} ${status}</div>
            <div style="color: #d0d0d0;">Engine: ${result.engine}</div>
            <div style="color: #d0d0d0;">Model: ${result.model}</div>
    `;

    if (result.success) {
        html += `<div style="color: #d0d0d0;">Response time: ${result.elapsed.toFixed(2)}s</div>`;
    } else if (result.error) {
        html += `<div style="color: #ff3333;">Error: ${result.error}</div>`;
    }

    html += '</div>';
    return html;
}

// ============================================================================
// Debate Execution with SSE (Task 27)
// ============================================================================

/**
 * Reset UI to initial state (used by both stopDebate and error handlers).
 */
function resetToInitialState() {
    // Reset session ID
    currentSid = null;
    // Hide all cut-ins
    axisCutin.classList.remove('show');
    axisDisplay.classList.remove('show');
    document.getElementById('axisReasoning').classList.remove('show');
    roundCutin.classList.remove('show');
    objectionCutin.classList.remove('show');
    breakshotCutin.classList.remove('show');
    judgmentCutin.classList.remove('show');
    winnerCutin.classList.remove('show');

    // Hide loading indicator
    hideLoadingIndicator();

    // Clear round wait timer if exists
    if (currentRoundWaitTimer) {
        clearTimeout(currentRoundWaitTimer);
        currentRoundWaitTimer = null;
    }
    if (currentRoundSkipCallback) {
        currentRoundSkipCallback = null;
    }
    isWaitingForRound = false;

    // Remove skip button if exists
    const skipButton = document.getElementById('roundSkipButton');
    if (skipButton) {
        skipButton.remove();
    }

    // Clear new wait system state
    nextRoundReady = false;
    waitingFor45Seconds = false;
    if (current45SecondTimer) {
        clearTimeout(current45SecondTimer);
        current45SecondTimer = null;
    }
    if (current45SecondCountdown) {
        clearInterval(current45SecondCountdown);
        current45SecondCountdown = null;
    }
    if (continueButtonHandler) {
        continueButtonHandler = null;
    }

    // Hide all sections
    document.getElementById('round1').classList.remove('visible');
    document.getElementById('round2').classList.remove('visible');
    document.getElementById('judgment').classList.remove('visible');
    document.getElementById('analyzing').classList.remove('visible');
    document.getElementById('analyzing').classList.add('hidden');
    document.getElementById('topicHeader').classList.remove('visible');

    // Show hero section
    document.getElementById('hero').classList.remove('hidden');
    document.getElementById('hero').classList.add('visible');

    // Hide stop button
    stopButton.classList.remove('show');

    // Hide copy and back to top buttons
    fullReportButton.classList.remove('show');
    copyButton.classList.remove('show');
    backToTop.classList.remove('show');

    // Reset stored debate data
    round1Data = null;
    round2Data = null;
    currentDebateData = null;
}

/**
 * Stop the current debate and reset UI to initial state.
 */
function stopDebate() {
    // Close EventSource connection
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }

    resetToInitialState();
    showToast('Debate stopped', 'info');
}

/**
 * Start debate with EventSource SSE.
 */
async function startDebate() {
    const topic = topicInput.value.trim();

    if (!topic || topic.length < 10) {
        showToast('Please enter a topic (at least 10 characters)', 'error');
        return;
    }

    // Reset previous debate display (Issue #6)
    document.getElementById('round1').classList.remove('visible');
    document.getElementById('round2').classList.remove('visible');
    document.getElementById('judgment').classList.remove('visible');

    // Reset animation states
    const scoreValues = document.querySelectorAll('.score-value');
    scoreValues.forEach(elem => elem.classList.remove('show'));
    document.getElementById('breakshotSection').classList.remove('show');
    document.getElementById('winnerAnnouncement').classList.remove('show');
    document.getElementById('reasoningText').classList.remove('show');
    document.getElementById('synthesisText').classList.remove('show');

    // Hide copy and back to top buttons
    fullReportButton.classList.remove('show');
    copyButton.classList.remove('show');
    backToTop.classList.remove('show');

    // Clear stored debate data
    round1Data = null;
    round2Data = null;
    currentDebateData = null;

    // Show topic header
    document.getElementById('topicHeaderText').textContent = topic;
    document.getElementById('topicHeader').classList.add('visible');

    // Hide hero section, show analyzing section
    document.getElementById('hero').classList.remove('visible');
    document.getElementById('hero').classList.add('hidden');
    // Remove hidden class first, then add visible
    document.getElementById('analyzing').classList.remove('hidden');
    document.getElementById('analyzing').classList.add('visible');

    // Show stop button
    stopButton.classList.add('show');

    // Play start sound
    playSound('start.mp3');

    // Reset session ID and completion flag for new debate run
    currentSid = null;
    debateCompleted = false;
    pendingPayloads.round2 = null;
    pendingPayloads.judgment = null;
    waitPayloadResolvers.round2 = null;
    waitPayloadResolvers.judgment = null;

    try {
        // Create EventSource for SSE
        currentEventSource = new EventSource(`/api/debate?topic=${encodeURIComponent(topic)}&config=${encodeURIComponent(JSON.stringify(currentConfig))}`);

        currentEventSource.onmessage = async (event) => {
            try {
                const data = JSON.parse(event.data);

                // Capture sid from first event
                if (data.sid) {
                    currentSid = data.sid;
                }

                switch (data.type) {
                    case 'axis':
                        await handleAxisEvent(data.data);
                        break;
                    case 'round1':
                        // Round1 data arrived - always handle immediately (not waiting for Round1)
                        await handleRound1Event(data.data);
                        break;
                    case 'round2':
                        pendingPayloads.round2 = data.data;
                        if (waitPayloadResolvers.round2) {
                            waitPayloadResolvers.round2(data.data);
                        }
                        break;
                    case 'judgment':
                        pendingPayloads.judgment = data.data;
                        if (waitPayloadResolvers.judgment) {
                            waitPayloadResolvers.judgment(data.data);
                        }
                        break;
                    case 'complete':
                        handleCompleteEvent(data.data);
                        currentEventSource.close();
                        currentEventSource = null;
                        break;
                    case 'error':
                        handleErrorEvent(data.data);
                        currentEventSource.close();
                        currentEventSource = null;
                        break;
                }
            } catch (error) {
                console.error('Failed to parse event data:', error);
                showToast('Data parsing error. Resetting...', 'error');
                // Reset to initial state on JSON error
                if (currentEventSource) {
                    currentEventSource.close();
                    currentEventSource = null;
                }
                resetToInitialState();
            }
        };

        currentEventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            showToast('Connection error. Resetting...', 'error');
            if (currentEventSource) {
                currentEventSource.close();
                currentEventSource = null;
            }
            resetToInitialState();
        };

    } catch (error) {
        console.error('Failed to start debate:', error);
        showToast('Failed to start debate', 'error');
        stopButton.classList.remove('show');
    }
}

// ============================================================================
// Event Handlers (Task 28, 29)
// ============================================================================

/**
 * Handle axis determination event.
 * Issue #3 & #4: Keep axis display visible while loading Round1, use axis_reasoning field
 */
async function handleAxisEvent(data) {
    // Hide analyzing section
    document.getElementById('analyzing').classList.remove('visible');
    document.getElementById('analyzing').classList.add('hidden');

    // Update top controls position (fix to top when not on hero)
    updateTopControlsPosition();

    // Show axis cut-in
    document.getElementById('axisLeft').textContent = `${data.axis_left}[${getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)}]`;
    document.getElementById('axisRight').textContent = `${data.axis_right}[${getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model)}]`;

    // Set reasoning text - use axis_reasoning field
    const axisReasoningElem = document.getElementById('axisReasoning');
    axisReasoningElem.textContent = data.axis_reasoning || '';

    axisCutin.classList.add('show');

    // Show axis display after announcement
    setTimeout(() => {
        axisDisplay.classList.add('show');
    }, 500);

    // Show reasoning after axis display
    setTimeout(() => {
        axisReasoningElem.classList.add('show');
    }, 1300);

    // Play determined sound with slight delay
    setTimeout(() => {
        playSound('determined.mp3');
    }, 1500);

    // Issue #4: DO NOT close cut-in - keep it visible during Round1 loading
    // The cut-in will be closed when Round1 data arrives
    // NEW: Remove 4500ms wait - proceed immediately to loading

    // Show loading indicator (bottom-right) while keeping axis display visible
    // NO countdown for axis screen - just show loading
    showLoadingIndicator('Preparing Round 1 arguments...');
}

/**
 * Handle Round 1 event.
 * Issue #4: Close axis cut-in when Round1 data arrives
 */
async function handleRound1Event(data) {
    // Store Round 1 data for COPY function
    round1Data = data;

    // Hide loading indicator
    hideLoadingIndicator();

    // Issue #4: Close axis cut-in now that Round1 is ready
    axisCutin.classList.remove('show');
    axisDisplay.classList.remove('show');
    document.getElementById('axisReasoning').classList.remove('show');

    // Hide analyzing section
    document.getElementById('analyzing').classList.remove('visible');
    document.getElementById('analyzing').classList.add('hidden');

    // Play round1 sound
    playSound('round1.mp3');

    // Show Round 1 cut-in
    roundCutinTitle.textContent = 'ROUND 1';
    roundCutinSubtitle.textContent = 'Opening Arguments';
    roundCutin.classList.add('show');
    await sleep(1500);
    roundCutin.classList.remove('show');

    // Show Round 1 section
    document.getElementById('round1').classList.add('visible');

    // Display Round 1 arguments
    displayRound1(data);

    // Scroll to Round 1
    await sleep(500);
    scrollToSection('round1');

    // NEW SYSTEM: Wait 45 seconds with early exit when Round2 ready
    const round2Payload = await waitFor45SecondsWithEarlyExit('round2');

    if (round2Payload) {
        await handleRound2Event(round2Payload);
    }
}

/**
 * Handle Round 2 event.
 */
async function handleRound2Event(data) {
    // Store Round 2 data for COPY function
    round2Data = data;

    // Hide loading indicator
    hideLoadingIndicator();

    // Play round2 sound (objection cut-in)
    playSound('round2.mp3');

    // Show objection cut-in
    objectionCutin.classList.add('show');
    await sleep(1500);
    objectionCutin.classList.remove('show');

    // Show Round 2 cut-in
    roundCutinTitle.textContent = 'ROUND 2';
    roundCutinSubtitle.textContent = 'Counter Arguments';
    roundCutin.classList.add('show');
    await sleep(1500);
    roundCutin.classList.remove('show');

    // Show Round 2 section
    document.getElementById('round2').classList.add('visible');

    // Display Round 2 arguments
    displayRound2(data);

    // Scroll to Round 2 section (Task 32)
    await sleep(500);
    scrollToSection('round2');

    // NEW SYSTEM: Wait 45 seconds with early exit when Judgment ready
    const judgmentPayload = await waitFor45SecondsWithEarlyExit('judgment');

    if (judgmentPayload) {
        await handleJudgmentEvent(judgmentPayload);
    }
}

/**
 * Handle judgment event.
 */
async function handleJudgmentEvent(data) {
    // Hide loading indicator first
    hideLoadingIndicator();

    // Play final sound
    playSound('final.mp3');

    // 1. Show FINAL JUDGMENT cut-in
    judgmentCutin.classList.add('show');
    await sleep(2500);
    judgmentCutin.classList.remove('show');

    // 2. Show judgment section
    document.getElementById('judgment').classList.add('visible');

    // 3. Display judgment data
    displayJudgment(data);

    // 4. Scroll to judgment section
    await sleep(500);
    scrollToSection('judgment');

    // 5. Animate scores
    await sleep(1000);
    await animateScoresWithCutins(data);

    // 6. Show copy and back to top buttons
    fullReportButton.classList.add('show');
    copyButton.classList.add('show');
    backToTop.classList.add('show');

    // Hide stop button after judgment is complete
    stopButton.classList.remove('show');
}

/**
 * Animate scores with BREAKSHOT and WINNER cut-ins.
 */
async function animateScoresWithCutins(data) {
    // Animate score values
    const scoreValues = document.querySelectorAll('.score-value');
    scoreValues.forEach((elem, index) => {
        setTimeout(() => {
            elem.classList.add('show');
        }, index * 200);
    });

    // Wait for score animation + 500ms
    await sleep(scoreValues.length * 200 + 500);

    // Play breakshot sound with slight delay before cut-in
    setTimeout(() => {
        playSound('breakshot.mp3');
    }, 200);

    // Show BREAKSHOT cut-in - use axis[engine] format
    const breakshotCutinStance = data.break_shot.ai === 'AI_A' ? data.axis_left : data.axis_right;
    const breakshotCutinModel = data.break_shot.ai === 'AI_A' ? currentConfig.ai_a.model : currentConfig.ai_b.model;
    const breakshotCutinEngine = data.break_shot.ai === 'AI_A' ? currentConfig.ai_a.engine : currentConfig.ai_b.engine;
    const breakshotCutinDisplayName = getDisplayName(breakshotCutinEngine, breakshotCutinModel);
    const breakshotText = `${breakshotCutinStance}[${breakshotCutinDisplayName}] / ${data.break_shot.category.toUpperCase()} : ${data.break_shot.score}/10`;
    document.getElementById('breakshotEval').textContent = breakshotText;
    document.getElementById('breakshotQuote').textContent = `「${data.break_shot.quote}」`;
    breakshotCutin.classList.add('show');
    await sleep(4500);
    breakshotCutin.classList.remove('show');

    // Show BREAKSHOT section in page
    await sleep(1100);
    document.getElementById('breakshotSection').classList.add('show');

    // Show WINNER cut-in with laser effect
    await sleep(900);
    winnerCutin.classList.add('show');
    winnerCutinText.style.display = 'block';
    winnerCutinText.innerHTML = 'WINNER......';

    // After 2s, add lightning flash and show winner
    await sleep(2000);
    winnerCutin.style.animation = 'screenFlash 0.15s ease-in-out 3';

    await sleep(450);
    const winnerCutinStance = data.winner === 'AI_A' ? data.axis_left : data.axis_right;
    const winnerCutinDisplayName = data.winner === 'AI_A'
        ? getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)
        : getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model);

    // Play winner sound when displaying winner name
    playSound('winner.mp3');

    winnerCutinText.innerHTML = `WINNER......<br><div style="font-size: 1.2em; color: var(--primary-color); text-shadow: 0 0 80px var(--primary-color), 0 0 120px var(--primary-color); margin-top: 20px; animation: dramaticZoom 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;">${winnerCutinStance}<br>[${winnerCutinDisplayName}]</div>`;

    // Close winner cut-in after 3.5s more
    await sleep(3500);
    winnerCutin.classList.remove('show');
    winnerCutin.style.animation = '';

    // Show WINNER announcement in page
    document.getElementById('winnerAnnouncement').classList.add('show');

    // Show REASONING first
    await sleep(900);
    document.getElementById('reasoningText').classList.add('show');

    // Show SYNTHESIS after REASONING
    await sleep(700);
    document.getElementById('synthesisText').classList.add('show');

    // Restore hero section BEFORE scrolling to prevent page height change after scroll
    await sleep(300);
    document.getElementById('hero').classList.remove('hidden');
    document.getElementById('hero').classList.add('visible');
    topicInput.value = '';  // Clear previous topic

    // Issue #6: Scroll to bottom after hero is restored (prevents scroll position jump)
    await sleep(200);
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

/**
 * Handle complete event.
 */
function handleCompleteEvent(data) {
    showToast('Debate completed successfully', 'success');
    // Hide stop button
    stopButton.classList.remove('show');
    // Mark debate as completed to prevent further ADVANCE requests
    debateCompleted = true;
}

/**
 * Handle error event.
 */
function handleErrorEvent(data) {
    console.error('Debate error:', data.message);

    // Check if it's a NOT_APPLICABLE error (topic not suitable for debate)
    if (data.message && data.message.includes('NOT_APPLICABLE')) {
        // Show specific message for invalid topic
        showToast('このトピックは議論に適していません。別の議論可能なテーマを入力してください。', 'error');
    } else {
        showToast(`Error: ${data.message}`, 'error');
    }

    // Mark debate as completed (even on error) to prevent further ADVANCE requests
    debateCompleted = true;

    // Reset to initial state
    resetToInitialState();
}

// ============================================================================
// Display Functions (Task 28, 29)
// ============================================================================

/**
 * Display Round 1 loading state with axis information.
 */
function displayRound1Loading(axisLeft, axisRight) {
    // Use axis[engine] format instead of AI_A/AI_B
    document.getElementById('round1NameA').textContent = `${axisLeft}[${getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)}]`;
    const badgeA = document.getElementById('round1BadgeA');
    badgeA.className = 'confidence-badge';
    badgeA.innerHTML = '<span style="color: #888;">⏳ PREPARING...</span>';
    document.getElementById('round1ArgumentA').innerHTML = `
        <div style="text-align: center; padding: 40px; color: #888;">
            <div style="font-size: 1.2rem; margin-bottom: 10px;">⏳</div>
            <div>Preparing opening arguments...</div>
        </div>
    `;

    document.getElementById('round1NameB').textContent = `${axisRight}[${getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model)}]`;
    const badgeB = document.getElementById('round1BadgeB');
    badgeB.className = 'confidence-badge';
    badgeB.innerHTML = '<span style="color: #888;">⏳ PREPARING...</span>';
    document.getElementById('round1ArgumentB').innerHTML = `
        <div style="text-align: center; padding: 40px; color: #888;">
            <div style="font-size: 1.2rem; margin-bottom: 10px;">⏳</div>
            <div>Preparing opening arguments...</div>
        </div>
    `;
}

/**
 * Display Round 1 arguments.
 */
function displayRound1(data) {
    // Safety checks for data structure
    if (!data || !data.ai_a || !data.ai_b) {
        console.error('Invalid Round1 data structure:', data);
        showToast('Failed to display Round 1 data', 'error');
        return;
    }

    // Use axis[engine] format instead of AI_A/AI_B
    document.getElementById('round1NameA').textContent = `${data.axis_left || 'N/A'}[${getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)}]`;
    updateConfidenceBadge('round1BadgeA', data.ai_a.confidence_level);

    const rationaleA = Array.isArray(data.ai_a.rationale)
        ? data.ai_a.rationale.map(r => `<div class="rationale-item">${processCriticalTags(r, 1)}</div>`).join('')
        : '<div class="rationale-item">N/A</div>';

    const argA = `
        <div class="argument-section">
            <div class="argument-header">CLAIM</div>
            <div class="argument-claim">${processCriticalTags(data.ai_a.claim || 'N/A', 1)}</div>
        </div>
        <div class="argument-section">
            <div class="argument-header">PREEMPTIVE COUNTER</div>
            <div class="argument-claim">${processCriticalTags(data.ai_a.preemptive_counter || 'N/A', 1)}</div>
        </div>
        <div class="argument-section">
            <div class="argument-header">RATIONALE</div>
            ${rationaleA}
        </div>
    `;
    document.getElementById('round1ArgumentA').innerHTML = argA;

    document.getElementById('round1NameB').textContent = `${data.axis_right || 'N/A'}[${getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model)}]`;
    updateConfidenceBadge('round1BadgeB', data.ai_b.confidence_level);

    const rationaleB = Array.isArray(data.ai_b.rationale)
        ? data.ai_b.rationale.map(r => `<div class="rationale-item">${processCriticalTags(r, 1)}</div>`).join('')
        : '<div class="rationale-item">N/A</div>';

    const argB = `
        <div class="argument-section">
            <div class="argument-header">CLAIM</div>
            <div class="argument-claim">${processCriticalTags(data.ai_b.claim || 'N/A', 1)}</div>
        </div>
        <div class="argument-section">
            <div class="argument-header">PREEMPTIVE COUNTER</div>
            <div class="argument-claim">${processCriticalTags(data.ai_b.preemptive_counter || 'N/A', 1)}</div>
        </div>
        <div class="argument-section">
            <div class="argument-header">RATIONALE</div>
            ${rationaleB}
        </div>
    `;
    document.getElementById('round1ArgumentB').innerHTML = argB;
}

/**
 * Display Round 2 arguments.
 */
function displayRound2(data) {
    // Safety checks for data structure
    if (!data || !data.ai_a || !data.ai_b) {
        console.error('Invalid Round2 data structure:', data);
        showToast('Failed to display Round 2 data', 'error');
        return;
    }

    // Use axis[engine] format instead of AI_A/AI_B
    document.getElementById('round2NameA').textContent = `${data.axis_left || 'N/A'}[${getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)}]`;
    updateConfidenceBadge('round2BadgeA', data.ai_a.confidence_level);

    const countersA = Array.isArray(data.ai_a.counters)
        ? data.ai_a.counters.map(c => `<div class="rationale-item">${processCriticalTags(c, 2)}</div>`).join('')
        : '<div class="rationale-item">N/A</div>';

    const argA = `
        <div class="argument-section">
            <div class="argument-header">COUNTER ARGUMENTS</div>
            ${countersA}
        </div>
        <div class="argument-section">
            <div class="argument-header">FINAL STATEMENT</div>
            <div class="argument-claim">${processCriticalTags(data.ai_a.final_statement || 'N/A', 2)}</div>
        </div>
    `;
    document.getElementById('round2ArgumentA').innerHTML = argA;

    document.getElementById('round2NameB').textContent = `${data.axis_right || 'N/A'}[${getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model)}]`;
    updateConfidenceBadge('round2BadgeB', data.ai_b.confidence_level);

    const countersB = Array.isArray(data.ai_b.counters)
        ? data.ai_b.counters.map(c => `<div class="rationale-item">${processCriticalTags(c, 2)}</div>`).join('')
        : '<div class="rationale-item">N/A</div>';

    const argB = `
        <div class="argument-section">
            <div class="argument-header">COUNTER ARGUMENTS</div>
            ${countersB}
        </div>
        <div class="argument-section">
            <div class="argument-header">FINAL STATEMENT</div>
            <div class="argument-claim">${processCriticalTags(data.ai_b.final_statement || 'N/A', 2)}</div>
        </div>
    `;
    document.getElementById('round2ArgumentB').innerHTML = argB;
}

/**
 * Display judgment results.
 */
function displayJudgment(data) {
    // Update score table with axis[engine] format instead of AI_A/AI_B
    document.getElementById('scoreLabelA').textContent = `${data.axis_left}[${getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)}]`;
    document.getElementById('scoreALogic').textContent = `${data.scores.ai_a.logic}/10`;
    document.getElementById('scoreAAttack').textContent = `${data.scores.ai_a.attack}/10`;
    document.getElementById('scoreAConstruct').textContent = `${data.scores.ai_a.construct}/10`;
    document.getElementById('scoreATotal').textContent = `${data.scores.ai_a.total}/30`;

    document.getElementById('scoreLabelB').textContent = `${data.axis_right}[${getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model)}]`;
    document.getElementById('scoreBLogic').textContent = `${data.scores.ai_b.logic}/10`;
    document.getElementById('scoreBAttack').textContent = `${data.scores.ai_b.attack}/10`;
    document.getElementById('scoreBConstruct').textContent = `${data.scores.ai_b.construct}/10`;
    document.getElementById('scoreBTotal').textContent = `${data.scores.ai_b.total}/30`;

    // Prepare break shot data (will be animated later) - use axis[engine] format
    const breakshotStance = data.break_shot.ai === 'AI_A' ? data.axis_left : data.axis_right;
    const breakshotDisplayName = data.break_shot.ai === 'AI_A'
        ? getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)
        : getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model);
    document.getElementById('breakshotTitle').textContent =
        `${breakshotStance}[${breakshotDisplayName}] / ${data.break_shot.category} : ${data.break_shot.score}/10`;
    document.getElementById('breakshotQuoteText').textContent = data.break_shot.quote;

    // Prepare winner announcement (will be shown later) - use axis[model] format (single line)
    const winnerStance = data.winner === 'AI_A' ? data.axis_left : data.axis_right;
    const winnerDisplayName = data.winner === 'AI_A'
        ? getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model)
        : getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model);
    document.getElementById('winnerAnnouncement').textContent =
        `WINNER: ${winnerStance}[${winnerDisplayName}]`;

    // Prepare reasoning and synthesis (will be shown later)
    document.getElementById('reasoningText').textContent = data.reasoning || '';
    document.getElementById('synthesisText').textContent = data.synthesis;

    // Store debate data for copy function
    currentDebateData = {
        topic: topicInput.value,
        ...data
    };
}

/**
 * Update confidence badge.
 * Issue #9: Only show badge when confidence_level is explicitly provided
 */
function updateConfidenceBadge(badgeId, confidenceLevel) {
    const badge = document.getElementById(badgeId);

    // Only show badge if confidence_level is explicitly provided
    if (confidenceLevel === 'high') {
        badge.className = 'confidence-badge valid';
        badge.innerHTML = '<span class="icon">💎</span><span>VALID</span>';
        badge.style.display = 'inline-flex';
    } else if (confidenceLevel === 'low') {
        badge.className = 'confidence-badge unstable';
        badge.innerHTML = '<span class="icon">⚠️</span><span>UNSTABLE</span>';
        badge.style.display = 'inline-flex';
    } else {
        // Hide badge if confidence_level not provided
        badge.style.display = 'none';
    }
}

/**
 * Show loading indicator with optional countdown.
 */
function showLoadingIndicator(text, countdown = null) {
    if (countdown) {
        let remaining = countdown;
        const baseText = text;

        const updateText = () => {
            loadingText.textContent = `${baseText} (${remaining}s)`;
        };

        updateText();

        const countdownInterval = setInterval(() => {
            remaining--;
            if (remaining >= 0) {
                updateText();
            } else {
                clearInterval(countdownInterval);
            }
        }, 1000);

        // Store interval for cleanup
        loadingIndicator.dataset.countdownInterval = countdownInterval;
    } else {
        loadingText.textContent = text;
    }

    loadingIndicator.classList.add('show');
}

/**
 * Hide loading indicator.
 */
function hideLoadingIndicator() {
    // Clear countdown interval if exists
    if (loadingIndicator.dataset.countdownInterval) {
        clearInterval(parseInt(loadingIndicator.dataset.countdownInterval));
        delete loadingIndicator.dataset.countdownInterval;
    }

    loadingIndicator.classList.remove('show');
}

/**
 * Get loading text for next event type.
 */
function getLoadingText(nextEventType) {
    switch (nextEventType) {
        case 'round2': return 'Preparing counter arguments...';
        case 'judgment': return 'Analyzing debate and calculating scores...';
        case 'round1': return 'Preparing Round 1 arguments...';
        default: return 'Loading...';
    }
}

/**
 * Convert loading indicator to CONTINUE button when next round is ready.
 */
function convertLoadingToContinueButton(nextEventType) {
    // Use global currentWaitRemainingSeconds instead of parsing text
    const remainingSeconds = currentWaitRemainingSeconds;

    // Clear countdown interval
    if (loadingIndicator.dataset.countdownInterval) {
        clearInterval(parseInt(loadingIndicator.dataset.countdownInterval));
        delete loadingIndicator.dataset.countdownInterval;
    }

    // Clear any existing countdown update interval
    if (current45SecondCountdown) {
        clearInterval(current45SecondCountdown);
        current45SecondCountdown = null;
    }

    // Get appropriate text based on next event type (matching existing UI style)
    const continueText = nextEventType === 'round2' ? 'Ready to continue to Round 2' : 'Ready to continue to Judgment';

    // Change loading text to CONTINUE button with remaining seconds
    if (remainingSeconds > 0) {
        loadingText.innerHTML = `<span style="cursor: pointer; color: var(--primary-color); text-decoration: underline;">${continueText} (${remainingSeconds}s)</span>`;

        // Continue countdown for CONTINUE button
        current45SecondCountdown = setInterval(() => {
            currentWaitRemainingSeconds--;
            if (currentWaitRemainingSeconds > 0) {
                loadingText.innerHTML = `<span style="cursor: pointer; color: var(--primary-color); text-decoration: underline;">${continueText} (${currentWaitRemainingSeconds}s)</span>`;
            } else {
                clearInterval(current45SecondCountdown);
                current45SecondCountdown = null;
                loadingText.innerHTML = `<span style="cursor: pointer; color: var(--primary-color); text-decoration: underline;">Click to continue</span>`;
            }
        }, 1000);
    } else {
        loadingText.innerHTML = `<span style="cursor: pointer; color: var(--primary-color); text-decoration: underline;">Click to continue</span>`;
    }

    // Make indicator clickable
    loadingIndicator.style.cursor = 'pointer';

    // Store handler reference for cleanup
    continueButtonHandler = () => {
        if (nextRoundReady && window._currentWaitResolve) {
            // Call the resolve function with fromButton=true to allow immediate proceed
            window._currentWaitResolve(true);
        }
    };

    loadingIndicator.addEventListener('click', continueButtonHandler);
}

/**
 * Wait for 45 seconds with early exit when next round data is ready.
 * Shows loading indicator with countdown, converts to CONTINUE button when ready.
 * Progression condition: Data ready AND (45 seconds elapsed OR CONTINUE clicked)
 */
async function waitFor45SecondsWithEarlyExit(nextEventType) {
    return new Promise((resolve) => {
        nextRoundReady = false;
        waitingFor45Seconds = true;
        currentWaitRemainingSeconds = 45;

        let gateResolved = false;
        let payloadResolved = false;
        let payloadData = null;
        let advanceRequested = false;

        const typeKey = nextEventType === 'round2' ? 'round2' : 'judgment';

        const loadingTextContent = getLoadingText(nextEventType);
        const waitForDataMessage = `${loadingTextContent} (waiting for data...)`;

        // Initialize loading indicator and countdown
        loadingText.textContent = `${loadingTextContent} (${currentWaitRemainingSeconds}s)`;
        loadingIndicator.classList.add('show');

        current45SecondCountdown = setInterval(() => {
            currentWaitRemainingSeconds--;
            if (currentWaitRemainingSeconds >= 0 && !payloadResolved) {
                loadingText.textContent = `${loadingTextContent} (${currentWaitRemainingSeconds}s)`;
            } else if (currentWaitRemainingSeconds < 0) {
                clearInterval(current45SecondCountdown);
                current45SecondCountdown = null;
            }
        }, 1000);

        const showWaitingForData = () => {
            loadingText.textContent = waitForDataMessage;
            loadingIndicator.style.cursor = 'default';
            if (current45SecondCountdown) {
                clearInterval(current45SecondCountdown);
                current45SecondCountdown = null;
            }
            if (continueButtonHandler) {
                loadingIndicator.removeEventListener('click', continueButtonHandler);
                continueButtonHandler = null;
            }
        };

        const settleIfReady = () => {
            if (gateResolved && payloadResolved) {
                const data = payloadData;
                cleanup();
                resolve(data);
            }
        };

        const handlePayload = (payload) => {
            if (!payload || payloadResolved) {
                return;
            }

            payloadResolved = true;
            payloadData = payload;
            nextRoundReady = true;

            pendingPayloads[typeKey] = null;

            if (!gateResolved) {
                convertLoadingToContinueButton(nextEventType);
            } else {
                showWaitingForData();
            }

            settleIfReady();
        };

        waitPayloadResolvers[typeKey] = handlePayload;

        if (pendingPayloads[typeKey]) {
            handlePayload(pendingPayloads[typeKey]);
        }

        const requestAdvanceIfNeeded = () => {
            if (!advanceRequested) {
                advanceRequested = true;
                advancePhase();
            }
        };

        window._currentWaitResolve = (fromButton = false) => {
            if (fromButton && !payloadResolved) {
                showWaitingForData();
            }

            requestAdvanceIfNeeded();

            if (!gateResolved) {
                gateResolved = true;
            }

            settleIfReady();
        };

        current45SecondTimer = setTimeout(() => {
            if (window._currentWaitResolve) {
                showWaitingForData();
                window._currentWaitResolve(false);
            }
        }, 45000);

        function cleanup() {
            waitingFor45Seconds = false;
            nextRoundReady = false;
            gateResolved = false;
            payloadResolved = false;
            payloadData = null;
            advanceRequested = false;
            currentWaitRemainingSeconds = 0;

            if (current45SecondTimer) {
                clearTimeout(current45SecondTimer);
                current45SecondTimer = null;
            }
            if (current45SecondCountdown) {
                clearInterval(current45SecondCountdown);
                current45SecondCountdown = null;
            }

            if (continueButtonHandler) {
                loadingIndicator.removeEventListener('click', continueButtonHandler);
                continueButtonHandler = null;
            }

            loadingIndicator.style.cursor = '';

            window._currentWaitResolve = null;
            waitPayloadResolvers[typeKey] = null;
            pendingPayloads[typeKey] = null;

            hideLoadingIndicator();
        }
    });
}

/**
 * OLD SYSTEM - DEPRECATED - Keeping for reference but not used anymore.
 * Wait for a specified duration with skip button support.
 * Returns early if skip button is clicked.
 */
async function waitWithSkip_DEPRECATED(durationMs, skipButtonText = 'SKIP') {
    return new Promise((resolve) => {
        isWaitingForRound = true;
        let remainingSeconds = Math.ceil(durationMs / 1000);

        // Create skip button
        const skipButton = document.createElement('button');
        skipButton.id = 'roundSkipButton';
        skipButton.className = 'round-skip-button';
        skipButton.innerHTML = `${skipButtonText} (${remainingSeconds}s)`;
        skipButton.style.display = 'none'; // Initially hidden
        document.body.appendChild(skipButton);

        // Update countdown
        const countdownInterval = setInterval(() => {
            remainingSeconds--;
            if (remainingSeconds >= 0) {
                skipButton.innerHTML = `${skipButtonText} (${remainingSeconds}s)`;
            } else {
                clearInterval(countdownInterval);
            }
        }, 1000);

        // Timer to auto-resolve after duration
        const timer = setTimeout(() => {
            cleanup();
            resolve();
        }, durationMs);

        // Skip button click handler
        const skipHandler = () => {
            cleanup();
            resolve();
        };

        skipButton.addEventListener('click', skipHandler);

        // Store for external access
        currentRoundWaitTimer = timer;
        currentRoundSkipCallback = () => {
            cleanup();
            resolve();
        };

        const cleanup = () => {
            isWaitingForRound = false;
            clearTimeout(timer);
            clearInterval(countdownInterval);
            currentRoundWaitTimer = null;
            currentRoundSkipCallback = null;
            skipButton.remove();
        };

        // Show skip button after a short delay (to avoid accidental clicks)
        setTimeout(() => {
            if (isWaitingForRound) {
                skipButton.style.display = 'flex';
            }
        }, 2000);
    });
}

/**
 * Truncate text to maximum length with ellipsis.
 */
function truncate(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 1) + '…';
}

/**
 * Copy debate summary to clipboard (1000 character limit).
 */
async function copyDebateToClipboard() {
    if (!currentDebateData) {
        showToast('No debate data available', 'error');
        return;
    }

    const data = currentDebateData;

    // Get Round 1 and Round 2 text from stored data (remove critical tags)
    const round1A = removeCriticalTags(round1Data?.ai_a?.claim || '');
    const round1B = removeCriticalTags(round1Data?.ai_b?.claim || '');
    const round2A = removeCriticalTags(round2Data?.ai_a?.final_statement || '');
    const round2B = removeCriticalTags(round2Data?.ai_b?.final_statement || '');

    // Get display names
    const aiADisplayName = getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model);
    const aiBDisplayName = getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model);

    // Format according to requirements (use REASONING instead of SYNTHESIS, axis[engine] format)
    const winnerStance = data.winner === 'AI_A' ? data.axis_left : data.axis_right;
    const winnerDisplayName = data.winner === 'AI_A' ? aiADisplayName : aiBDisplayName;
    const breakshotStance = data.break_shot.ai === 'AI_A' ? data.axis_left : data.axis_right;
    const breakshotDisplayName = data.break_shot.ai === 'AI_A' ? aiADisplayName : aiBDisplayName;

    // Character limits (will be truncated to 1000 if exceeded)
    const LIMITS = {
        topic: 45,
        axisLeft: 25,
        axisRight: 25,
        aiADisplayName: 25,
        aiBDisplayName: 25,
        winnerStance: 15,
        winnerDisplayName: 15,
        round1A: 150,
        round1B: 150,
        round2A: 150,
        round2B: 150,
        breakshotStance: 15,
        breakshotDisplayName: 25,
        breakshotCategory: 25,
        breakshotQuote: 120,
        reasoning: 160
    };

    // Build summary with character limits (new format: ROUND 1\nA: ... instead of ROUND 1 A: ...)
    const summary = `TOPIC: ${truncate(data.topic, LIMITS.topic)}
AXIS: A:${truncate(data.axis_left, LIMITS.axisLeft)}[${truncate(aiADisplayName, LIMITS.aiADisplayName)}] ⚔ B:${truncate(data.axis_right, LIMITS.axisRight)}[${truncate(aiBDisplayName, LIMITS.aiBDisplayName)}]
FINAL RESULT: WIN${truncate(winnerStance, LIMITS.winnerStance)}[${truncate(winnerDisplayName, LIMITS.winnerDisplayName)}] / A:${data.scores.ai_a.total} vs B:${data.scores.ai_b.total}
ROUND 1
A: ${truncate(round1A, LIMITS.round1A)}
B: ${truncate(round1B, LIMITS.round1B)}
ROUND 2
A: ${truncate(round2A, LIMITS.round2A)}
B: ${truncate(round2B, LIMITS.round2B)}

BREAK SHOT: ${truncate(breakshotStance, LIMITS.breakshotStance)}[${truncate(breakshotDisplayName, LIMITS.breakshotDisplayName)}]:${truncate(data.break_shot.category, LIMITS.breakshotCategory)}「${truncate(data.break_shot.quote, LIMITS.breakshotQuote)}」
REASONING: ${truncate(data.reasoning || '', LIMITS.reasoning)}`;

    // Final check: ensure <= 1000 characters
    let finalSummary = summary;
    if (finalSummary.length > 1000) {
        finalSummary = finalSummary.substring(0, 997) + '...';
    }

    try {
        // Check if Clipboard API is available (requires HTTPS or localhost)
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(finalSummary);
            showToast(`Copied (${finalSummary.length}/1000 chars)`, 'success');
        } else {
            // Fallback for non-HTTPS environments
            const textArea = document.createElement('textarea');
            textArea.value = finalSummary;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast(`Copied (${finalSummary.length}/1000 chars)`, 'success');
        }
    } catch (error) {
        console.error('Failed to copy:', error);
        showToast('Failed to copy to clipboard', 'error');
    }
}

/**
 * Copy full debate report in Markdown format to clipboard.
 */
async function copyFullReportToClipboard() {
    if (!currentDebateData || !round1Data || !round2Data) {
        showToast('No complete debate data available', 'error');
        return;
    }

    const data = currentDebateData;

    // Helper function to format rationale/counters as bullet list
    const formatList = (items) => {
        if (!Array.isArray(items)) return 'N/A';
        return items.map((item, index) => `${index + 1}. ${removeCriticalTags(item)}`).join('\n');
    };

    // Get display names
    const aiADisplayName = getDisplayName(currentConfig.ai_a.engine, currentConfig.ai_a.model);
    const aiBDisplayName = getDisplayName(currentConfig.ai_b.engine, currentConfig.ai_b.model);
    const judgeDisplayName = getDisplayName(currentConfig.judge.engine, currentConfig.judge.model);

    // Determine winner
    const winnerStance = data.winner === 'AI_A' ? data.axis_left : data.axis_right;
    const winnerDisplayName = data.winner === 'AI_A' ? aiADisplayName : aiBDisplayName;

    // Determine break shot
    const breakshotStance = data.break_shot.ai === 'AI_A' ? data.axis_left : data.axis_right;
    const breakshotDisplayName = data.break_shot.ai === 'AI_A' ? aiADisplayName : aiBDisplayName;

    const fullReport = `## Topic
${data.topic}

## Debate Axis
- **Left (AI_A)**: ${data.axis_left}
- **Right (AI_B)**: ${data.axis_right}
- **Reasoning**: ${data.axis_reasoning || 'N/A'}

## AI Configuration
- **AI_A**: ${currentConfig.ai_a.engine} / ${currentConfig.ai_a.model} (Display: ${aiADisplayName})
- **AI_B**: ${currentConfig.ai_b.engine} / ${currentConfig.ai_b.model} (Display: ${aiBDisplayName})
- **Judge**: ${currentConfig.judge.engine} / ${currentConfig.judge.model} (Display: ${judgeDisplayName})

---

## Round 1: Opening Arguments

### ${data.axis_left} [${aiADisplayName}]
${round1Data.ai_a.confidence_level ? `**Confidence Level**: ${round1Data.ai_a.confidence_level}\n\n` : ''}**Claim**:
${removeCriticalTags(round1Data.ai_a.claim || 'N/A')}

**Rationale**:
${formatList(round1Data.ai_a.rationale)}

**Preemptive Counter**:
${removeCriticalTags(round1Data.ai_a.preemptive_counter || 'N/A')}

---

### ${data.axis_right} [${aiBDisplayName}]
${round1Data.ai_b.confidence_level ? `**Confidence Level**: ${round1Data.ai_b.confidence_level}\n\n` : ''}**Claim**:
${removeCriticalTags(round1Data.ai_b.claim || 'N/A')}

**Rationale**:
${formatList(round1Data.ai_b.rationale)}

**Preemptive Counter**:
${removeCriticalTags(round1Data.ai_b.preemptive_counter || 'N/A')}

---

## Round 2: Counter Arguments

### ${data.axis_left} [${aiADisplayName}]
${round2Data.ai_a.confidence_level ? `**Confidence Level**: ${round2Data.ai_a.confidence_level}\n\n` : ''}**Counter Arguments**:
${formatList(round2Data.ai_a.counters)}

**Final Statement**:
${removeCriticalTags(round2Data.ai_a.final_statement || 'N/A')}

---

### ${data.axis_right} [${aiBDisplayName}]
${round2Data.ai_b.confidence_level ? `**Confidence Level**: ${round2Data.ai_b.confidence_level}\n\n` : ''}**Counter Arguments**:
${formatList(round2Data.ai_b.counters)}

**Final Statement**:
${removeCriticalTags(round2Data.ai_b.final_statement || 'N/A')}

---

## Final Judgment

### Scores
| Debater | Logic | Attack | Construct | Total |
|---------|-------|--------|-----------|-------|
| ${data.axis_left} [${aiADisplayName}] | ${data.scores.ai_a.logic}/10 | ${data.scores.ai_a.attack}/10 | ${data.scores.ai_a.construct}/10 | **${data.scores.ai_a.total}/30** |
| ${data.axis_right} [${aiBDisplayName}] | ${data.scores.ai_b.logic}/10 | ${data.scores.ai_b.attack}/10 | ${data.scores.ai_b.construct}/10 | **${data.scores.ai_b.total}/30** |

### Winner
**${winnerStance} [${winnerDisplayName}]**

Score Difference: +${Math.abs(data.scores.ai_a.total - data.scores.ai_b.total)}

### Break Shot
**${breakshotStance} [${breakshotDisplayName}]** / ${data.break_shot.category} : ${data.break_shot.score}/10

> 「${data.break_shot.quote}」

### Reasoning
${data.reasoning || 'N/A'}

### Synthesis
${data.synthesis || 'N/A'}
`;

    try {
        // Check if Clipboard API is available (requires HTTPS or localhost)
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(fullReport);
            showToast('Full report copied to clipboard (Markdown)', 'success');
        } else {
            // Fallback for non-HTTPS environments
            const textArea = document.createElement('textarea');
            textArea.value = fullReport;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('Full report copied to clipboard (Markdown)', 'success');
        }
    } catch (error) {
        console.error('Failed to copy full report:', error);
        showToast('Failed to copy to clipboard', 'error');
    }
}

/**
 * Sleep utility function.
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Convert <critical> tags to HTML spans with appropriate classes.
 * Round 1: claim-core class
 * Round 2: counter-critical class
 */
function processCriticalTags(text, roundNum) {
    if (!text) return text;

    const className = roundNum === 1 ? 'claim-core' : 'counter-critical';
    return text.replace(
        /<critical>(.*?)<\/critical>/g,
        `<span class="critical-phrase ${className}">$1</span>`
    );
}

/**
 * Remove <critical> tags from text (for COPY functionality).
 */
function removeCriticalTags(text) {
    if (!text) return text;
    return text.replace(/<critical>(.*?)<\/critical>/g, '$1');
}

/**
 * Scroll to section with smooth behavior.
 * Issue #5: Scroll past title AND subtitle to show content fully.
 */
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;

    const sectionRect = section.getBoundingClientRect();
    const sectionTop = window.scrollY + sectionRect.top;

    // Find the debate content container (debate-grid or scoreboard-container)
    // We want these to be at the top, hiding the title/subtitle above them
    const contentElement = section.querySelector('.debate-grid, .scoreboard-container');

    let contentOffset = 0;
    if (contentElement) {
        const contentRect = contentElement.getBoundingClientRect();
        contentOffset = contentRect.top - sectionRect.top;
    }

    // Small padding to show the content clearly (positive value to keep some spacing from viewport top)
    const viewportOffset = 20; // Show content 20px from top of viewport

    const scrollToPosition = sectionTop + contentOffset - viewportOffset;

    window.scrollTo({
        top: scrollToPosition,
        behavior: 'smooth'
    });
}

// ============================================================================
// History Modal (Task 30-32)
// ============================================================================

// History state
let historyState = {
    items: [],
    total: 0,
    offset: 0,
    limit: 50,
    loading: false,
    hasMore: true
};

// Track currently shown round in history detail (0 = none, 1 = round1, 2 = round2)
let currentHistoryRound = 0;

/**
 * Open history modal and load initial data (Task 30a).
 */
async function openHistoryModal() {
    // Reset state
    historyState = {
        items: [],
        total: 0,
        offset: 0,
        limit: 100,
        loading: false,
        hasMore: true
    };

    // Show modal
    historyModal.classList.add('show');

    // Show list view, hide detail view
    document.getElementById('historyList').classList.add('show');
    document.getElementById('historyDetail').classList.remove('show');

    // Load first page
    await loadHistoryPage();
}

/**
 * Load history page from API (Task 30a, 31).
 */
async function loadHistoryPage() {
    if (historyState.loading || !historyState.hasMore) return;

    historyState.loading = true;

    try {
        const response = await fetch(`/api/history?limit=${historyState.limit}&offset=${historyState.offset}`);
        if (!response.ok) throw new Error('Failed to load history');

        const data = await response.json();

        historyState.total = data.total;
        historyState.items = data.items.slice(0, historyState.limit);
        historyState.offset = historyState.items.length;
        historyState.hasMore = false;

        renderHistoryList();

    } catch (error) {
        console.error('Failed to load history:', error);
        showToast('Failed to load debate history', 'error');
    } finally {
        historyState.loading = false;
    }
}

/**
 * Render history list (Task 30a).
 */
function renderHistoryList() {
    const listContainer = document.getElementById('historyListItems');

    // Clear if first page
    if (historyState.offset === historyState.items.length) {
        listContainer.innerHTML = '';
    }

    // Check if empty
    if (historyState.items.length === 0) {
        listContainer.innerHTML = '<div class="history-item" style="text-align: center; color: #888;">No debate history found</div>';
        return;
    }

    // Render items
    historyState.items.forEach(item => {
        // Skip if already rendered
        if (document.getElementById(`history-item-${item.id}`)) return;

        const itemDiv = document.createElement('div');
        itemDiv.id = `history-item-${item.id}`;
        itemDiv.className = 'history-item';
        itemDiv.style.cursor = 'pointer';

        // Format date - explicitly use JST timezone
        const date = new Date(item.created_at);
        const dateStr = date.toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Asia/Tokyo'
        });

        // Parse axis (stored as JSON string in database)
        let axisLeft = 'AI_A';
        let axisRight = 'AI_B';
        try {
            if (item.axis) {
                const axisData = typeof item.axis === 'string' ? JSON.parse(item.axis) : item.axis;
                axisLeft = axisData.left || axisLeft;
                axisRight = axisData.right || axisRight;
            }
        } catch (e) {
            console.warn('Failed to parse axis:', e);
        }

        // Convert winner from AI_A/AI_B to axis[model] format
        const winnerStance = item.winner === 'AI_A' ? axisLeft : axisRight;
        const winnerDisplayName = item.winner === 'AI_A'
            ? getDisplayName(item.ai_a_engine, item.ai_a_model)
            : getDisplayName(item.ai_b_engine, item.ai_b_model);

        const aiADisplayName = getDisplayName(item.ai_a_engine, item.ai_a_model);
        const aiBDisplayName = getDisplayName(item.ai_b_engine, item.ai_b_model);

        itemDiv.innerHTML = `
            <div class="history-date">${dateStr}　${item.topic}</div>
            <div class="history-axis">
                ${axisLeft}[${aiADisplayName || 'N/A'}] vs ${axisRight}[${aiBDisplayName || 'N/A'}] / WINNER: ${winnerStance}[${winnerDisplayName || 'N/A'}]
            </div>
        `;

        // Add click handler
        itemDiv.addEventListener('click', () => showHistoryDetail(item.id));

        listContainer.appendChild(itemDiv);
    });

    // Update pagination info
    const paginationInfo = document.getElementById('historyPaginationInfo');
    if (paginationInfo) {
        const totalShown = Math.min(historyState.items.length, historyState.limit);
        const totalAvailable = Math.min(historyState.total, historyState.limit);
        paginationInfo.textContent = `Showing ${totalShown} of ${totalAvailable} debates`;
    }
}

/**
 * Close history modal (Task 30a).
 */
function closeHistoryModal() {
    historyModal.classList.remove('show');

    // Hide both views
    document.getElementById('historyList').classList.remove('show');
    document.getElementById('historyDetail').classList.remove('show');
}

/**
 * Show history detail view (Task 30b).
 */
async function showHistoryDetail(debateId) {
    try {
        const response = await fetch(`/api/history/${debateId}`);
        if (!response.ok) throw new Error('Failed to load debate detail');

        const data = await response.json();

        // Hide list, show detail
        document.getElementById('historyList').classList.remove('show');
        document.getElementById('historyDetail').classList.add('show');

        // Render detail
        renderHistoryDetail(data);

    } catch (error) {
        console.error('Failed to load debate detail:', error);
        showToast('Failed to load debate detail', 'error');
    }
}

/**
 * Show history list view (Task 30b).
 */
function showHistoryList() {
    document.getElementById('historyDetail').classList.remove('show');
    document.getElementById('historyList').classList.add('show');
}

/**
 * Toggle round display in history detail (モック準拠).
 */
function showHistoryRound(roundNum) {
    // Toggle behavior: clicking same round hides it
    if (currentHistoryRound === roundNum) {
        // Hide current round
        const contents = document.querySelectorAll('#historyDetail .round-content');
        contents.forEach(content => content.classList.remove('active'));

        const tabs = document.querySelectorAll('#historyDetail .round-tab');
        tabs.forEach(tab => tab.classList.remove('active'));

        currentHistoryRound = 0;
        return;
    }

    // Show selected round
    currentHistoryRound = roundNum;

    // Update tabs
    const tabs = document.querySelectorAll('#historyDetail .round-tab');
    tabs.forEach((tab, index) => {
        if (index + 1 === roundNum) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update content
    const contents = document.querySelectorAll('#historyDetail .round-content');
    contents.forEach((content, index) => {
        if (index + 1 === roundNum) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

/**
 * Render history detail view (Task 30b).
 */
function renderHistoryDetail(data) {
    // Parse JSON fields with safety checks
    let axis, round1, round2, scores, breakShot;

    try {
        axis = typeof data.axis === 'string' ? JSON.parse(data.axis) : (data.axis || {});
        round1 = typeof data.round1_data === 'string' ? JSON.parse(data.round1_data) : (data.round1_data || {});
        round2 = typeof data.round2_data === 'string' ? JSON.parse(data.round2_data) : (data.round2_data || {});
        scores = typeof data.scores === 'string' ? JSON.parse(data.scores) : (data.scores || {});
        breakShot = typeof data.break_shot === 'string' ? JSON.parse(data.break_shot) : (data.break_shot || {});
    } catch (e) {
        console.error('Failed to parse history detail data:', e);
        showToast('Failed to parse debate history', 'error');
        return;
    }

    // Set defaults if parsing failed
    axis = axis || {};
    axis.left = axis.left || 'N/A';
    axis.right = axis.right || 'N/A';
    round1 = round1 || { ai_a: {}, ai_b: {} };
    round2 = round2 || { ai_a: {}, ai_b: {} };
    scores = scores || { ai_a: {}, ai_b: {} };
    breakShot = breakShot || {};

    // Update back button
    const backButton = document.querySelector('.history-detail-back');
    backButton.onclick = showHistoryList;

    // Update close button
    const detailCloseBtn = document.querySelector('#historyDetail .history-close');
    if (detailCloseBtn) {
        detailCloseBtn.onclick = showHistoryList;
    }

    // Reset round toggle state (hide all rounds initially)
    currentHistoryRound = 0;
    const allRoundContents = document.querySelectorAll('#historyDetail .round-content');
    allRoundContents.forEach(content => content.classList.remove('active'));
    const allRoundTabs = document.querySelectorAll('#historyDetail .round-tab');
    allRoundTabs.forEach(tab => tab.classList.remove('active'));

    // Add event listeners to round tabs
    const round1Tab = document.getElementById('round1Tab');
    const round2Tab = document.getElementById('round2Tab');
    if (round1Tab) {
        round1Tab.onclick = () => showHistoryRound(1);
    }
    if (round2Tab) {
        round2Tab.onclick = () => showHistoryRound(2);
    }

    // Topic section
    document.getElementById('historyDetailTopic').textContent = data.topic;

    // Axis section
    const detailAiADisplayName = getDisplayName(data.ai_a_engine, data.ai_a_model);
    const detailAiBDisplayName = getDisplayName(data.ai_b_engine, data.ai_b_model);
    document.getElementById('historyDetailAxis').textContent =
        `${axis.left}[${detailAiADisplayName || 'N/A'}] ⚔️ ${axis.right}[${detailAiBDisplayName || 'N/A'}]`;

    // Round 1 section
    const round1Container = document.getElementById('historyDetailRound1');
    const rationaleA = Array.isArray(round1.ai_a?.rationale)
        ? round1.ai_a.rationale.map((r, i) => `${i + 1}. ${r}`).join('<br>')
        : 'N/A';
    const rationaleB = Array.isArray(round1.ai_b?.rationale)
        ? round1.ai_b.rationale.map((r, i) => `${i + 1}. ${r}`).join('<br>')
        : 'N/A';

    round1Container.innerHTML = `
        <div class="debater-argument">
            <div class="debater-name">${axis.left}[${detailAiADisplayName || 'N/A'}]</div>
            <div class="history-detail-text">
                <strong>CLAIM:</strong> ${round1.ai_a?.claim || 'N/A'}<br><br>
                <strong>RATIONALE:</strong><br>
                ${rationaleA}<br><br>
                <strong>PREEMPTIVE COUNTER:</strong> ${round1.ai_a?.preemptive_counter || 'N/A'}
            </div>
        </div>
        <div class="debater-argument">
            <div class="debater-name">${axis.right}[${detailAiBDisplayName || 'N/A'}]</div>
            <div class="history-detail-text">
                <strong>CLAIM:</strong> ${round1.ai_b?.claim || 'N/A'}<br><br>
                <strong>RATIONALE:</strong><br>
                ${rationaleB}<br><br>
                <strong>PREEMPTIVE COUNTER:</strong> ${round1.ai_b?.preemptive_counter || 'N/A'}
            </div>
        </div>
    `;

    // Round 2 section
    const round2Container = document.getElementById('historyDetailRound2');
    const countersA = Array.isArray(round2.ai_a?.counters)
        ? round2.ai_a.counters.map((c, i) => `${i + 1}. ${c}`).join('<br>')
        : 'N/A';
    const countersB = Array.isArray(round2.ai_b?.counters)
        ? round2.ai_b.counters.map((c, i) => `${i + 1}. ${c}`).join('<br>')
        : 'N/A';

    round2Container.innerHTML = `
        <div class="debater-argument">
            <div class="debater-name">${axis.left}[${detailAiADisplayName || 'N/A'}]</div>
            <div class="history-detail-text">
                <strong>COUNTER ARGUMENTS:</strong><br>
                ${countersA}<br><br>
                <strong>FINAL STATEMENT:</strong> ${round2.ai_a?.final_statement || 'N/A'}
            </div>
        </div>
        <div class="debater-argument">
            <div class="debater-name">${axis.right}[${detailAiBDisplayName || 'N/A'}]</div>
            <div class="history-detail-text">
                <strong>COUNTER ARGUMENTS:</strong><br>
                ${countersB}<br><br>
                <strong>FINAL STATEMENT:</strong> ${round2.ai_b?.final_statement || 'N/A'}
            </div>
        </div>
    `;

    // Final result section - use axis[model] format
    const scoreDiff = Math.abs((scores.ai_a?.total || 0) - (scores.ai_b?.total || 0));
    const histWinnerStance = data.winner === 'AI_A' ? axis.left : axis.right;
    const histWinnerDisplayName = data.winner === 'AI_A' ? detailAiADisplayName : detailAiBDisplayName;
    document.getElementById('historyDetailResult').innerHTML = `
        <strong>WINNER: ${histWinnerStance}[${histWinnerDisplayName || 'N/A'}] (+${scoreDiff})</strong><br>
        ${axis.left}[${detailAiADisplayName || 'N/A'}]: LOGIC[${scores.ai_a?.logic || 0}/10] ATTACK[${scores.ai_a?.attack || 0}/10] CONSTRUCT[${scores.ai_a?.construct || 0}/10] = ${scores.ai_a?.total || 0}/30<br>
        ${axis.right}[${detailAiBDisplayName || 'N/A'}]: LOGIC[${scores.ai_b?.logic || 0}/10] ATTACK[${scores.ai_b?.attack || 0}/10] CONSTRUCT[${scores.ai_b?.construct || 0}/10] = ${scores.ai_b?.total || 0}/30
    `;

    // Break shot section - use axis[model] format
    const histBreakshotStance = breakShot.ai === 'AI_A' ? axis.left : axis.right;
    const histBreakshotDisplayName = breakShot.ai === 'AI_A' ? detailAiADisplayName : detailAiBDisplayName;
    document.getElementById('historyDetailBreakShot').innerHTML = `
        ${histBreakshotStance}[${histBreakshotDisplayName || 'N/A'}] / ${breakShot.category || 'N/A'} : ${breakShot.score || 0}/10<br>
        「${breakShot.quote || 'N/A'}」
    `;

    // Reasoning section
    document.getElementById('historyDetailReasoning').textContent = data.reasoning || 'N/A';

    // Synthesis section
    document.getElementById('historyDetailSynthesis').textContent = data.synthesis || 'N/A';
}

// ============================================================================
// UI Event Listeners
// ============================================================================

// Font size control
fontSizeSlider.addEventListener('input', (e) => {
    const size = e.target.value;
    document.documentElement.style.setProperty('--argument-font-size', `${size}rem`);
});

// Back to top button (Task 32)
backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Scroll visibility control (Task 32)
window.addEventListener('scroll', () => {
    const round1Section = document.getElementById('round1');
    if (round1Section && round1Section.classList.contains('visible')) {
        const round1Top = round1Section.offsetTop;
        if (window.scrollY > round1Top) {
            backToTop.classList.add('show');
        } else {
            backToTop.classList.remove('show');
        }
    }
});

// Top controls fixed positioning control
// When hero section is not visible, fix the top controls to the top of the screen
function updateTopControlsPosition() {
    const heroSection = document.getElementById('hero');
    const topControls = document.querySelector('.top-controls');

    if (!heroSection || !topControls) return;

    // If hero is not visible, fix the controls to the top
    if (!heroSection.classList.contains('visible')) {
        topControls.classList.add('fixed');
    } else {
        topControls.classList.remove('fixed');
    }
}

// Full report button
fullReportButton.addEventListener('click', copyFullReportToClipboard);

// Copy button
copyButton.addEventListener('click', copyDebateToClipboard);

// Start debate button
startButton.addEventListener('click', startDebate);

// Ctrl+Enter keyboard shortcut for debate start
topicInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        startDebate();
    }
});

// Stop button
stopButton.addEventListener('click', stopDebate);

// ESC key to stop debate or reset to initial state
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        e.preventDefault();
        if (currentEventSource) {
            // If debate is running, stop it
            stopDebate();
        } else {
            // If no debate is running but UI is stuck, reset to initial state
            const analyzing = document.getElementById('analyzing');
            const hero = document.getElementById('hero');
            if (!hero.classList.contains('visible') || analyzing.classList.contains('visible')) {
                resetToInitialState();
                showToast('Reset to initial state', 'info');
            }
        }
    }
});

// Test modal
testButton.addEventListener('click', () => {
    testModal.classList.add('show');
});
testClose.addEventListener('click', () => {
    testModal.classList.remove('show');
});
testModal.addEventListener('click', (e) => {
    if (e.target === testModal) {
        testModal.classList.remove('show');
    }
});
document.getElementById('runTestButton').addEventListener('click', testConnection);

// Config modal
configButton.addEventListener('click', () => {
    configModal.classList.add('show');
});
configClose.addEventListener('click', () => {
    configModal.classList.remove('show');
});
configModal.addEventListener('click', (e) => {
    if (e.target === configModal) {
        configModal.classList.remove('show');
    }
});
document.getElementById('saveConfigButton').addEventListener('click', saveConfig);

// Engine change handlers
document.getElementById('aiAEngine').addEventListener('change', (e) => {
    updateModelDropdown('aiA', e.target.value);
});
document.getElementById('aiBEngine').addEventListener('change', (e) => {
    updateModelDropdown('aiB', e.target.value);
});
document.getElementById('judgeEngine').addEventListener('change', (e) => {
    updateModelDropdown('judge', e.target.value);
});

// API modal
apiButton.addEventListener('click', async () => {
    await loadEnv();  // Load and mask API keys
    apiModal.classList.add('show');
});
apiClose.addEventListener('click', () => {
    apiModal.classList.remove('show');
});
apiModal.addEventListener('click', (e) => {
    if (e.target === apiModal) {
        apiModal.classList.remove('show');
    }
});
document.getElementById('saveApiButton').addEventListener('click', async () => {
    // Get input values
    const geminiInput = document.getElementById('geminiApiKey');
    const openrouterInput = document.getElementById('openrouterApiKey');
    const ollamaInput = document.getElementById('ollamaUrl');

    // Build request body (only include changed values)
    const requestBody = {};

    // Check if masked keys were changed
    if (!(geminiInput.dataset.hasKey === 'true' && geminiInput.value === '●●●●●●●●')) {
        requestBody.GEMINI_API_KEY = geminiInput.value;
    }

    if (!(openrouterInput.dataset.hasKey === 'true' && openrouterInput.value === '●●●●●●●●')) {
        requestBody.OPENROUTER_API_KEY = openrouterInput.value;
    }

    // Always include Ollama URL
    requestBody.OLLAMA_URL = ollamaInput.value;

    try {
        const response = await fetch('/api/env', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error('Failed to save API settings');
        }

        showToast('API settings saved successfully', 'success');
        apiModal.classList.remove('show');
    } catch (error) {
        console.error('Failed to save API settings:', error);
        showToast('Failed to save API settings', 'error');
    }
});

// History modal (Task 30a, 31)
historyButton.addEventListener('click', openHistoryModal);
historyClose.addEventListener('click', closeHistoryModal);
historyModal.addEventListener('click', (e) => {
    if (e.target === historyModal) {
        closeHistoryModal();
    }
});

// Sound toggle button
const soundToggle = document.getElementById('soundToggle');
if (soundToggle) {
    soundToggle.addEventListener('click', toggleSound);
}

// ============================================================================
// Initialization
// ============================================================================

// Load configuration on page load
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
});
