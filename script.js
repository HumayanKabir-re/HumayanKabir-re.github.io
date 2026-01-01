// Loading Screen Management
const loadingScreen = document.getElementById('loadingScreen');
const loadingProgress = document.getElementById('loadingProgress');
const loadingStatus = document.getElementById('loadingStatus');

let progress = 0;
const loadingInterval = setInterval(() => {
    progress += Math.random() * 30;
    if (progress > 90) progress = 90;
    
    loadingProgress.style.width = progress + '%';
    
    if (progress < 30) {
        loadingStatus.textContent = 'Loading resources...';
    } else if (progress < 60) {
        loadingStatus.textContent = 'Initializing animations...';
    } else {
        loadingStatus.textContent = 'Almost ready...';
    }
}, 200);

// Typing effect for hero section
const typingTexts = [
    'ML Engineer',
    'Deep Learning Researcher',
    'LLM & GenAI Developer',
    'Data Pipeline Architect',
    'DevOps Specialist'
];

let textIndex = 0;
let charIndex = 0;
let isDeleting = false;
let typingSpeed = 100;

function typeWriter() {
    const typingElement = document.getElementById('typingText');
    if (!typingElement) return;

    const currentText = typingTexts[textIndex];
    
    if (isDeleting) {
        typingElement.textContent = currentText.substring(0, charIndex - 1);
        charIndex--;
        typingSpeed = 50;
    } else {
        typingElement.textContent = currentText.substring(0, charIndex + 1);
        charIndex++;
        typingSpeed = 100;
    }
    
    if (!isDeleting && charIndex === currentText.length) {
        isDeleting = true;
        typingSpeed = 2000; // Pause at end
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        textIndex = (textIndex + 1) % typingTexts.length;
        typingSpeed = 500;
    }
    
    setTimeout(typeWriter, typingSpeed);
}

// Neural Network Canvas Animation
class NeuralNetwork {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.connections = [];
        this.particleCount = 80;
        this.maxDistance = 150;
        this.mouse = { x: null, y: null, radius: 150 };
        
        this.resize();
        this.init();
        this.animate();
        
        window.addEventListener('resize', () => this.resize());
        canvas.addEventListener('mousemove', (e) => {
            this.mouse.x = e.x;
            this.mouse.y = e.y;
        });
        canvas.addEventListener('mouseleave', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    init() {
        this.particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                // REDUCED SPEED: Changed from 0.5 to 0.2 (60% slower)
                vx: (Math.random() - 0.5) * 0.2,
                vy: (Math.random() - 0.5) * 0.2,
                radius: Math.random() * 2 + 1
            });
        }
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        this.particles.forEach((particle, i) => {
            // Move particle
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Bounce off edges
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            // REDUCED DAMPING: Apply slight damping to prevent particles from flying too fast
            particle.vx *= 0.995;
            particle.vy *= 0.995;
            
            // Keep minimum velocity to prevent stopping
            const minSpeed = 0.05;
            if (Math.abs(particle.vx) < minSpeed) particle.vx = (Math.random() - 0.5) * 0.2;
            if (Math.abs(particle.vy) < minSpeed) particle.vy = (Math.random() - 0.5) * 0.2;
            
            // Mouse interaction - REDUCED FORCE
            if (this.mouse.x !== null && this.mouse.y !== null) {
                const dx = this.mouse.x - particle.x;
                const dy = this.mouse.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < this.mouse.radius) {
                    const force = (this.mouse.radius - distance) / this.mouse.radius;
                    const angle = Math.atan2(dy, dx);
                    // REDUCED from 0.5 to 0.15 (70% less force)
                    particle.vx -= Math.cos(angle) * force * 0.15;
                    particle.vy -= Math.sin(angle) * force * 0.15;
                }
            }
            
            // Draw particle - MUCH BRIGHTER AND MORE VISIBLE
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius * 1.5, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(0, 217, 255, 0.95)'; // Increased from 0.7 to 0.95
            this.ctx.fill();
            
            // Add glow effect to particles
            this.ctx.shadowBlur = 8;
            this.ctx.shadowColor = 'rgba(0, 217, 255, 0.8)';
            this.ctx.fill();
            this.ctx.shadowBlur = 0;
            
            // Draw connections - MUCH THICKER AND BRIGHTER
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[j].x - particle.x;
                const dy = this.particles[j].y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < this.maxDistance) {
                    // INCREASED OPACITY: from 0.5 to 0.8 (much more visible)
                    const opacity = (1 - distance / this.maxDistance) * 0.8;
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(0, 217, 255, ${opacity})`;
                    // INCREASED LINE WIDTH: from 1.5 to 2.5 (much thicker)
                    this.ctx.lineWidth = 2.5;
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Scroll animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Observe all animated elements
    document.querySelectorAll('[data-animate]').forEach(el => {
        observer.observe(el);
    });
    
    document.querySelectorAll('.project-card').forEach(el => {
        observer.observe(el);
    });
    
    document.querySelectorAll('.skill-category').forEach(el => {
        observer.observe(el);
    });
    
    document.querySelectorAll('.timeline-item').forEach(el => {
        observer.observe(el);
    });
}

// Navbar scroll effect
function setupNavbar() {
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

// Mobile navigation
function setupMobileNav() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });
    
    // Close menu when clicking on a link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
        });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
            navMenu.classList.remove('active');
        }
    });
}

// Smooth scrolling for anchor links
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Parallax effect for hero section
function setupParallax() {
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero-content');
        if (hero) {
            hero.style.transform = `translateY(${scrolled * 0.3}px)`;
            hero.style.opacity = 1 - scrolled / 700;
        }
    });
}

// Add copy to clipboard functionality for contact details
function setupCopyToClipboard() {
    document.querySelectorAll('.contact-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const text = item.querySelector('span')?.textContent;
            if (text && !item.getAttribute('href').startsWith('http')) {
                e.preventDefault();
                navigator.clipboard.writeText(text).then(() => {
                    // Visual feedback
                    const originalText = item.querySelector('span').textContent;
                    item.querySelector('span').textContent = 'Copied!';
                    setTimeout(() => {
                        item.querySelector('span').textContent = originalText;
                    }, 2000);
                });
            }
        });
    });
}

// Particle effect on hover for project cards
function setupProjectCardEffects() {
    const cards = document.querySelectorAll('.project-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Add gradient animation to section titles
function animateSectionTitles() {
    const titles = document.querySelectorAll('.section-title');
    
    titles.forEach(title => {
        let hue = 0;
        setInterval(() => {
            hue = (hue + 1) % 360;
            const gradient = `linear-gradient(135deg, 
                hsl(${hue}, 100%, 60%) 0%, 
                hsl(${(hue + 60) % 360}, 100%, 60%) 50%, 
                hsl(${(hue + 120) % 360}, 100%, 60%) 100%)`;
            title.style.backgroundImage = gradient;
        }, 50);
    });
}

// Add active section highlighting in navbar
function setupActiveSection() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    window.addEventListener('scroll', () => {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add loading class to body
    document.body.classList.add('loading');
    
    // Start typing effect
    typeWriter();
    
    // Initialize neural network animation
    const canvas = document.getElementById('neural-network');
    if (canvas) {
        new NeuralNetwork(canvas);
    }
    
    // Setup all features
    setupScrollAnimations();
    setupNavbar();
    setupMobileNav();
    setupSmoothScroll();
    setupParallax();
    setupCopyToClipboard();
    setupProjectCardEffects();
    setupActiveSection();
    setupVisitorCounter();
    
    // Complete loading after everything is initialized
    setTimeout(() => {
        clearInterval(loadingInterval);
        loadingProgress.style.width = '100%';
        loadingStatus.textContent = 'Ready!';
        
        setTimeout(() => {
            loadingScreen.classList.add('hidden');
            document.body.classList.remove('loading');
            document.body.classList.add('page-loaded');
        }, 300);
    }, 1500);
    
    console.log('✨ Portfolio initialized successfully! 🚀');
});

// Visitor Counter with Location Detection
async function setupVisitorCounter() {
    const visitorCountElement = document.getElementById('visitorCount');
    const visitorLocationElement = document.getElementById('visitorLocation');
    
    // Get current count from localStorage
    let visitCount = localStorage.getItem('portfolioVisitCount');
    
    if (!visitCount) {
        visitCount = 0;
    }
    
    // Increment count
    visitCount = parseInt(visitCount) + 1;
    
    // Save back to localStorage
    localStorage.setItem('portfolioVisitCount', visitCount);
    
    // Animate counter
    let currentCount = 0;
    const targetCount = visitCount;
    const duration = 2000; // 2 seconds
    const increment = targetCount / (duration / 16); // 60fps
    
    const counterInterval = setInterval(() => {
        currentCount += increment;
        if (currentCount >= targetCount) {
            currentCount = targetCount;
            clearInterval(counterInterval);
        }
        visitorCountElement.textContent = Math.floor(currentCount).toLocaleString();
    }, 16);
    
    // Fetch visitor location using free ipapi.co API
    try {
        const response = await fetch('https://ipapi.co/json/');
        const data = await response.json();
        
        // Format location string
        let locationText = '';
        
        if (data.city && data.country_name) {
            locationText = `${data.city}, ${data.country_name}`;
        } else if (data.country_name) {
            locationText = data.country_name;
        } else if (data.country) {
            locationText = data.country;
        } else {
            locationText = 'Unknown Location';
        }
        
        // Add flag emoji if available
        if (data.country_code) {
            const flag = getFlagEmoji(data.country_code);
            locationText = `${flag} ${locationText}`;
        }
        
        visitorLocationElement.textContent = locationText;
        
        console.log('📍 Location detected:', locationText);
        console.log('🌍 Full location data:', {
            city: data.city,
            region: data.region,
            country: data.country_name,
            ip: data.ip
        });
        
    } catch (error) {
        console.error('Location detection failed:', error);
        visitorLocationElement.textContent = 'Location unavailable';
    }
    
    console.log(`👁️ Visit count: ${visitCount}`);
}

// Convert country code to flag emoji
function getFlagEmoji(countryCode) {
    if (!countryCode || countryCode.length !== 2) return '';
    
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt());
    
    return String.fromCodePoint(...codePoints);
}

// Add keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.getElementById('navMenu')?.classList.remove('active');
    }
});

// Respect prefers-reduced-motion
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
if (prefersReducedMotion.matches) {
    console.log('Reduced motion preference detected - animations minimized');
}

// Performance monitoring
if (window.performance && window.performance.timing) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            const domReadyTime = perfData.domContentLoadedEventEnd - perfData.navigationStart;
            
            console.log(`📊 Performance Metrics:`);
            console.log(`   Page Load: ${pageLoadTime}ms`);
            console.log(`   DOM Ready: ${domReadyTime}ms`);
        }, 0);
    });
}
