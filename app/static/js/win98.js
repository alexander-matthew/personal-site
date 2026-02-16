/**
 * Windows 98 Theme JavaScript
 * Handles Start menu, clock, and other interactive elements
 */

(function() {
    'use strict';

    // ===== CLOCK =====
    function updateClock() {
        const clockEl = document.querySelector('.win98-clock');
        if (!clockEl) return;

        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';

        hours = hours % 12;
        hours = hours ? hours : 12; // 0 becomes 12

        clockEl.textContent = `${hours}:${minutes} ${ampm}`;
    }

    // Update clock every minute
    function initClock() {
        updateClock();
        setInterval(updateClock, 60000);
    }

    // ===== START MENU =====
    function initStartMenu() {
        const startBtn = document.querySelector('.win98-start-btn');
        const startMenu = document.querySelector('.win98-start-menu');

        if (!startBtn || !startMenu) return;

        // Toggle start menu on click
        startBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            startMenu.classList.toggle('open');
            startBtn.classList.toggle('active');
        });

        // Close start menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!startMenu.contains(e.target) && !startBtn.contains(e.target)) {
                startMenu.classList.remove('open');
                startBtn.classList.remove('active');
            }
        });

        // Close start menu when pressing Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                startMenu.classList.remove('open');
                startBtn.classList.remove('active');
            }
        });
    }

    // ===== DESKTOP ICON SELECTION =====
    function initDesktopIcons() {
        const icons = document.querySelectorAll('.win98-icon');
        let selectedIcon = null;

        icons.forEach(icon => {
            // Single click to select
            icon.addEventListener('click', function(e) {
                if (selectedIcon) {
                    selectedIcon.classList.remove('selected');
                }
                this.classList.add('selected');
                selectedIcon = this;
            });

            // Double click to open (navigate)
            icon.addEventListener('dblclick', function(e) {
                const href = this.getAttribute('href');
                if (href) {
                    window.location.href = href;
                }
            });
        });

        // Click on desktop to deselect
        const desktop = document.querySelector('.win98-desktop-area');
        if (desktop) {
            desktop.addEventListener('click', function(e) {
                if (e.target === this && selectedIcon) {
                    selectedIcon.classList.remove('selected');
                    selectedIcon = null;
                }
            });
        }
    }

    // ===== TABS =====
    function initTabs() {
        const tabContainers = document.querySelectorAll('.win98-tabs');

        tabContainers.forEach(container => {
            const buttons = container.querySelectorAll('.win98-tab-btn');
            const panels = container.querySelectorAll('.win98-tab-panel');

            buttons.forEach((btn, index) => {
                btn.addEventListener('click', function() {
                    // Remove active from all
                    buttons.forEach(b => b.classList.remove('active'));
                    panels.forEach(p => p.classList.remove('active'));

                    // Add active to clicked
                    this.classList.add('active');
                    if (panels[index]) {
                        panels[index].classList.add('active');
                    }
                });
            });
        });
    }

    // ===== WINDOW CONTROLS =====
    function initWindowControls() {
        // Close button - go back to desktop
        document.querySelectorAll('.win98-close-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                window.location.href = '/';
            });
        });

        // Minimize button - go back to desktop
        document.querySelectorAll('.win98-minimize-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                window.location.href = '/';
            });
        });

        // Maximize button - could toggle fullscreen or just be decorative
        document.querySelectorAll('.win98-maximize-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                // Decorative for now
            });
        });
    }

    // ===== DIALOGS (using safe DOM methods) =====
    function createDialogElement(title, message) {
        const overlay = document.createElement('div');
        overlay.className = 'win98-overlay';

        const dialog = document.createElement('div');
        dialog.className = 'win98-window win98-dialog';

        // Title bar
        const titleBar = document.createElement('div');
        titleBar.className = 'win98-title-bar';
        const titleText = document.createElement('span');
        titleText.className = 'win98-title-bar-text';
        titleText.textContent = title;
        titleBar.appendChild(titleText);

        // Content
        const content = document.createElement('div');
        content.className = 'win98-dialog-content';
        const textDiv = document.createElement('div');
        textDiv.className = 'win98-dialog-text';
        textDiv.textContent = message;
        content.appendChild(textDiv);

        // Buttons container
        const buttons = document.createElement('div');
        buttons.className = 'win98-dialog-buttons';

        dialog.appendChild(titleBar);
        dialog.appendChild(content);
        dialog.appendChild(buttons);

        return { overlay, dialog, buttons };
    }

    window.win98Alert = function(message, title = 'Alert') {
        const { overlay, dialog, buttons } = createDialogElement(title, message);

        const okBtn = document.createElement('button');
        okBtn.className = 'win98-btn win98-btn-default';
        okBtn.textContent = 'OK';
        okBtn.addEventListener('click', function() {
            overlay.remove();
            dialog.remove();
        });
        buttons.appendChild(okBtn);

        document.body.appendChild(overlay);
        document.body.appendChild(dialog);
        okBtn.focus();
    };

    window.win98Confirm = function(message, title = 'Confirm') {
        return new Promise((resolve) => {
            const { overlay, dialog, buttons } = createDialogElement(title, message);

            const cleanup = () => {
                overlay.remove();
                dialog.remove();
            };

            const okBtn = document.createElement('button');
            okBtn.className = 'win98-btn';
            okBtn.textContent = 'OK';
            okBtn.addEventListener('click', () => {
                cleanup();
                resolve(true);
            });

            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'win98-btn';
            cancelBtn.textContent = 'Cancel';
            cancelBtn.addEventListener('click', () => {
                cleanup();
                resolve(false);
            });

            buttons.appendChild(okBtn);
            buttons.appendChild(cancelBtn);

            document.body.appendChild(overlay);
            document.body.appendChild(dialog);
        });
    };

    // ===== INIT =====
    function init() {
        initClock();
        initStartMenu();
        initDesktopIcons();
        initTabs();
        initWindowControls();
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
