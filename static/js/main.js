/**
 * WeekStory Frontend Interactions helper (Zero-AI)
 */

// Helper for live character counter in social post inline editor
window.updateSocialCharCounter = function(textarea) {
    if (!textarea) return;
    const targetId = textarea.getAttribute('data-counter-target');
    const maxLen = parseInt(textarea.getAttribute('data-max-length') || '2200', 10);
    const counterEl = targetId ? document.getElementById(targetId) : null;
    if (counterEl) {
        const currentLen = textarea.value.length;
        counterEl.textContent = currentLen;
        const wrapper = counterEl.closest('.social-char-counter');
        if (wrapper) {
            wrapper.style.color = currentLen > maxLen ? 'hsl(var(--danger))' : 'hsl(var(--text-muted))';
        }
    }
};

// Helper for typography size selector (A-, A, A+)
window.setStoryFontSize = function(sizeKey) {
    const bodyEl = document.querySelector('.story-body-text');
    if (!bodyEl) return;
    const sizes = {
        sm: '0.95rem',
        md: '1.1rem',
        lg: '1.28rem'
    };
    const chosen = sizes[sizeKey] || sizes.md;
    bodyEl.style.fontSize = chosen;
    try {
        localStorage.setItem('weekstory_font_size', sizeKey);
    } catch (e) {}
    document.querySelectorAll('.font-size-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-size') === sizeKey);
    });
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);

        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.remove();
            });
        }
    });

    // 2. Tab switcher for social media posts dashboard
    window.switchTab = function(event, platformId) {
        const tabsContainer = event.currentTarget.closest('.social-dashboard');
        if (!tabsContainer) return;

        const tabs = tabsContainer.querySelectorAll('.social-tab');
        const contents = tabsContainer.querySelectorAll('.tab-content');

        tabs.forEach(t => t.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));

        event.currentTarget.classList.add('active');
        const targetContent = tabsContainer.querySelector(`#post-${platformId}`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    };

    // 3. Toggle Categories Dropdown in Navbar
    const categoriesBtn = document.getElementById("categoriesDropdownBtn");
    const categoriesMenu = document.getElementById("categoriesDropdownMenu");

    if (categoriesBtn && categoriesMenu) {
        categoriesBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const isShown = categoriesMenu.classList.contains("show") || categoriesMenu.style.display === "block";
            if (isShown) {
                categoriesMenu.style.display = "none";
                categoriesMenu.classList.remove("show");
            } else {
                categoriesMenu.style.display = "block";
                categoriesMenu.classList.add("show");
            }
        });

        document.addEventListener("click", (e) => {
            if (!categoriesBtn.contains(e.target) && !categoriesMenu.contains(e.target)) {
                categoriesMenu.style.display = "none";
                categoriesMenu.classList.remove("show");
            }
        });
    }

    // 4. Cookies Consent Banner Manager
    const cookieBanner = document.getElementById("cookie-consent-banner");
    const acceptCookiesBtn = document.getElementById("accept-cookies-btn");

    if (cookieBanner && acceptCookiesBtn) {
        const cookiesAccepted = document.cookie.split('; ').find(row => row.startsWith('cookies_accepted='));
        if (!cookiesAccepted) {
            cookieBanner.style.display = 'block';
        }

        acceptCookiesBtn.addEventListener("click", () => {
            document.cookie = "cookies_accepted=true; max-age=31536000; path=/";
            cookieBanner.style.animation = 'none';
            cookieBanner.style.opacity = '0';
            cookieBanner.style.transition = 'opacity 0.4s ease';
            setTimeout(() => {
                cookieBanner.style.display = 'none';
            }, 400);
        });
    }

    // 5. Toggle Mobile Menu Accordion
    const togglerBtn = document.getElementById("navbarTogglerBtn");
    const navbarNav = document.querySelector(".navbar-nav");

    if (togglerBtn && navbarNav) {
        togglerBtn.addEventListener("click", (e) => {
            e.preventDefault();
            navbarNav.classList.toggle("show");
            const icon = togglerBtn.querySelector("i");
            if (navbarNav.classList.contains("show")) {
                icon.className = "fa-solid fa-xmark";
            } else {
                icon.className = "fa-solid fa-bars";
            }
        });
    }

    // 6. Restore saved typography size preference
    try {
        const savedSize = localStorage.getItem('weekstory_font_size') || 'md';
        if (document.querySelector('.story-body-text')) {
            window.setStoryFontSize(savedSize);
        }
    } catch (e) {}

    // 7. Native Web Speech API (window.speechSynthesis) Paragraph-Synchronized Reader
    const ttsContainer = document.getElementById('tts-audio-player');
    if (ttsContainer) {
        const storyId = ttsContainer.getAttribute('data-story-id') || 'default';
        const storageKeyIndex = `weekstory_tts_para_${storyId}`;
        const storageKeyRate = `weekstory_tts_rate_${storyId}`;
        const playIcon = document.getElementById('tts-play-icon');
        const statusLabel = document.getElementById('tts-status-label');
        const progressFill = document.getElementById('tts-progress-fill');
        const progressText = document.getElementById('tts-progress-text');
        const rateSelect = document.getElementById('tts-rate-select');

        if (!('speechSynthesis' in window)) {
            if (statusLabel) {
                statusLabel.textContent = 'Tu navegador no soporta síntesis de voz (Web Speech API).';
            }
        } else {
            const synth = window.speechSynthesis;
            let paragraphs = [];
            let currentParagraphIndex = 0;
            let isPlaying = false;
            let isPaused = false;
            let currentRate = 1.0;

            // Restore saved preferences
            try {
                const savedRate = localStorage.getItem(storageKeyRate);
                if (savedRate && rateSelect) {
                    rateSelect.value = savedRate;
                    currentRate = parseFloat(savedRate) || 1.0;
                }
                const savedIdx = parseInt(localStorage.getItem(storageKeyIndex) || '0', 10);
                if (!isNaN(savedIdx) && savedIdx >= 0) {
                    currentParagraphIndex = savedIdx;
                }
            } catch (e) {}

            function collectParagraphs() {
                const bodyEl = document.querySelector('.story-body-text');
                if (!bodyEl) return [];
                const pNodes = Array.from(bodyEl.querySelectorAll('p, blockquote, h2, h3, li')).filter(
                    el => (el.innerText || el.textContent || '').trim().length > 0
                );
                if (pNodes.length > 0) {
                    return pNodes;
                }
                return [bodyEl];
            }

            function splitIntoChunks(text) {
                return text
                    .replace(/\s+/g, ' ')
                    .split(/(?<=[.!?…;])\s+/)
                    .map(s => s.trim())
                    .filter(Boolean);
            }

            function clearHighlight() {
                document.querySelectorAll('.reading-active').forEach(el => {
                    el.classList.remove('reading-active');
                });
            }

            function highlightParagraph(index) {
                clearHighlight();
                const el = paragraphs[index];
                if (el && el.classList) {
                    el.classList.add('reading-active');
                    const rect = el.getBoundingClientRect();
                    const inView = rect.top >= 80 && rect.bottom <= (window.innerHeight - 80);
                    if (!inView && typeof el.scrollIntoView === 'function') {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            }

            function getSpanishVoice() {
                const voices = synth.getVoices() || [];
                return (
                    voices.find(v => v.lang && v.lang.toLowerCase().startsWith('es')) ||
                    voices[0] ||
                    null
                );
            }

            function updateUI() {
                if (playIcon) {
                    playIcon.className = (isPlaying && !isPaused) ? 'fa-solid fa-pause' : 'fa-solid fa-play';
                }
                const total = paragraphs.length;
                const pct = total > 0 ? Math.min(100, Math.round((currentParagraphIndex / total) * 100)) : 0;
                if (progressFill) progressFill.style.width = `${pct}%`;
                if (progressText) progressText.textContent = `${pct}%`;
                try {
                    localStorage.setItem(storageKeyIndex, String(currentParagraphIndex));
                } catch (e) {}
            }

            function speakParagraph(index) {
                if (!paragraphs.length) {
                    paragraphs = collectParagraphs();
                }
                if (index >= paragraphs.length) {
                    isPlaying = false;
                    isPaused = false;
                    clearHighlight();
                    currentParagraphIndex = paragraphs.length;
                    updateUI();
                    currentParagraphIndex = 0;
                    try {
                        localStorage.setItem(storageKeyIndex, '0');
                    } catch (e) {}
                    return;
                }

                currentParagraphIndex = Math.max(0, index);
                updateUI();

                const el = paragraphs[currentParagraphIndex];
                const rawText = (el.innerText || el.textContent || '').trim();
                const chunks = splitIntoChunks(rawText);
                if (!chunks.length) {
                    speakParagraph(currentParagraphIndex + 1);
                    return;
                }

                let chunkIdx = 0;
                function speakNextChunk() {
                    if (!isPlaying) return;
                    if (chunkIdx >= chunks.length) {
                        el.classList.remove('reading-active');
                        speakParagraph(currentParagraphIndex + 1);
                        return;
                    }
                    const utterance = new SpeechSynthesisUtterance(chunks[chunkIdx]);
                    utterance.lang = 'es-ES';
                    utterance.rate = currentRate;
                    const voice = getSpanishVoice();
                    if (voice) utterance.voice = voice;

                    utterance.onstart = () => {
                        highlightParagraph(currentParagraphIndex);
                    };

                    utterance.onend = () => {
                        if (isPlaying && !isPaused) {
                            chunkIdx += 1;
                            speakNextChunk();
                        }
                    };

                    utterance.onerror = () => {
                        isPlaying = false;
                        isPaused = false;
                        clearHighlight();
                        updateUI();
                    };

                    synth.speak(utterance);
                }

                speakNextChunk();
            }

            paragraphs = collectParagraphs();
            if (currentParagraphIndex >= paragraphs.length) {
                currentParagraphIndex = 0;
            }
            updateUI();

            window.weekStoryTTS = {
                togglePlayPause() {
                    if (!paragraphs.length) {
                        paragraphs = collectParagraphs();
                    }
                    if (!paragraphs.length) return;

                    if (!isPlaying) {
                        synth.cancel();
                        isPlaying = true;
                        isPaused = false;
                        updateUI();
                        speakParagraph(currentParagraphIndex);
                    } else if (isPaused) {
                        synth.resume();
                        isPaused = false;
                        updateUI();
                    } else {
                        synth.pause();
                        isPaused = true;
                        updateUI();
                    }
                },
                prevParagraph() {
                    if (!paragraphs.length) paragraphs = collectParagraphs();
                    if (!paragraphs.length) return;
                    synth.cancel();
                    currentParagraphIndex = Math.max(0, currentParagraphIndex - 1);
                    isPlaying = true;
                    isPaused = false;
                    speakParagraph(currentParagraphIndex);
                },
                nextParagraph() {
                    if (!paragraphs.length) paragraphs = collectParagraphs();
                    if (!paragraphs.length) return;
                    synth.cancel();
                    currentParagraphIndex = Math.min(paragraphs.length - 1, currentParagraphIndex + 1);
                    isPlaying = true;
                    isPaused = false;
                    speakParagraph(currentParagraphIndex);
                },
                stop() {
                    synth.cancel();
                    isPlaying = false;
                    isPaused = false;
                    currentParagraphIndex = 0;
                    clearHighlight();
                    updateUI();
                },
                setRate(value) {
                    currentRate = parseFloat(value) || 1.0;
                    try {
                        localStorage.setItem(storageKeyRate, String(currentRate));
                    } catch (e) {}
                    if (isPlaying && !isPaused) {
                        synth.cancel();
                        speakParagraph(currentParagraphIndex);
                    }
                }
            };

            window.addEventListener('beforeunload', () => {
                synth.cancel();
            });

            document.body.addEventListener('htmx:beforeRequest', () => {
                if (synth.speaking || synth.pending) {
                    synth.cancel();
                }
            });
        }
    }
});
