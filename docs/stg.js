/**
 * Game News Bot - STG Easter Egg
 * Turns the webpage into a simple Shoot 'em Up game
 */
window.addEventListener('error', function (event) {
    const errorDiv = document.createElement('div');
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '10px';
    errorDiv.style.left = '10px';
    errorDiv.style.background = 'red';
    errorDiv.style.color = 'white';
    errorDiv.style.padding = '10px';
    errorDiv.style.zIndex = '999999';
    errorDiv.style.fontFamily = 'monospace';
    errorDiv.style.pointerEvents = 'none';
    errorDiv.style.whiteSpace = 'pre-wrap';
    errorDiv.innerText = 'JS_ERROR: ' + event.filename + ':' + event.lineno + ' ' + event.message;
    document.body.appendChild(errorDiv);
    console.error(event.error);
});

function setupSTG() {
    const trigger = document.getElementById('stg-trigger');
    if (!trigger) return;

    let isPlaying = false;
    let score = 0;
    let player = null;
    let ui = null;
    let enemies = [];
    let bullets = [];
    let lastTime = 0;
    let mousePos = { x: window.innerWidth / 2, y: window.innerHeight - 100 };
    let isShooting = false;
    let lastShotTime = 0;
    let gameStartTime = 0;
    let gameEndTime = 0;
    let invulnerable = false;
    const SHOT_DELAY = 150; // ms
    let audioCtx = null;

    function playSound(type) {
        if (!audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            audioCtx = new AudioContext();
        }
        if (audioCtx.state === 'suspended') audioCtx.resume();

        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        const now = audioCtx.currentTime;

        switch (type) {
            case 'shoot':
                osc.type = 'square';
                osc.frequency.setValueAtTime(880, now);
                osc.frequency.exponentialRampToValueAtTime(110, now + 0.1);
                gain.gain.setValueAtTime(0.05, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
                osc.start(now);
                osc.stop(now + 0.1);
                break;
            case 'hit':
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(200, now);
                osc.frequency.exponentialRampToValueAtTime(50, now + 0.1);
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
                osc.start(now);
                osc.stop(now + 0.1);
                break;
            case 'explode':
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(100, now);
                osc.frequency.exponentialRampToValueAtTime(0.01, now + 0.5);
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
                osc.start(now);
                osc.stop(now + 0.5);
                break;
            case 'start':
                osc.type = 'sine';
                osc.frequency.setValueAtTime(440, now);
                osc.frequency.setValueAtTime(880, now + 0.1);
                osc.frequency.setValueAtTime(1760, now + 0.2);
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 0.5);
                osc.start(now);
                osc.stop(now + 0.5);
                break;
            case 'gameover':
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(200, now);
                osc.frequency.linearRampToValueAtTime(50, now + 1.0);
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 1.0);
                osc.start(now);
                osc.stop(now + 1.0);
                break;
            case 'win':
                osc.type = 'square';
                osc.frequency.setValueAtTime(440, now);
                osc.frequency.setValueAtTime(554, now + 0.2);
                osc.frequency.setValueAtTime(659, now + 0.4);
                osc.frequency.setValueAtTime(880, now + 0.6);
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.linearRampToValueAtTime(0.001, now + 1.0);
                osc.start(now);
                osc.stop(now + 1.0);
                break;
        }
    }

    trigger.addEventListener('click', initGame);

    function initGame(e) {
        if (isPlaying || document.body.dataset.stgActive === "true") return;
        document.body.dataset.stgActive = "true";

        // Hide trigger and scroll
        trigger.style.display = 'none';
        window.scrollTo(0, 0);

        playSound('start'); // ominous intro sound

        // Collect all target elements for fade out (literally everything on screen)
        const targetBlocks = Array.from(document.querySelectorAll('.logo-icon, .site-title, .site-description, .time-panel, .poem-container, .filter-btn, .category-header, .article-card, .featured-card, .event-item, .cal-month, .cal-event, .site-footer p, h2, h3, .category-date'))
            .filter(el => {
                if (el.style.display === 'none') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            });

        // Pass ALL fading blocks (including titles) to become enemies
        const enemiesToSpawn = targetBlocks;

        // Phase 1: Staggered fade out natively
        let delay = 0;
        targetBlocks.forEach((el, index) => {
            setTimeout(() => {
                el.classList.add('stg-fade-out');
                if (index % 3 === 0) playSound('hit'); // quiet blip occasionally
            }, delay);
            delay += 30; // 30ms per element (faster since there are more now)
        });

        // Phase 2: Spawn clickable player after fade out completes
        setTimeout(() => {
            // Now apply the game mode CSS so background dims and layouts shift
            document.body.classList.add('stg-mode');
            spawnPlayer(enemiesToSpawn);
        }, delay + 500);
    }

    function spawnPlayer(targetCards) {
        // Setup the Player Pod
        player = document.createElement('div');
        player.id = 'stg-player';
        player.classList.add('clickable');

        // Force spawn at bottom center
        mousePos.x = window.innerWidth / 2;
        mousePos.y = window.innerHeight - 80;
        player.style.left = `${mousePos.x}px`;
        player.style.top = `${mousePos.y}px`;

        document.body.appendChild(player);

        // Click to start game
        player.addEventListener('click', () => startGame(targetCards), { once: true });
    }

    function startGame(cards) {
        if (isPlaying) return;
        isPlaying = true;
        score = 0;
        gameStartTime = performance.now();
        gameEndTime = 0;
        invulnerable = true;

        player.classList.remove('clickable');
        setTimeout(() => invulnerable = false, 2000);

        // Play energetic start sound
        playSound('win');

        // Setup UI
        ui = document.createElement('div');
        ui.id = 'stg-ui';
        updateUI();
        document.body.appendChild(ui);

        // Convert articles to enemies (Phase 3)
        setupEnemies(cards);

        // Inputs
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mousedown', () => isShooting = true);
        document.addEventListener('mouseup', () => isShooting = false);
        window.addEventListener('keydown', (e) => {
            if (e.key in keys) keys[e.key] = true;
            if (e.code === 'Space') {
                isShooting = true;
                if (isPlaying) e.preventDefault();
            }
        });
        window.addEventListener('keyup', (e) => {
            if (e.key in keys) keys[e.key] = false;
            if (e.code === 'Space') {
                isShooting = false;
                if (isPlaying) e.preventDefault();
            }
        });

        // Start Loop
        requestAnimationFrame(gameLoop);
    }

    trigger.addEventListener('click', initGame);

    function setupEnemies(cards) {
        cards.forEach((card, index) => {
            // Unconstrain the element from its parent grid/flex layouts by putting it in the body directly
            document.body.appendChild(card);

            // Force inline-block and no-wrap to get the true single-line expanded width for headers
            card.style.display = 'inline-block';
            card.style.whiteSpace = 'nowrap';
            const rect = card.getBoundingClientRect();

            // Start items falling from top of screen at random X
            const startX = Math.random() * (window.innerWidth - rect.width);
            const startY = -rect.height - (Math.random() * 500); // Stagger off-screen drops

            // Removed opacity/class removal from here, doing it after reflow
            card.classList.add('stg-enemy'); // For potential future CSS styling

            card.style.top = `${startY}px`;
            card.style.left = `${startX}px`;
            card.style.width = `${rect.width}px`;
            card.style.height = `${rect.height}px`;

            enemies.push({
                el: card,
                x: startX,
                y: startY,
                width: rect.width,
                height: rect.height,
                hp: card.classList.contains('featured-card') ? 5 : 2, // Larger cards have more HP
                speedX: (Math.random() - 0.5) * 2, // Drift
                speedY: 0.5 + Math.random() * 2.0, // Fall speed
                active: true
            });
        });

        // Need to reflow so absolute positioning takes hold smoothly
        setTimeout(() => {
            enemies.forEach(e => {
                e.el.style.margin = '0';
                e.el.style.position = 'absolute';
                // Now that they are off-screen and absolute, make them visible again
                e.el.classList.remove('stg-fade-out');
            });
            // Hide the actual grid containers so the layout breaks gracefully for the enemies
            document.querySelectorAll('.category-group, #featured-section').forEach(el => {
                el.style.height = `${el.offsetHeight}px`; // preserve scrolling space
            });
        }, 50);
    }

    function onMouseMove(e) {
        if (!isPlaying) return;
        // Relative mouse movement (delta)
        mousePos.x += e.movementX;
        mousePos.y += e.movementY;

        // Clamp to screen bounds
        mousePos.x = Math.max(16, Math.min(window.innerWidth - 16, mousePos.x));
        mousePos.y = Math.max(20, Math.min(window.innerHeight - 20, mousePos.y));
    }

    // Keyboard state
    const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowLeft: false, ArrowDown: false, ArrowRight: false };

    window.addEventListener('keydown', (e) => {
        if (e.key in keys) keys[e.key] = true;
    });
    window.addEventListener('keyup', (e) => {
        if (e.key in keys) keys[e.key] = false;
    });

    function updatePlayerPosKeyboard(dt) {
        const speed = 0.5 * dt; // pixels per ms
        if (keys.w || keys.ArrowUp) mousePos.y -= speed;
        if (keys.s || keys.ArrowDown) mousePos.y += speed;
        if (keys.a || keys.ArrowLeft) mousePos.x -= speed;
        if (keys.d || keys.ArrowRight) mousePos.x += speed;

        // Clamp
        mousePos.x = Math.max(16, Math.min(window.innerWidth - 16, mousePos.x));
        mousePos.y = Math.max(20, Math.min(window.innerHeight - 20, mousePos.y));
    }

    function shoot(now) {
        if (now - lastShotTime < SHOT_DELAY) return;
        lastShotTime = now;

        playSound('shoot');

        const bullet = document.createElement('div');
        bullet.className = 'stg-bullet';
        const bx = mousePos.x;
        const by = mousePos.y - 20;
        bullet.style.left = `${bx - 3}px`;
        bullet.style.top = `${by}px`;
        document.body.appendChild(bullet);

        bullets.push({
            el: bullet,
            x: bx,
            y: by,
            width: 6,
            height: 20,
            active: true
        });
    }

    function createExplosion(x, y, color = '#ff4444') {
        const count = 10 + Math.random() * 10;
        for (let i = 0; i < count; i++) {
            const p = document.createElement('div');
            p.className = 'stg-particle';
            p.style.left = `${x}px`;
            p.style.top = `${y}px`;
            p.style.background = color;

            const angle = Math.random() * Math.PI * 2;
            const dist = 50 + Math.random() * 50;
            p.style.setProperty('--dx', `${Math.cos(angle) * dist}px`);
            p.style.setProperty('--dy', `${Math.sin(angle) * dist}px`);

            document.body.appendChild(p);

            // Cleanup
            setTimeout(() => p.remove(), 500);
        }
    }

    function updateUI() {
        if (!ui) return;

        let timeStr = "0.00";
        if (gameStartTime > 0) {
            const now = gameEndTime > 0 ? gameEndTime : performance.now();
            timeStr = ((now - gameStartTime) / 1000).toFixed(2);
        }

        ui.innerHTML = `
            <div style="display: flex; justify-content: space-between; gap: 40px; align-items: flex-end;">
                <div>
                    <div class="score-label">SCORE</div>
                    <div style="font-size: 1.5em;">${String(score).padStart(6, '0')}</div>
                </div>
                <div style="text-align: right;">
                    <div class="score-label">TIME</div>
                    <div style="font-size: 1.5em;">${timeStr}</div>
                </div>
            </div>
            <div style="font-size: 0.5em; opacity: 0.5; margin-top: 5px;">X: ${Math.round(mousePos.x)} Y: ${Math.round(mousePos.y)}</div>
        `;
    }

    function endGame(win) {
        isPlaying = false;
        isShooting = false;
        gameEndTime = performance.now();
        updateUI(); // Finalize time on UI

        playSound(win ? 'win' : 'gameover');

        const timeStr = ((gameEndTime - gameStartTime) / 1000).toFixed(2);

        // Show result overlay
        const resultDiv = document.createElement('div');
        resultDiv.className = 'stg-result';
        resultDiv.innerHTML = win
            ? `<h1>ALL TARGETS DESTROYED</h1><p>TIME: ${timeStr} s</p><p>SCORE: ${score}</p><p style="font-size:0.5em; margin-top:20px; opacity:0.7;">Glory to Mankind.</p>`
            : `<h1>POD DESTROYED</h1><p>SCORE: ${score}</p>`;
        document.body.appendChild(resultDiv);

        setTimeout(() => {
            location.reload(); // Quickest way to reset the page state perfectly
        }, 4000); // 4 seconds wait so they can see the score and time
    }

    function checkCollision(r1, r2) {
        return !(r2.x > r1.x + r1.width ||
            r2.x + r2.width < r1.x ||
            r2.y > r1.y + r1.height ||
            r2.y + r2.height < r1.y);
    }

    function gameLoop(timestamp) {
        if (!isPlaying) return;
        try {
            const dt = timestamp - lastTime;
            lastTime = timestamp;

            // Update Keyboard pos
            updatePlayerPosKeyboard(dt);

            // Player movement
            if (player) {
                player.style.left = `${mousePos.x}px`;
                player.style.top = `${mousePos.y}px`;
                // Blinking effect while invulnerable
                player.style.opacity = invulnerable ? (Math.floor(timestamp / 100) % 2 === 0 ? '0.5' : '1') : '1';
                updateUI(); // Update coords display
            }

            // Shooting
            if (isShooting) {
                shoot(timestamp);
            }

            // --- Bullets logic ---
            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                if (!b.active) continue;

                b.y -= 15; // Bullet speed
                b.el.style.top = `${b.y}px`;

                if (b.y < -50) {
                    b.active = false;
                    if (b.el && b.el.parentNode) b.el.remove();
                    bullets.splice(i, 1);
                }
            }

            // --- Enemies logic ---
            let winCheck = true;
            const playerRect = { x: mousePos.x - 16, y: mousePos.y - 20, width: 32, height: 40 };

            for (let i = enemies.length - 1; i >= 0; i--) {
                const e = enemies[i];
                if (!e.active) continue;
                winCheck = false; // Still an active enemy

                // Move enemy
                e.y += e.speedY;
                e.x += e.speedX;

                // Screen wrap/bounce
                if (e.x < 0 || e.x + e.width > window.innerWidth) e.speedX *= -1;

                e.el.style.transform = `translate(${e.x - (parseFloat(e.el.style.left) || 0)}px, ${e.y - (parseFloat(e.el.style.top) || 0)}px)`;

                // Build current hitbox
                const eRect = { x: e.x, y: e.y, width: e.width, height: e.height };

                // Check collision with player
                if (!invulnerable && checkCollision(playerRect, eRect)) {
                    playSound('explode');
                    createExplosion(mousePos.x, mousePos.y, '#eae6d9');
                    endGame(false);
                    return;
                }

                // Check collision with bullets
                for (let j = bullets.length - 1; j >= 0; j--) {
                    const b = bullets[j];
                    if (!b.active) continue;

                    if (checkCollision(b, eRect)) {
                        b.active = false;
                        if (b.el && b.el.parentNode) b.el.remove();
                        bullets.splice(j, 1);

                        e.hp--;
                        // Flash effect
                        e.el.style.backgroundColor = 'rgba(255, 68, 68, 0.5)';
                        setTimeout(() => { if (e.active) e.el.style.backgroundColor = ''; }, 50);

                        if (e.hp <= 0) {
                            e.active = false;
                            e.el.classList.add('stg-destroyed');
                            playSound('explode');
                            createExplosion(e.x + e.width / 2, e.y + e.height / 2);
                            score += (e.width > 300) ? 500 : 100; // More points for featured
                            updateUI();
                            break;
                        } else {
                            playSound('hit');
                        }
                    }
                }

                // Loop enemies to top if they fall off bottom
                if (e.y > Math.max(document.body.scrollHeight, window.innerHeight)) {
                    e.y = -e.height;
                    e.x = Math.random() * (window.innerWidth - e.width);
                }
            }

            if (winCheck) {
                endGame(true);
                return;
            }
        } catch (err) {
            console.error(err);
            const errDiv = document.createElement('div');
            errDiv.style.position = 'fixed';
            errDiv.style.top = '100px';
            errDiv.style.left = '10px';
            errDiv.style.background = 'blue';
            errDiv.style.color = 'white';
            errDiv.style.zIndex = '999999';
            errDiv.innerText = 'GAMELOOP_ERR: ' + err.message + '\n' + err.stack;
            document.body.appendChild(errDiv);
        }

        requestAnimationFrame(gameLoop);
    }
} // End of setupSTG

// Initialize if DOM is already loaded, otherwise wait
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupSTG);
} else {
    setupSTG();
}
