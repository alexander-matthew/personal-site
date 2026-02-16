/* Blackjack Trainer - UI Controller
 * Wires BlackjackGame engine to the Win98 Solitaire-themed HTML interface.
 * All data rendered is from local game state constants - no user/external input.
 */
(function() {
    const game = new BlackjackGame({ numDecks: 6, startingBalance: 1000 });

    // --- DOM refs ---
    const $ = id => document.getElementById(id);

    // Toolbar buttons
    const hitBtn       = $('hit-btn');
    const standBtn     = $('stand-btn');
    const doubleBtn    = $('double-btn');
    const splitBtn     = $('split-btn');
    const insuranceBtn = $('insurance-btn');
    const dealBtn      = $('deal-btn');
    const clearBetBtn  = $('clear-bet');
    const hintCheckbox = $('hint-mode');

    // Felt areas
    const dealerCardsEl = $('dealer-cards');
    const dealerTotalEl = $('dealer-total');
    const playerHandsEl = $('player-hands');

    // Result dialog
    const resultDialog = $('result-dialog');
    const resultText   = $('result-text');
    const resultOkBtn  = $('result-ok');

    // Status bar
    const statusBalance  = $('status-balance');
    const statusBet      = $('status-bet');
    const statusFeedback = $('status-feedback');
    const statusAccuracy = $('status-accuracy');
    const statusHands    = $('status-hands');

    // Dialogs
    const statsDialog    = $('stats-dialog');
    const strategyDialog = $('strategy-dialog');
    const aboutDialog    = $('about-dialog');
    const strategyChart  = $('strategy-chart');
    const mistakesList   = $('mistakes-list');

    // Chip buttons
    const chipBtns = document.querySelectorAll('.bj-chip-btn');

    // --- Stats ---
    let stats = loadStats();
    let pendingBet = 0;
    let feedbackTimer = null;

    function defaultStats() {
        return {
            handsPlayed: 0, optimalPlays: 0, totalPlays: 0,
            startBalance: 1000,
            byType: {
                hard: { correct: 0, total: 0 }, soft: { correct: 0, total: 0 },
                pair: { correct: 0, total: 0 }, double: { correct: 0, total: 0 }
            },
            mistakes: []
        };
    }

    function loadStats() {
        try { return JSON.parse(localStorage.getItem('bj_stats')) || defaultStats(); }
        catch { return defaultStats(); }
    }

    function saveStats() { localStorage.setItem('bj_stats', JSON.stringify(stats)); }

    // --- Card Rendering ---
    const SUIT_SYMBOLS = { hearts: '\u2665', diamonds: '\u2666', clubs: '\u2663', spades: '\u2660' };
    const SUIT_COLORS  = { hearts: '#c00', diamonds: '#c00', clubs: '#000', spades: '#000' };

    function renderCard(card) {
        const el = document.createElement('div');
        el.className = 'card' + (card.faceDown ? ' face-down' : '');
        if (!card.faceDown) {
            const sym = SUIT_SYMBOLS[card.suit];
            const color = SUIT_COLORS[card.suit];

            const topRank = document.createElement('span');
            topRank.style.cssText = 'position:absolute;top:4px;left:5px;font-size:15px;font-weight:bold;color:' + color;
            topRank.textContent = card.rank;

            const topSuit = document.createElement('span');
            topSuit.style.cssText = 'position:absolute;top:19px;left:5px;font-size:12px;color:' + color;
            topSuit.textContent = sym;

            const bottomRank = document.createElement('span');
            bottomRank.style.cssText = 'position:absolute;bottom:4px;right:5px;font-size:15px;font-weight:bold;color:' + color + ';transform:rotate(180deg)';
            bottomRank.textContent = card.rank;

            const center = document.createElement('span');
            center.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:26px;color:' + color;
            center.textContent = sym;

            el.append(topRank, topSuit, bottomRank, center);
        }
        return el;
    }

    function renderHands() {
        // Dealer
        dealerCardsEl.replaceChildren();
        game.dealerHand.forEach(c => dealerCardsEl.appendChild(renderCard(c)));
        const dealerVis = calculateHand(game.dealerHand, false);
        const allRevealed = game.dealerHand.every(c => !c.faceDown);
        dealerTotalEl.textContent = allRevealed
            ? calculateHand(game.dealerHand, true)
            : (dealerVis > 0 ? dealerVis : '');

        // Player hands
        playerHandsEl.replaceChildren();
        game.playerHands.forEach((hand, i) => {
            const div = document.createElement('div');
            div.className = 'bj-player-hand' + (i === game.currentHandIndex && game.isPlaying ? ' active-hand' : '');

            const cardsDiv = document.createElement('div');
            cardsDiv.className = 'bj-cards';
            hand.forEach(c => cardsDiv.appendChild(renderCard(c)));
            div.appendChild(cardsDiv);

            const totalDiv = document.createElement('div');
            totalDiv.className = 'bj-hand-total';
            const total = calculateHand(hand);
            const soft = isSoft(hand);
            totalDiv.textContent = total + (soft ? ' (soft)' : '');
            if (total > 21) totalDiv.classList.add('bust');
            div.appendChild(totalDiv);

            playerHandsEl.appendChild(div);
        });
    }

    // --- UI State ---
    function updateUI() {
        // Status bar
        statusBalance.textContent = 'Balance: $' + game.balance;
        statusBet.textContent = 'Bet: $' + pendingBet;

        // Toolbar state
        dealBtn.disabled = pendingBet === 0 || game.isPlaying;

        // Chip buttons: disabled during play
        chipBtns.forEach(btn => { btn.disabled = game.isPlaying; });
        clearBetBtn.disabled = game.isPlaying || pendingBet === 0;

        updateActionButtons();
        updateStatusBar();
    }

    function updateActionButtons() {
        if (!game.isPlaying) {
            hitBtn.disabled = standBtn.disabled = doubleBtn.disabled = splitBtn.disabled = insuranceBtn.disabled = true;
            clearHints();
            return;
        }
        hitBtn.disabled = false;
        standBtn.disabled = false;
        doubleBtn.disabled = !game.canDouble();
        splitBtn.disabled = !game.canSplit();
        insuranceBtn.disabled = !game.canTakeInsurance();

        if (hintCheckbox.checked) showHint();
    }

    function showHint() {
        const hand = game.getCurrentHand();
        if (!hand || hand.length === 0) return;
        const upcard = game.dealerHand[0];
        const optimal = getOptimalAction(hand, upcard, game.canDouble(), game.canSplit());
        const btnMap = { hit: hitBtn, stand: standBtn, double: doubleBtn, split: splitBtn };
        Object.values(btnMap).forEach(b => b.classList.remove('hint-active'));
        if (btnMap[optimal.action]) {
            btnMap[optimal.action].classList.add('hint-active');
        }
    }

    function clearHints() {
        [hitBtn, standBtn, doubleBtn, splitBtn].forEach(b => b.classList.remove('hint-active'));
    }

    // --- Status Bar ---
    function updateStatusBar() {
        const pct = stats.totalPlays > 0 ? Math.round(stats.optimalPlays / stats.totalPlays * 100) : null;
        statusAccuracy.textContent = (pct !== null ? pct + '%' : '--') + ' Optimal';
        statusHands.textContent = stats.handsPlayed + ' hands';
    }

    function showFeedback(correct, optimalAction) {
        if (feedbackTimer) clearTimeout(feedbackTimer);
        statusFeedback.textContent = correct ? 'Optimal play!' : 'Optimal: ' + optimalAction.toUpperCase();
        statusFeedback.className = 'win98-status-section bj-status-feedback ' + (correct ? 'correct' : 'incorrect');
        feedbackTimer = setTimeout(() => {
            statusFeedback.textContent = '';
            statusFeedback.className = 'win98-status-section bj-status-feedback';
        }, 3000);
    }

    // --- Stats ---
    function updateStatsDialog() {
        $('stat-hands').textContent = stats.handsPlayed;
        $('stat-pl').textContent = '$' + (game.balance - stats.startBalance);
        const pct = stats.totalPlays > 0 ? Math.round(stats.optimalPlays / stats.totalPlays * 100) : null;
        $('stat-accuracy').textContent = pct !== null ? pct + '%' : '--';

        ['hard', 'soft', 'pair', 'double'].forEach(type => {
            const s = stats.byType[type];
            $('stat-' + type).textContent = s.total > 0 ? Math.round(s.correct / s.total * 100) + '%' : '--';
        });

        renderMistakes();
    }

    function renderMistakes() {
        mistakesList.replaceChildren();
        if (stats.mistakes.length === 0) {
            const msg = document.createElement('div');
            msg.className = 'bj-no-mistakes';
            msg.textContent = 'No mistakes yet!';
            mistakesList.appendChild(msg);
            return;
        }
        stats.mistakes.slice(0, 15).forEach(m => {
            const div = document.createElement('div');
            div.className = 'bj-mistake-item';
            div.textContent = m.hand + ' vs ' + m.dealer + ' (' + m.type + ') \u2014 played ' + m.played + ', optimal ' + m.optimal;
            mistakesList.appendChild(div);
        });
    }

    function recordPlay(action) {
        const hand = game.getCurrentHand();
        if (!hand || hand.length === 0) return;
        const upcard = game.dealerHand[0];
        const optimal = getOptimalAction(hand, upcard, game.canDouble(), game.canSplit());
        const isCorrect = action === optimal.action;

        stats.totalPlays++;
        if (isCorrect) stats.optimalPlays++;

        const typeKey = optimal.handType === 'double' ? 'double' : optimal.handType;
        if (stats.byType[typeKey]) {
            stats.byType[typeKey].total++;
            if (isCorrect) stats.byType[typeKey].correct++;
        }

        if (!isCorrect) {
            stats.mistakes.unshift({
                hand: hand.map(c => c.rank + SUIT_SYMBOLS[c.suit]).join(' '),
                dealer: upcard.rank + SUIT_SYMBOLS[upcard.suit],
                played: action,
                optimal: optimal.action,
                type: optimal.handType
            });
            if (stats.mistakes.length > 20) stats.mistakes.length = 20;
        }

        saveStats();
        showFeedback(isCorrect, optimal.action);
    }

    // --- Result ---
    function showResult(text) {
        resultText.textContent = text;
        resultDialog.style.display = '';
    }

    function hideResult() {
        resultDialog.style.display = 'none';
    }

    // --- Game Flow ---
    function startDeal() {
        if (pendingBet === 0 || game.isPlaying) return;
        hideResult();
        clearHints();
        game.placeBet(pendingBet);
        const result = game.deal();
        if (!result.success) return;

        renderHands();

        if (result.playerBlackjack || result.dealerBlackjack) {
            finishRound();
            return;
        }

        updateUI();
    }

    function doAction(action) {
        recordPlay(action);
        clearHints();

        let result;
        switch (action) {
            case 'hit':    result = game.hit(); break;
            case 'stand':  result = game.stand(); break;
            case 'double': result = game.double(); break;
            case 'split':  result = game.split(); break;
            default: return;
        }

        if (!result.success) return;

        renderHands();

        if (result.handComplete) {
            if (!game.moveToNextHand()) {
                finishRound();
                return;
            }
            renderHands();
        }

        updateUI();
    }

    function finishRound() {
        game.playDealer();
        renderHands();

        setTimeout(() => {
            const resolution = game.resolveHands();
            renderHands();

            const messages = resolution.results.map(r => {
                const prefix = resolution.results.length > 1 ? 'Hand ' + (r.handIndex + 1) + ': ' : '';
                switch (r.result) {
                    case 'blackjack': return prefix + 'Blackjack! +$' + (r.payout - r.bet);
                    case 'player':    return prefix + 'Win! +$' + (r.payout - r.bet);
                    case 'push':      return prefix + 'Push';
                    case 'dealer':    return prefix + 'Dealer wins -$' + r.bet;
                    default:          return prefix + r.result;
                }
            });

            showResult(messages.join(' | '));
            stats.handsPlayed++;
            saveStats();

            pendingBet = game.balance >= pendingBet ? pendingBet : 0;
            updateUI();
        }, 400);
    }

    // --- Toolbar Button Handlers ---
    chipBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (game.isPlaying) return;
            hideResult();
            const val = parseInt(btn.dataset.value);
            if (pendingBet + val <= game.balance) {
                pendingBet += val;
                updateUI();
            }
        });
    });

    clearBetBtn.addEventListener('click', () => {
        hideResult();
        pendingBet = 0;
        updateUI();
    });

    dealBtn.addEventListener('click', startDeal);
    hitBtn.addEventListener('click', () => doAction('hit'));
    standBtn.addEventListener('click', () => doAction('stand'));
    doubleBtn.addEventListener('click', () => doAction('double'));
    splitBtn.addEventListener('click', () => doAction('split'));
    insuranceBtn.addEventListener('click', () => {
        const result = game.takeInsurance();
        if (result.success) updateUI();
    });

    resultOkBtn.addEventListener('click', hideResult);

    // --- Menu System ---
    const menuMap = { game: $('menu-game'), help: $('menu-help') };
    let openMenu = null;

    document.querySelectorAll('[data-menu]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const menuId = trigger.dataset.menu;
            const dropdown = menuMap[menuId];
            if (openMenu === dropdown) {
                closeMenus();
            } else {
                closeMenus();
                dropdown.classList.add('open');
                openMenu = dropdown;
            }
        });
    });

    document.querySelectorAll('.bj-dropdown-item').forEach(item => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;
            closeMenus();
            handleMenuAction(action);
        });
    });

    document.addEventListener('click', closeMenus);

    function closeMenus() {
        Object.values(menuMap).forEach(d => d.classList.remove('open'));
        openMenu = null;
    }

    function handleMenuAction(action) {
        switch (action) {
            case 'deal':
                if (pendingBet > 0 && !game.isPlaying) startDeal();
                break;
            case 'stats':
                updateStatsDialog();
                statsDialog.style.display = '';
                break;
            case 'strategy':
                renderStrategyChart();
                strategyDialog.style.display = '';
                break;
            case 'reset':
                if (confirm('Reset all training stats?')) {
                    stats = defaultStats();
                    stats.startBalance = game.balance;
                    saveStats();
                    updateStatusBar();
                }
                break;
            case 'about':
                aboutDialog.style.display = '';
                break;
        }
    }

    // --- Dialog Close ---
    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const dialogId = btn.dataset.close;
            $(dialogId).style.display = 'none';
        });
    });

    // Close dialogs when clicking overlay background
    document.querySelectorAll('.bj-dialog-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.style.display = 'none';
        });
    });

    // --- Strategy Chart ---
    function renderStrategyChart() {
        const dealerCols = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'A'];
        const colors = { H: '#ddf', S: '#fdd', D: '#dfd', P: '#ffd', Ds: '#bfb' };

        strategyChart.replaceChildren();

        function makeTable(title, chart, rows) {
            const wrapper = document.createElement('div');
            wrapper.style.marginBottom = '8px';
            const heading = document.createElement('b');
            heading.style.fontSize = '11px';
            heading.textContent = title;
            wrapper.appendChild(heading);

            const table = document.createElement('table');
            const headerRow = table.insertRow();
            const emptyTh = document.createElement('th');
            emptyTh.style.padding = '2px 4px';
            headerRow.appendChild(emptyTh);
            dealerCols.forEach(d => {
                const th = document.createElement('th');
                th.textContent = d;
                headerRow.appendChild(th);
            });

            rows.forEach(r => {
                const tr = table.insertRow();
                const label = tr.insertCell();
                label.textContent = r;
                dealerCols.forEach(d => {
                    const td = tr.insertCell();
                    const a = chart[r] && chart[r][d] ? chart[r][d] : '';
                    td.style.background = colors[a] || '#fff';
                    td.textContent = a;
                });
            });

            wrapper.appendChild(table);
            return wrapper;
        }

        strategyChart.appendChild(makeTable('Hard Totals', HARD_STRATEGY, [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]));
        strategyChart.appendChild(makeTable('Soft Totals', SOFT_STRATEGY, [13,14,15,16,17,18,19,20]));
        strategyChart.appendChild(makeTable('Pairs', PAIR_STRATEGY, [2,3,4,5,6,7,8,9,10,'A']));

        const legend = document.createElement('div');
        legend.style.cssText = 'font-size:10px;margin-top:4px';
        legend.textContent = 'H=Hit S=Stand D=Double P=Split Ds=Double/Stand';
        strategyChart.appendChild(legend);
    }

    // --- Init ---
    updateUI();
})();
