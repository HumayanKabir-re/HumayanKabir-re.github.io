// Hero background: drifting nodes that link up when close and scatter away
// from the pointer. Colours come from the theme tokens so one code path
// serves both themes.

(function () {
    const canvas = document.getElementById('neural-network');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    const MAX_LINK_DISTANCE = 150;
    const POINTER_RADIUS = 150;
    const POINTER_FORCE = 0.15;
    const DAMPING = 0.995;
    const MIN_SPEED = 0.05;

    let particles = [];
    let width = 0;
    let height = 0;
    let isMobile = false;
    let frameId = null;
    let resizePending = false;
    let heroVisible = true;
    let palette = readPalette();

    function readPalette() {
        const style = getComputedStyle(document.documentElement);
        const read = (name, fallback) => (style.getPropertyValue(name).trim() || fallback);

        return {
            node: read('--canvas-node', '0, 217, 255'),
            edge: read('--canvas-edge', '0, 217, 255'),
            nodeAlpha: parseFloat(read('--canvas-node-opacity', '0.95')),
            edgeAlpha: parseFloat(read('--canvas-edge-opacity', '0.8'))
        };
    }

    function particleCount() {
        return isMobile ? 25 : 80;
    }

    function randomVelocity() {
        return (Math.random() - 0.5) * 0.2;
    }

    // The CSS sizes this canvas to its parent, so the backing store has to be
    // derived from the rendered box rather than the window. Without this the
    // nodes render blurred and oversized on high-density screens.
    function resize() {
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return;

        const dpr = window.devicePixelRatio || 1;
        width = rect.width;
        height = rect.height;

        canvas.width = Math.round(rect.width * dpr);
        canvas.height = Math.round(rect.height * dpr);
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);

        const wasMobile = isMobile;
        isMobile = rect.width <= 768 || 'ontouchstart' in window;

        if (!particles.length || wasMobile !== isMobile) {
            seed();
        } else {
            // Keep the existing nodes, just pull any strays back inside.
            particles.forEach((p) => {
                p.x = Math.min(p.x, width);
                p.y = Math.min(p.y, height);
            });
        }
    }

    function seed() {
        const count = particleCount();
        particles = [];

        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: randomVelocity(),
                vy: randomVelocity(),
                radius: Math.random() * 2 + 1
            });
        }
    }

    const pointer = { x: null, y: null };

    // Bound to the window rather than the canvas: the hero copy sits above the
    // canvas, so canvas-bound pointer events never fire over the text.
    function trackPointer(clientX, clientY) {
        const rect = canvas.getBoundingClientRect();
        const x = clientX - rect.left;
        const y = clientY - rect.top;
        const inside = x >= 0 && x <= rect.width && y >= 0 && y <= rect.height;

        pointer.x = inside ? x : null;
        pointer.y = inside ? y : null;
    }

    function step() {
        ctx.clearRect(0, 0, width, height);

        particles.forEach((p, i) => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;

            p.vx *= DAMPING;
            p.vy *= DAMPING;

            // Damping alone would eventually stall every node.
            if (Math.abs(p.vx) < MIN_SPEED) p.vx = randomVelocity();
            if (Math.abs(p.vy) < MIN_SPEED) p.vy = randomVelocity();

            if (pointer.x !== null && pointer.y !== null) {
                const dx = pointer.x - p.x;
                const dy = pointer.y - p.y;
                const distance = Math.hypot(dx, dy);

                if (distance < POINTER_RADIUS) {
                    const force = (POINTER_RADIUS - distance) / POINTER_RADIUS;
                    const angle = Math.atan2(dy, dx);
                    p.vx -= Math.cos(angle) * force * POINTER_FORCE;
                    p.vy -= Math.sin(angle) * force * POINTER_FORCE;
                }
            }

            const size = p.radius * (isMobile ? 1.3 : 1.5);
            ctx.beginPath();
            ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${palette.node}, ${palette.nodeAlpha})`;
            ctx.fill();

            ctx.shadowBlur = isMobile ? 4 : 8;
            ctx.shadowColor = `rgba(${palette.node}, ${palette.nodeAlpha * 0.85})`;
            ctx.fill();
            ctx.shadowBlur = 0;

            for (let j = i + 1; j < particles.length; j++) {
                const other = particles[j];
                const dx = other.x - p.x;
                const dy = other.y - p.y;
                const distance = Math.hypot(dx, dy);

                if (distance < MAX_LINK_DISTANCE) {
                    const alpha = (1 - distance / MAX_LINK_DISTANCE) * palette.edgeAlpha;
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(${palette.edge}, ${alpha})`;
                    ctx.lineWidth = isMobile ? 1.5 : 2.5;
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(other.x, other.y);
                    ctx.stroke();
                }
            }
        });
    }

    function loop() {
        if (resizePending) {
            resizePending = false;
            resize();
        }

        step();
        frameId = requestAnimationFrame(loop);
    }

    function start() {
        if (frameId !== null || reduceMotion.matches) return;
        frameId = requestAnimationFrame(loop);
    }

    function stop() {
        if (frameId === null) return;
        cancelAnimationFrame(frameId);
        frameId = null;
    }

    function shouldRun() {
        return heroVisible && !document.hidden;
    }

    function sync() {
        if (shouldRun()) {
            start();
        } else {
            stop();
        }
    }

    resize();

    if (reduceMotion.matches) {
        step();
    } else {
        start();
    }

    // The observer only flags the canvas as dirty; the resize itself happens
    // once inside the next frame, so a drag-resize cannot queue up dozens.
    if ('ResizeObserver' in window) {
        const parent = canvas.parentElement || canvas;
        new ResizeObserver(() => {
            if (reduceMotion.matches) {
                resize();
                step();
                return;
            }
            resizePending = true;
        }).observe(parent);
    } else {
        window.addEventListener('resize', () => {
            resize();
            if (reduceMotion.matches) step();
        });
    }

    if ('IntersectionObserver' in window) {
        new IntersectionObserver((entries) => {
            heroVisible = entries[0].isIntersecting;
            if (!reduceMotion.matches) sync();
        }, { threshold: 0 }).observe(canvas);
    }

    document.addEventListener('visibilitychange', () => {
        if (!reduceMotion.matches) sync();
    });

    window.addEventListener('mousemove', (e) => trackPointer(e.clientX, e.clientY));
    window.addEventListener('mouseout', () => {
        pointer.x = null;
        pointer.y = null;
    });

    // Passive: preventing the default here would block scrolling for anyone
    // who starts a swipe inside the hero.
    window.addEventListener('touchmove', (e) => {
        const touch = e.touches[0];
        if (touch) trackPointer(touch.clientX, touch.clientY);
    }, { passive: true });

    window.addEventListener('touchend', () => {
        pointer.x = null;
        pointer.y = null;
    });

    reduceMotion.addEventListener('change', () => {
        if (reduceMotion.matches) {
            stop();
            step();
        } else {
            sync();
        }
    });

    document.addEventListener('themechange', () => {
        palette = readPalette();
        if (reduceMotion.matches) step();
    });
})();
