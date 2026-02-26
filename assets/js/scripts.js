import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

document.addEventListener('DOMContentLoaded', function() {
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

    const themeKey = 'cauldron_theme';
    const currentTheme = localStorage.getItem(themeKey) || 'default-light';

    applyTheme(currentTheme);

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
        html.setAttribute('data-theme', theme);

        if (theme.includes('dark')) {
            html.classList.add('dark-mode');
            body.classList.add('dark-mode');
        } else {
            html.classList.remove('dark-mode');
            body.classList.remove('dark-mode');
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

    if (currentTheme.startsWith('cyber')) {
        initCyberEffects();
    }
});

function initCyberEffects() {

}
