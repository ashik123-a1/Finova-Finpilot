/**
 * SME Finance Copilot Site-Wide Persistent Hands-Free Voice Assistant Controller ("Hi Ashik")
 * Adapted from LandGuard architecture for Autonomous SME Financial Participant Operations.
 * 
 * Features:
 * 1. Singleton controller running across ALL authenticated and public pages.
 * 2. Preserves active hands-free state in sessionStorage ('sme_voice_hands_free').
 * 3. Automatic speech recognition reinitialization upon destination page load.
 * 4. Multilingual wake words: "Hi Ashik" / "হাই আশিক" / "Hello Copilot".
 * 5. Strict stop phrase detection: "Stop Ashik" / "Stop Copilot" / "স্টপ আশিক" / "停止".
 * 6. Synthesized Web Audio feedback chimes (activate, reply, stop).
 * 7. Verified cross-page navigation routing and real-time TTS voice responses.
 */

(function (window, document) {
    'use strict';

    // Prevent duplicate initialization
    if (window.SMEVoiceController) {
        return;
    }

    const STORAGE_KEY = 'sme_voice_hands_free';

    const STATE = {
        HANDS_FREE_OFF: 'HANDS_FREE_OFF',
        WAKE_WORD_STANDBY: 'WAKE_WORD_STANDBY',
        COMMAND_LISTENING: 'COMMAND_LISTENING',
        PROCESSING: 'PROCESSING',
        SPEAKING: 'SPEAKING',
        ERROR: 'ERROR'
    };

    // Wake words: English, Bengali, Chinese - specifically optimized for "Hi Ashik"
    const WAKE_WORD_REGEX = /(?:^|[^\p{L}\p{N}])(?:(?:hell?o+|hallo|hey|hi|hai|high|হ্যালো|হেলো|হাই|হে|你好|喂)[\s,.:;!?-]+)?(?:ashik|ashique|ashiq|asik|আশিক|আসীক|阿希克|copilot|co-pilot|assistant|কপিলট|সহকারী|智能助手|助手)(?:$|[^\p{L}\p{N}])/iu;
    
    // Stop phrases: English, Bengali, Chinese
    const STOP_COPILOT_REGEX = /(?:^|[^\p{L}\p{N}])(?:(?:stop|shut\s+down|deactivate|exit|bye|goodbye|স্টপ|বন্ধ\s*করো?|থামো|停止|关闭|退出)[\s,.:;!?-]+(?:ashik|ashique|ashiq|asik|আশিক|copilot|co-pilot|assistant|কপিলট|সহকারী|智能助手|助手)|(?:ashik|ashique|ashiq|asik|আশিক|copilot|co-pilot|assistant|কপিলট|সহকারী|智能助手|助手)[\s,.:;!?-]+(?:stop|বন্ধ|থামো|বন্ধ\s*করো?|停止|关闭)|turn\s+off\s+hands\s*free|disable\s+hands\s*free|হ্যান্ডস\s*ফ্রি\s*বন্ধ|关闭免提)(?:$|[^\p{L}\p{N}])/iu;

    /* =========================================================
       1. CONTROLLER STATE
       ========================================================= */
    function getSiteLanguage() {
        try {
            if (typeof document !== 'undefined' && document.documentElement) {
                const htmlLang = document.documentElement.lang;
                if (htmlLang === 'bn' || htmlLang === 'zh' || htmlLang === 'en') return htmlLang;
            }
            if (typeof document !== 'undefined' && document.cookie) {
                const match = document.cookie.match(/(?:^|;\s*)sme_lang=(bn|zh|en)(?:;|$)/);
                if (match && match[1]) return match[1];
            }
        } catch (e) {}
        return 'en';
    }

    let handsFreeActive = false;
    let isSessionActivated = false;
    let currentState = STATE.HANDS_FREE_OFF;
    let currentLanguage = 'auto'; // 'auto', 'en', 'bn', 'zh'
    let autoSpeechLang = (getSiteLanguage() === 'bn') ? 'bn-BD' : (getSiteLanguage() === 'zh' ? 'zh-CN' : 'en-US');

    let wakeRecognition = null;
    let isStartingSpotter = false;
    let isSpotterPausedForTTS = false;
    let lastSpotterStartTime = 0;
    let consecutiveRestartCount = 0;
    let spotterRestartTimer = null;

    let audioCtx = null;
    let currentUtterance = null;
    let lastSpokenText = '';
    const stateChangeListeners = [];

    /* =========================================================
       2. SESSION STORAGE PERSISTENCE
       ========================================================= */
    function loadSession() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function saveSession(data) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch (e) {}
    }

    function clearSession() {
        try {
            sessionStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
    }

    /* =========================================================
       3. SYNTHESIZED WEB AUDIO CHIMES
       ========================================================= */
    function initAudioContext() {
        if (!audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                audioCtx = new AudioContext();
            }
        }
        if (audioCtx && audioCtx.state === 'suspended') {
            audioCtx.resume().catch(() => {});
        }
    }

    function playChime(type) {
        try {
            initAudioContext();
            if (!audioCtx) return;
            const now = audioCtx.currentTime;

            if (type === 'activate') {
                // High-tech ascending futuristic chime
                const osc1 = audioCtx.createOscillator();
                const gain1 = audioCtx.createGain();
                osc1.type = 'sine';
                osc1.frequency.setValueAtTime(440, now);
                osc1.frequency.exponentialRampToValueAtTime(880, now + 0.12);
                gain1.gain.setValueAtTime(0.12, now);
                gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
                osc1.connect(gain1);
                gain1.connect(audioCtx.destination);
                osc1.start(now);
                osc1.stop(now + 0.25);

                const osc2 = audioCtx.createOscillator();
                const gain2 = audioCtx.createGain();
                osc2.type = 'sine';
                osc2.frequency.setValueAtTime(880, now + 0.1);
                osc2.frequency.exponentialRampToValueAtTime(1320, now + 0.26);
                gain2.gain.setValueAtTime(0.12, now + 0.1);
                gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.32);
                osc2.connect(gain2);
                gain2.connect(audioCtx.destination);
                osc2.start(now + 0.1);
                osc2.stop(now + 0.35);
            } else if (type === 'reply') {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(520, now);
                osc.frequency.exponentialRampToValueAtTime(660, now + 0.08);
                gain.gain.setValueAtTime(0.08, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start(now);
                osc.stop(now + 0.2);
            } else if (type === 'stop') {
                // Descending deactivation tone
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(700, now);
                osc.frequency.exponentialRampToValueAtTime(220, now + 0.18);
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.19);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start(now);
                osc.stop(now + 0.20);
            }
        } catch (e) {}
    }

    function getActiveSpeechLang() {
        if (currentLanguage === 'bn') return 'bn-BD';
        if (currentLanguage === 'zh') return 'zh-CN';
        if (currentLanguage === 'en') return 'en-US';
        const siteLang = getSiteLanguage();
        if (siteLang === 'bn') return 'bn-BD';
        if (siteLang === 'zh') return 'zh-CN';
        return 'en-US';
    }

    /* =========================================================
       4. UI SYNCHRONIZATION
       ========================================================= */
    function setVisualState(newState) {
        currentState = newState;
        updateHandsFreeBtnUI();
        updateStatusLabelUI();
        stateChangeListeners.forEach(fn => {
            try { fn(newState); } catch (e) {}
        });
    }

    function onVisualStateChange(fn) {
        if (typeof fn === 'function') {
            stateChangeListeners.push(fn);
        }
    }

    function updateHandsFreeBtnUI() {
        const buttons = document.querySelectorAll('#handsFreeToggleBtn, .js-hands-free-toggle');
        const dots = document.querySelectorAll('#handsFreeDot, .js-hands-free-dot');
        const labels = document.querySelectorAll('#handsFreeLabel, .js-hands-free-label');

        if (handsFreeActive) {
            dots.forEach(dot => {
                if (currentState === STATE.COMMAND_LISTENING) {
                    dot.className = "w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse";
                } else if (currentState === STATE.PROCESSING) {
                    dot.className = "w-2.5 h-2.5 rounded-full bg-purple-400 animate-ping";
                } else if (currentState === STATE.SPEAKING) {
                    dot.className = "w-2.5 h-2.5 rounded-full bg-fuchsia-400 animate-pulse";
                } else {
                    dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse";
                }
            });

            labels.forEach(label => {
                label.textContent = isSessionActivated ? 'Hands-Free: LISTENING' : 'Hands-Free: ON';
            });

            buttons.forEach(btn => {
                btn.classList.remove('bg-slate-900', 'border-slate-700', 'text-slate-300');
                btn.classList.add('bg-emerald-950/80', 'border-emerald-500/70', 'text-emerald-300');
            });
        } else {
            dots.forEach(dot => {
                dot.className = "w-2.5 h-2.5 rounded-full bg-slate-500";
            });

            labels.forEach(label => {
                label.textContent = 'Hands-Free: OFF';
            });

            buttons.forEach(btn => {
                btn.classList.remove('bg-emerald-950/80', 'border-emerald-500/70', 'text-emerald-300');
                btn.classList.add('bg-slate-900', 'border-slate-700', 'text-slate-300');
            });
        }
    }

    function updateStatusLabelUI() {
        const statusText = document.getElementById('statusText');
        const statusDot = document.getElementById('statusIndicatorDot');
        if (!statusText) return;

        if (!handsFreeActive) {
            statusText.textContent = "SYSTEM READY";
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-slate-400";
        } else if (currentState === STATE.COMMAND_LISTENING) {
            statusText.textContent = "LISTENING FOR COMMANDS...";
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-cyan-400 animate-pulse";
        } else if (currentState === STATE.PROCESSING) {
            statusText.textContent = "ANALYZING INTENT...";
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-purple-400 animate-ping";
        } else if (currentState === STATE.SPEAKING) {
            statusText.textContent = "SPEAKING...";
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-fuchsia-400 animate-pulse";
        } else if (currentState === STATE.WAKE_WORD_STANDBY) {
            statusText.textContent = 'STANDBY: SAY "HI ASHIK"';
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
        } else if (currentState === STATE.ERROR) {
            statusText.textContent = "MIC PERMISSION REQUIRED";
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-rose-500";
        } else {
            statusText.textContent = "SYSTEM READY";
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-cyan-400";
        }
    }

    /* =========================================================
       5. CONTINUOUS SPEECH RECOGNITION SPOTTER
       ========================================================= */
    function startHandsFreeSpotter() {
        if (!handsFreeActive) return;
        if (isSpotterPausedForTTS) return;
        if (isStartingSpotter) return;

        if (spotterRestartTimer) {
            clearTimeout(spotterRestartTimer);
            spotterRestartTimer = null;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("[SME Voice] Web Speech API SpeechRecognition is not supported or inactive in this browser context.");
            return;
        }

        stopHandsFreeSpotter();

        const now = Date.now();
        if (now - lastSpotterStartTime < 500) {
            consecutiveRestartCount++;
            if (consecutiveRestartCount > 6) {
                spotterRestartTimer = setTimeout(() => {
                    consecutiveRestartCount = 0;
                    if (handsFreeActive && !wakeRecognition && !isSpotterPausedForTTS) {
                        startHandsFreeSpotter();
                    }
                }, 1200);
                return;
            }
        } else {
            consecutiveRestartCount = 0;
        }
        lastSpotterStartTime = now;
        isStartingSpotter = true;

        try {
            const rec = new SpeechRecognition();
            rec.continuous = true;
            rec.interimResults = false;
            rec.maxAlternatives = 3;
            rec.lang = getActiveSpeechLang();

            rec.onstart = () => {
                isStartingSpotter = false;
                if (handsFreeActive && currentState !== STATE.PROCESSING && currentState !== STATE.SPEAKING) {
                    setVisualState(isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY);
                }
            };

            rec.onresult = (e) => {
                if (!handsFreeActive) return;
                const lastIdx = e.results.length - 1;
                const res = e.results[lastIdx];
                if (!res || !res[0]) return;
                const rawTranscript = res[0].transcript;
                const altTranscripts = [];
                for (let i = 0; i < res.length; i++) {
                    if (res[i] && res[i].transcript) {
                        altTranscripts.push(res[i].transcript);
                    }
                }
                processSpotterTranscript(rawTranscript, altTranscripts);
            };

            rec.onerror = (e) => {
                isStartingSpotter = false;
                console.warn("[SME Voice] Spotter error:", e.error);
                if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
                    stopHandsFreeSpotter();
                    setVisualState(STATE.ERROR);
                    // Do not kill handsFreeActive state so button stays ON and user can grant permission on gesture
                    if (typeof window.showToast === 'function') {
                        window.showToast("Microphone access pending. Click Mic or Orb to speak.", "info");
                    }
                    return;
                }
            };

            rec.onend = () => {
                wakeRecognition = null;
                isStartingSpotter = false;
                if (handsFreeActive && !document.hidden && !isSpotterPausedForTTS) {
                    const restartDelay = (consecutiveRestartCount > 2) ? 600 : 200;
                    spotterRestartTimer = setTimeout(() => {
                        if (handsFreeActive && !wakeRecognition && !isSpotterPausedForTTS) {
                            startHandsFreeSpotter();
                        }
                    }, restartDelay);
                }
            };

            rec.start();
            wakeRecognition = rec;
        } catch (err) {
            isStartingSpotter = false;
            console.error("[SME Voice] Could not start hands-free recognition:", err);
        }
    }

    function stopHandsFreeSpotter() {
        if (spotterRestartTimer) {
            clearTimeout(spotterRestartTimer);
            spotterRestartTimer = null;
        }
        if (wakeRecognition) {
            try {
                wakeRecognition.onstart = null;
                wakeRecognition.onresult = null;
                wakeRecognition.onerror = null;
                wakeRecognition.onend = null;
                wakeRecognition.abort();
            } catch (e) {}
            wakeRecognition = null;
        }
        isStartingSpotter = false;
    }

    /* =========================================================
       6. TRANSCRIPT PROCESSING & EARLY STOP
       ========================================================= */
    function processSpotterTranscript(rawTranscript, altTranscripts = []) {
        if (!rawTranscript) return;
        let transcript = rawTranscript.trim();
        const candidates = [transcript];
        if (Array.isArray(altTranscripts)) {
            altTranscripts.forEach(alt => {
                if (alt && typeof alt === 'string') {
                    const c = alt.trim();
                    if (!candidates.includes(c)) candidates.push(c);
                }
            });
        }

        // 1. Check for Stop Phrase
        const stopCandidate = candidates.find(c => STOP_COPILOT_REGEX.test(c));
        if (stopCandidate) {
            console.log("[SME Voice] Stop Copilot phrase intercepted. Disabling hands-free.");
            handleStopCopilot();
            return;
        }

        // 2. Check for Wake Word ("Hi Ashik" / "Hello Copilot")
        const wakeCandidate = candidates.find(c => WAKE_WORD_REGEX.test(c));
        if (wakeCandidate) {
            initAudioContext();
            handsFreeActive = true;
            isSessionActivated = true;
            saveSession({
                enabled: true,
                mode: STATE.COMMAND_LISTENING,
                activated: true,
                language: currentLanguage
            });
            playChime('activate');
            setVisualState(STATE.COMMAND_LISTENING);
            updateHandsFreeBtnUI();

            let cleaned = wakeCandidate.replace(WAKE_WORD_REGEX, '').trim();
            cleaned = cleaned.replace(/^[,\s:;!?-]+|[,\s:;!?-]+$/g, '').trim();

            const queryToSubmit = (cleaned.length > 0) ? cleaned : wakeCandidate;
            const inputElem = document.getElementById('voice-text-input');
            if (inputElem) inputElem.value = queryToSubmit;

            setTimeout(() => { submitQuery(queryToSubmit); }, 200);
            return;
        }

        // 3. Consecutive Commands
        if (isSessionActivated || currentState === STATE.COMMAND_LISTENING) {
            const inputElem = document.getElementById('voice-text-input');
            if (inputElem) inputElem.value = transcript;
            submitQuery(transcript);
            return;
        }
    }

    /* =========================================================
       7. QUERY SUBMISSION & REAL CROSS-PAGE NAVIGATION
       ========================================================= */
    async function submitQuery(queryText) {
        if (!queryText || !queryText.trim()) return;
        const cleanQuery = queryText.trim();
        const inputElem = document.getElementById('voice-text-input');
        if (inputElem) inputElem.value = cleanQuery;

        setVisualState(STATE.PROCESSING);
        const startTime = performance.now();

        try {
            const res = await fetch('/api/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: cleanQuery,
                    transcript: cleanQuery,
                    language: currentLanguage,
                    locale: (currentLanguage === 'auto') ? getSiteLanguage() : currentLanguage
                })
            });

            const elapsed = Math.round(performance.now() - startTime);
            const latencyEl = document.getElementById('telemetryLatency');
            if (latencyEl) latencyEl.innerText = `${elapsed}ms`;

            if (!res.ok) {
                setVisualState(handsFreeActive ? (isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY) : STATE.HANDS_FREE_OFF);
                if (typeof window.showToast === 'function') window.showToast("Voice parsing failed", "error");
                return;
            }

            const data = await res.json();
            handleIntentResponse(data);
        } catch (err) {
            setVisualState(handsFreeActive ? (isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY) : STATE.HANDS_FREE_OFF);
            if (typeof window.showToast === 'function') window.showToast("Error contacting voice server: " + err.message, "error");
        }
    }

    function handleIntentResponse(data) {
        if (data.intent === 'CONTROL_STOP_COPILOT' || (data.suggested_action && data.suggested_action.action === 'DEACTIVATE_HANDS_FREE')) {
            handleStopCopilot();
            return;
        }

        // Saying or typing "Hi Ashik" / WAKE_WORD_GREETING activates Hands-Free ON / Listening mode!
        if (data.intent === 'WAKE_WORD_GREETING' || (data.suggested_action && data.suggested_action.action === 'STANDBY_COMMAND_LISTENING')) {
            initAudioContext();
            handsFreeActive = true;
            isSessionActivated = true;
            saveSession({
                enabled: true,
                mode: STATE.COMMAND_LISTENING,
                activated: true,
                language: currentLanguage
            });
            playChime('activate');
            setVisualState(STATE.COMMAND_LISTENING);
            updateHandsFreeBtnUI();
            startHandsFreeSpotter();
        }

        renderAssistantResponse(data);

        // Check if navigation action requested
        if (data.suggested_action && data.suggested_action.action === 'NAVIGATE' && data.suggested_action.url) {
            const targetUrl = data.suggested_action.url;
            const currentPath = window.location.pathname;

            if (handsFreeActive && targetUrl !== currentPath && targetUrl !== (currentPath + window.location.search)) {
                const respLang = (currentLanguage === 'auto') ? getSiteLanguage() : currentLanguage;
                let spokenMsg = data.spoken_response;
                if (respLang === 'bn' && data.spoken_response_bn) spokenMsg = data.spoken_response_bn;
                else if (respLang === 'zh' && data.spoken_response_zh) spokenMsg = data.spoken_response_zh;
                else if (data.spoken_response_en) spokenMsg = data.spoken_response_en;

                saveSession({
                    enabled: true,
                    mode: STATE.COMMAND_LISTENING,
                    activated: true,
                    language: currentLanguage,
                    speechToAnnounce: spokenMsg || '',
                    targetUrl: targetUrl
                });

                playSpokenAudio(spokenMsg);
                setTimeout(() => {
                    window.location.href = targetUrl;
                }, 400);
                return;
            } else {
                playSpokenAudio();
            }
        } else {
            playSpokenAudio();
        }
    }

    function renderAssistantResponse(data) {
        const respLang = (currentLanguage === 'auto') ? getSiteLanguage() : currentLanguage;
        lastSpokenText = data.spoken_response;
        if (respLang === 'bn' && data.spoken_response_bn) lastSpokenText = data.spoken_response_bn;
        else if (respLang === 'zh' && data.spoken_response_zh) lastSpokenText = data.spoken_response_zh;
        else if (data.spoken_response_en) lastSpokenText = data.spoken_response_en;

        const fullCard = document.getElementById('response-card');
        if (fullCard) {
            fullCard.classList.remove('hidden');

            const intentBadge = document.getElementById('response-intent-badge');
            if (intentBadge) intentBadge.innerText = data.intent || 'FINANCIAL_QUERY';

            const confBadge = document.getElementById('response-confidence-badge');
            if (confBadge) confBadge.innerText = `CONFIDENCE: ${( (data.confidence || 0.92) * 100).toFixed(0)}%`;

            const primaryText = document.getElementById('primary-response-text');
            if (primaryText) {
                primaryText.innerText = lastSpokenText || data.text_response || 'Query completed.';
            }

            const markdownContainer = document.getElementById('response-markdown-container');
            if (markdownContainer) {
                markdownContainer.innerText = data.text_response || lastSpokenText;
            }
        }
    }

    /* =========================================================
       8. SPEECH SYNTHESIS (TTS)
       ========================================================= */
    function playSpokenAudio(overrideText) {
        const textToSpeak = overrideText || lastSpokenText;
        if (!textToSpeak) {
            setVisualState(handsFreeActive ? (isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY) : STATE.HANDS_FREE_OFF);
            return;
        }

        playChime('reply');

        if (!('speechSynthesis' in window)) {
            setVisualState(handsFreeActive ? (isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY) : STATE.HANDS_FREE_OFF);
            return;
        }

        try {
            window.speechSynthesis.cancel();
            isSpotterPausedForTTS = true;
            stopHandsFreeSpotter();
            setVisualState(STATE.SPEAKING);

            const cleanSpeech = textToSpeak.replace(/[*#`_~]/g, '').trim();
            const utterance = new SpeechSynthesisUtterance(cleanSpeech);

            const respLang = (currentLanguage === 'auto') ? getSiteLanguage() : currentLanguage;
            if (respLang === 'bn') {
                utterance.lang = 'bn-BD';
            } else if (respLang === 'zh') {
                utterance.lang = 'zh-CN';
            } else {
                utterance.lang = 'en-US';
            }

            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            utterance.onend = () => {
                isSpotterPausedForTTS = false;
                currentUtterance = null;
                if (handsFreeActive) {
                    setVisualState(isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY);
                    setTimeout(() => { startHandsFreeSpotter(); }, 250);
                } else {
                    setVisualState(STATE.HANDS_FREE_OFF);
                }
            };

            utterance.onerror = () => {
                isSpotterPausedForTTS = false;
                currentUtterance = null;
                if (handsFreeActive) {
                    setVisualState(isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY);
                    setTimeout(() => { startHandsFreeSpotter(); }, 250);
                } else {
                    setVisualState(STATE.HANDS_FREE_OFF);
                }
            };

            currentUtterance = utterance;
            window.speechSynthesis.speak(utterance);
        } catch (err) {
            isSpotterPausedForTTS = false;
            if (handsFreeActive) {
                setVisualState(isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY);
                startHandsFreeSpotter();
            } else {
                setVisualState(STATE.HANDS_FREE_OFF);
            }
        }
    }

    function stopAllAudio() {
        if ('speechSynthesis' in window) {
            try { window.speechSynthesis.cancel(); } catch (e) {}
        }
        isSpotterPausedForTTS = false;
        currentUtterance = null;
        if (handsFreeActive) {
            setVisualState(isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY);
            startHandsFreeSpotter();
        } else {
            setVisualState(STATE.HANDS_FREE_OFF);
        }
    }

    /* =========================================================
       9. HANDS-FREE TOGGLE & STOP CONTROLS
       ========================================================= */
    function startStandby() {
        handsFreeActive = true;
        isSessionActivated = false;
        saveSession({
            enabled: true,
            mode: STATE.WAKE_WORD_STANDBY,
            activated: false,
            language: currentLanguage
        });
        setVisualState(STATE.WAKE_WORD_STANDBY);
        updateHandsFreeBtnUI();
        startHandsFreeSpotter();
    }

    function toggleHandsFreeMode() {
        initAudioContext();
        if (handsFreeActive) {
            handleStopCopilot();
        } else {
            startStandby();
            playChime('activate');
            if (typeof window.showToast === 'function') {
                window.showToast('Hands-Free Standby Active! Say "Hi Ashik" or ask a question.', 'success');
            }
        }
    }

    function handleStopCopilot() {
        playChime('stop');
        handsFreeActive = false;
        isSessionActivated = false;
        clearSession();
        stopHandsFreeSpotter();
        if ('speechSynthesis' in window) {
            try { window.speechSynthesis.cancel(); } catch (e) {}
        }
        isSpotterPausedForTTS = false;
        setVisualState(STATE.HANDS_FREE_OFF);
        updateHandsFreeBtnUI();
        if (typeof window.showToast === 'function') {
            window.showToast("Hands-Free Voice Assistant deactivated.", "info");
        }
    }

    function setLanguage(lang) {
        currentLanguage = lang;
        const btnAuto = document.getElementById('lang-btn-auto');
        const btnBn = document.getElementById('lang-btn-bn');
        const btnEn = document.getElementById('lang-btn-en');
        const btnZh = document.getElementById('lang-btn-zh');

        [btnAuto, btnBn, btnEn, btnZh].forEach(b => {
            if (b) {
                b.classList.remove('text-white', 'bg-cyan-600', 'bg-emerald-600');
                b.classList.add('text-slate-400');
            }
        });

        const activeBtn = (lang === 'auto') ? btnAuto : (lang === 'bn' ? btnBn : (lang === 'zh' ? btnZh : btnEn));
        if (activeBtn) {
            activeBtn.classList.remove('text-slate-400');
            activeBtn.classList.add('text-white', 'bg-cyan-600');
        }

        if (wakeRecognition) {
            wakeRecognition.lang = getActiveSpeechLang();
        }
    }

    /* =========================================================
       10. ON-LOAD INITIALIZATION & RECOVERY
       ========================================================= */
    document.addEventListener('DOMContentLoaded', () => {
        const saved = loadSession();
        if (saved && saved.enabled) {
            handsFreeActive = true;
            isSessionActivated = !!saved.activated;
            currentLanguage = saved.language || 'auto';
            setVisualState(isSessionActivated ? STATE.COMMAND_LISTENING : STATE.WAKE_WORD_STANDBY);
            updateHandsFreeBtnUI();

            // Check if there was pending speech to announce from previous navigation
            if (saved.speechToAnnounce) {
                const pendingSpeech = saved.speechToAnnounce;
                saveSession({
                    enabled: true,
                    mode: STATE.COMMAND_LISTENING,
                    activated: true,
                    language: currentLanguage
                });
                setTimeout(() => {
                    playSpokenAudio(pendingSpeech);
                }, 300);
            } else {
                setTimeout(() => {
                    startHandsFreeSpotter();
                }, 350);
            }
        } else if (window.location.pathname.includes('/app/voice')) {
            // Automatically initialize hands-free standby on dedicated Voice Assistant console
            startStandby();
        } else {
            setVisualState(STATE.HANDS_FREE_OFF);
            updateHandsFreeBtnUI();
        }

        // Attach signout listener to clear session
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href*="/logout"]');
            if (link) {
                clearSession();
            }
        });

        // User gesture listener to unblock audio/speech in browsers requiring touch/click
        const onFirstGesture = () => {
            initAudioContext();
            if (handsFreeActive && !wakeRecognition && !isSpotterPausedForTTS) {
                startHandsFreeSpotter();
            }
        };
        window.addEventListener('click', onFirstGesture, { passive: true });
        window.addEventListener('keydown', onFirstGesture, { passive: true });
        window.addEventListener('touchstart', onFirstGesture, { passive: true });
    });

    /* =========================================================
       11. EXPOSE PUBLIC API
       ========================================================= */
    window.SMEVoiceController = {
        isHandsFreeActive: () => handsFreeActive,
        isSessionActive: () => isSessionActivated,
        getCurrentState: () => currentState,
        startStandby: startStandby,
        toggleHandsFreeMode: toggleHandsFreeMode,
        handleStopCopilot: handleStopCopilot,
        submitQuery: submitQuery,
        playSpokenAudio: playSpokenAudio,
        stopAllAudio: stopAllAudio,
        setLanguage: setLanguage,
        onVisualStateChange: onVisualStateChange,
        simulateSpeechInput: (text) => {
            if (!text) return;
            processSpotterTranscript(text);
        }
    };

    // Global aliases
    window.toggleHandsFreeMode = toggleHandsFreeMode;
    window.submitQuery = submitQuery;
    window.stopAllAudio = stopAllAudio;
    window.setLanguage = setLanguage;

})(window, document);
