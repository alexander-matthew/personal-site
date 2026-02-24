/* Palantir Theme - Interactivity */
(function () {
    'use strict';

    // === Sidebar Toggle (mobile) ===
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (hamburger && sidebar && overlay) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        });

        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        });
    }

    // === Active Link Highlighting ===
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav a[data-path]');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('data-path');
        if (path === linkPath || (linkPath !== '/' && path.startsWith(linkPath))) {
            link.classList.add('active');
        }
    });

    // === Tab System ===
    document.querySelectorAll('.tabs').forEach(tabContainer => {
        const buttons = tabContainer.querySelectorAll('.tab-btn');
        const panelContainer = tabContainer.nextElementSibling;
        if (!panelContainer) return;
        const panels = panelContainer.querySelectorAll('.tab-panel');

        buttons.forEach((btn, index) => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                if (panels[index]) panels[index].classList.add('active');
            });
        });
    });

    // === Dialog System ===
    window.showDialog = function (title, message, onClose) {
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';
        overlay.innerHTML = `
            <div class="dialog" style="min-width: 320px">
                <div class="dialog-header">
                    <span>${title}</span>
                    <button class="dialog-close">&times;</button>
                </div>
                <div class="dialog-content">
                    <p>${message}</p>
                </div>
                <div class="dialog-footer">
                    <button class="btn btn-primary dialog-ok">OK</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const close = () => {
            overlay.remove();
            if (onClose) onClose();
        };

        overlay.querySelector('.dialog-close').addEventListener('click', close);
        overlay.querySelector('.dialog-ok').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
    };

    window.showConfirm = function (title, message, onConfirm, onCancel) {
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';
        overlay.innerHTML = `
            <div class="dialog" style="min-width: 320px">
                <div class="dialog-header">
                    <span>${title}</span>
                    <button class="dialog-close">&times;</button>
                </div>
                <div class="dialog-content">
                    <p>${message}</p>
                </div>
                <div class="dialog-footer">
                    <button class="btn dialog-cancel">Cancel</button>
                    <button class="btn btn-primary dialog-confirm">Confirm</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const close = (confirmed) => {
            overlay.remove();
            if (confirmed && onConfirm) onConfirm();
            if (!confirmed && onCancel) onCancel();
        };

        overlay.querySelector('.dialog-close').addEventListener('click', () => close(false));
        overlay.querySelector('.dialog-cancel').addEventListener('click', () => close(false));
        overlay.querySelector('.dialog-confirm').addEventListener('click', () => close(true));
    };
})();
