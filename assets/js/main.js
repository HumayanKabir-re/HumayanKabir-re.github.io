/* 
Site behaviour: theme, loading screen, hero typing, navigation, reveals.
The theme itself is applied by a small inline block in the head so the page never paints in the wrong palette first.
*/

(function () {
    'use strict';

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const root = document.documentElement;

    function setupTheme() {
        const toggle = document.querySelector('.theme-toggle');
        if (!toggle) return;

        toggle.addEventListener('click', () => {
            const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
            root.dataset.theme = next;
            toggle.setAttribute('aria-label', next === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');

            try {
                localStorage.setItem('theme', next);
            } catch (err) {
                // Private browsing can refuse writes. The theme still applies for this page load, it just will not be remembered.
            }

            document.dispatchEvent(new CustomEvent('themechange', { detail: next }));
        });
    }

    function setupLoadingScreen() {
        const screen = document.getElementById('loadingScreen');
        if (!screen) return;

        const bar = document.getElementById('loadingProgress');
        const status = document.getElementById('loadingStatus');
        const steps = ['Loading assets', 'Preparing content', 'Almost ready'];

        let progress = 0;
        let stepIndex = 0;

        const tick = setInterval(() => {
            progress = Math.min(progress + Math.random() * 30, 100);
            if (bar) bar.style.width = progress + '%';

            const nextStep = Math.min(Math.floor(progress / 34), steps.length - 1);
            if (status && nextStep !== stepIndex) {
                stepIndex = nextStep;
                status.textContent = steps[stepIndex];
            }

            if (progress >= 100) {
                clearInterval(tick);
                setTimeout(dismiss, 250);
            }
        }, 150);

        // Never leave the overlay up because a slow asset delayed the load event.
        const failsafe = setTimeout(dismiss, 3500);

        function dismiss() {
            clearTimeout(failsafe);
            clearInterval(tick);
            screen.classList.add('hidden');
            setTimeout(() => screen.remove(), 600);
        }
    }

    function setupTypingEffect() {
        const target = document.getElementById('typingText');
        if (!target) return;

        const phrases = [
            'ML Engineer',
            'Search & Retrieval',
            'LLM & GenAI Developer',
            'Data Pipeline Engineer',
            'DevOps Practitioner'
        ];

        if (reduceMotion.matches) {
            target.textContent = phrases[0];
            return;
        }

        let phrase = 0;
        let chars = 0;
        let deleting = false;

        (function tick() {
            const current = phrases[phrase];
            let delay = deleting ? 50 : 100;

            chars += deleting ? -1 : 1;
            target.textContent = current.slice(0, chars);

            if (!deleting && chars === current.length) {
                deleting = true;
                delay = 2000;
            } else if (deleting && chars === 0) {
                deleting = false;
                phrase = (phrase + 1) % phrases.length;
                delay = 500;
            }

            setTimeout(tick, delay);
        })();
    }

    function setupNavbar() {
        const nav = document.getElementById('navbar');
        if (!nav) return;

        const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 40);
        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    function setupMobileNav() {
        const toggle = document.getElementById('navToggle');
        const menu = document.getElementById('navMenu');
        if (!toggle || !menu) return;

        const close = () => {
            menu.classList.remove('open');
            toggle.classList.remove('open');
            toggle.setAttribute('aria-expanded', 'false');
        };

        toggle.addEventListener('click', () => {
            const open = menu.classList.toggle('open');
            toggle.classList.toggle('open', open);
            toggle.setAttribute('aria-expanded', String(open));
        });

        menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', close));

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') close();
        });
    }

    function setupReveals() {
        const targets = document.querySelectorAll('[data-animate]');
        if (!targets.length) return;

        if (reduceMotion.matches || !('IntersectionObserver' in window)) {
            targets.forEach((el) => el.classList.add('visible'));
            return;
        }

        targets.forEach((el) => el.classList.add('reveal-init'));

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px' });

        targets.forEach((el) => observer.observe(el));
    }

    function setupActiveSection() {
        const sections = document.querySelectorAll('main section[id], section[id]');
        const links = document.querySelectorAll('.nav-link[href^="#"]');
        if (!sections.length || !links.length || !('IntersectionObserver' in window)) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                links.forEach((link) => {
                    link.classList.toggle('active', link.getAttribute('href') === '#' + entry.target.id);
                });
            });
        }, { rootMargin: '-45% 0px -50%' });

        sections.forEach((section) => observer.observe(section));
    }

    function setupBackToTop() {
        const button = document.getElementById('backToTop');
        if (!button) return;

        const onScroll = () => button.classList.toggle('visible', window.scrollY > 600);
        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });

        button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: reduceMotion.matches ? 'auto' : 'smooth'
            });
        });
    }

    // Email and phone rows copy on click, with the label restored afterwards.
    function setupCopyToClipboard() {
        document.querySelectorAll('[data-copy]').forEach((el) => {
            el.addEventListener('click', (e) => {
                const value = el.dataset.copy;
                if (!navigator.clipboard || !value) return;

                e.preventDefault();
                const label = el.querySelector('.copy-label');
                if (!label) return;

                const original = label.textContent;
                navigator.clipboard.writeText(value).then(() => {
                    label.textContent = 'Copied';
                    setTimeout(() => { label.textContent = original; }, 1400);
                }).catch(() => {
                    window.location.href = el.getAttribute('href');
                });
            });
        });
    }

    function setFooterYear() {
        document.querySelectorAll('[data-year]').forEach((el) => {
            el.textContent = String(new Date().getFullYear());
        });
    }

    setupTheme();
    setFooterYear();
    setupLoadingScreen();
    setupTypingEffect();
    setupNavbar();
    setupMobileNav();
    setupReveals();
    setupActiveSection();
    setupBackToTop();
    setupCopyToClipboard();
})();
