import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const body = document.body;
    
    // Initialize Mermaid
    mermaid.initialize({ 
        startOnLoad: true, 
        theme: localStorage.getItem('theme') === 'dark' ? 'dark' : 'default',
        securityLevel: 'loose',
    });

    // Check for saved theme preference
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
        if(darkModeToggle) darkModeToggle.checked = true;
    }

    // Handle theme change
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
                mermaid.initialize({ theme: 'dark' });
            } else {
                body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
                mermaid.initialize({ theme: 'default' });
            }
        });
    }
});
