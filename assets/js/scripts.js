import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

document.addEventListener('DOMContentLoaded', function() {
    console.log('Cauldron Scripts Loaded');
    const body = document.body;
    const html = document.documentElement;
    
    // Initialize Materialize Components
    const dropdownElems = document.querySelectorAll('.dropdown-trigger');
    M.Dropdown.init(dropdownElems, {
        coverTrigger: false,
        constrainWidth: false
    });

    const sidenavElems = document.querySelectorAll('.sidenav');
    M.Sidenav.init(sidenavElems);

    const selectElems = document.querySelectorAll('select');
    M.FormSelect.init(selectElems);

    // Synthwave Canvas Initialization
    const canvas = document.getElementById('synth-canvas');
    let ctx = null;
    let particles = [];
    let animationFrame = null;

    if (canvas) {
        ctx = canvas.getContext('2d');
        console.log('Synth Canvas Found');
    }

    // Theme Management
    const themeKey = 'cauldron_theme';
    const currentTheme = localStorage.getItem(themeKey) || 'default-light';
    
    // Apply initial theme
    applyTheme(currentTheme);

    // Initialize theme selector if on profile page
    const themeSelector = document.getElementById('theme-selector');
    if (themeSelector) {
        themeSelector.value = currentTheme;
        M.FormSelect.init(themeSelector);

        themeSelector.addEventListener('change', function() {
            const selectedTheme = this.value;
            applyTheme(selectedTheme);
            localStorage.setItem(themeKey, selectedTheme);
            M.toast({html: 'Theme updated!', classes: 'green'});
        });
    }

    function applyTheme(theme) {
        console.log('Applying theme:', theme);
        html.setAttribute('data-theme', theme);
        
        if (theme.includes('dark')) {
            html.classList.add('dark-mode');
            body.classList.add('dark-mode');
        } else {
            html.classList.remove('dark-mode');
            body.classList.remove('dark-mode');
        }

        // Handle Synthwave Animation based on theme
        if (theme.startsWith('cyber') && canvas) {
            console.log('Starting Synth Animation');
            initSynth();
            if (!animationFrame) animateSynth();
        } else if (animationFrame) {
            console.log('Stopping Synth Animation');
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
            if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
        }

        // Initialize Mermaid with appropriate theme
        let mermaidTheme = 'default';
        if (theme === 'default-dark') mermaidTheme = 'dark';
        if (theme === 'cyber-dark') mermaidTheme = 'dark';
        if (theme === 'cyber-light') mermaidTheme = 'neutral';

        mermaid.initialize({ 
            startOnLoad: true, 
            theme: mermaidTheme,
            securityLevel: 'loose',
            themeVariables: theme.startsWith('cyber') ? {
                primaryColor: theme.includes('dark') ? '#ffb400' : '#0077be',
                primaryTextColor: theme.includes('dark') ? '#dddddd' : '#102a43',
                primaryBorderColor: theme.includes('dark') ? '#ffb400' : '#0077be',
                lineColor: theme.includes('dark') ? '#ffb400' : '#0077be',
                secondaryColor: theme.includes('dark') ? '#0a0a0a' : '#f5f0e6',
                tertiaryColor: theme.includes('dark') ? '#1a1a1a' : '#e8e0d0',
            } : {}
        });
    }

    function initSynth() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight * 0.4;
        particles = [];
        const particleCount = 150;
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 2 + 1,
                speed: Math.random() * 0.15 + 0.05,
                offset: Math.random() * Math.PI * 2,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }

    function animateSynth() {
        if (!canvas || !ctx) return;
        const theme = html.getAttribute('data-theme');
        if (!theme || !theme.startsWith('cyber')) {
            animationFrame = null;
            return;
        }

        const color = theme.includes('dark') ? '255, 180, 0' : '0, 119, 190';
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(p => {
            p.x += p.speed;
            if (p.x > canvas.width) p.x = 0;
            const wave = Math.sin(p.x * 0.01 + p.offset) * 20;
            const finalY = (canvas.height / 2) + wave;
            
            ctx.fillStyle = `rgba(${color}, ${p.opacity})`;
            ctx.beginPath();
            ctx.arc(p.x, finalY + (p.y - canvas.height/2) * 0.5, p.size, 0, Math.PI * 2);
            ctx.fill();
            
            for (let j = particles.indexOf(p) + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const wave2 = Math.sin(p2.x * 0.01 + p2.offset) * 20;
                const y1 = finalY + (p.y - canvas.height/2) * 0.5;
                const y2 = (canvas.height / 2) + wave2 + (p2.y - canvas.height/2) * 0.5;
                const dx = p.x - p2.x;
                const dy = y1 - y2;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 100) {
                    ctx.strokeStyle = `rgba(${color}, ${0.3 * (1 - dist/100)})`;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(p.x, y1);
                    ctx.lineTo(p2.x, y2);
                    ctx.stroke();
                }
            }
        });
        animationFrame = requestAnimationFrame(animateSynth);
    }

    window.addEventListener('resize', () => {
        if (html.getAttribute('data-theme')?.startsWith('cyber')) {
            initSynth();
        }
    });
});
