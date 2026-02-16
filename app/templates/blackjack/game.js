/* Blackjack Trainer - UI Controller
 * Wires BlackjackGame engine to the Win98-themed HTML interface.
 * All data rendered is from local game state constants - no user/external input.
 */
(function() {
    const game = new BlackjackGame({ numDecks: 6, startingBalance: 1000 });

    // --- DOM refs ---
    const $ = id => document.getElementById(id);
    const balanceEl       = $('balance');
    const currentBetEl    = $('current-bet');
    const betAmountEl     = $('bet-amount');
    const dealerCardsEl   = $('dealer-cards');
    const dealerTotalEl   = $('dealer-total');
    const resultMsg       = $('result-message');
    const playerHandsEl   = $('player-hands');
    const hitBtn          = $('hit-btn');
    const standBtn        = $('stand-btn');
    const doubleBtn       = $('double-btn');
    const splitBtn        = $('split-btn');
    const insuranceBtn    = $('insurance-btn');
    const dealBtn         = $('deal-btn');
    const clearBetBtn     = $('clear-bet');
    const bettingZone     = $('betting-zone');
    const actionButtons   = $('action-buttons');
    const hintCheckbox    = $('hint-mode');
    const strategyModal   = $('strategy-modal');
    const strategyChart   = $('strategy-chart');
    const mistakesPanel   = $('mistakes-panel');
    const mistakesList    = $('mistakes-list');

    // --- Stats ---
    let stats = loadStats();
    let pendingBet = 0;

    function defaultStats() {
        return {
            handsPlayed: 0, optimalPlays: 0, totalPlays: 0,
            startBalance: 1000,
            byType: { hard: { correct: 0, total: 0 }, soft: { correct: 0, total: 0 },
                      pair: { correct: 0, total: 0 }, double: { correct: 0, total: 0 } },
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
    const SUIT_COLORS  = { hearts: 'red', diamonds: 'red', clubs: 'black', spades: 'black' };

    function renderCard(card) {
        const el = document.createElement('div');
        el.className = 'card' + (card.faceDown ? ' face-down' : '');
        if (!card.faceDown) {
            const sym = SUIT_SYMBOLS[card.suit];
            const color = SUIT_COLORS[card.suit];
            // All values come from engine constants (RANKS, SUITS) - safe to use
            const topLeft = document.createElement('span');
            topLeft.style.cssText = 'position:absolute;top:4px;left:6px;font-size:14px;font-weight:bold;color:' + color;
            topLeft.textContent = card.rank;

            const topSuit = document.createElement('span');
            topSuit.style.cssText = 'position:absolute;top:16px;left:6px;font-size:12px;color:' + color;
            topSuit.textContent = sym;

            const bottomRight = document.createElement('span');
            bottomRight.style.cssText = 'position:absolute;bottom:4px;right:6px;font-size:14px;font-weight:bold;color:' + color + ';transform:rotate(180deg)';
            bottomRight.textContent = card.rank;

            const center = document.createElement('span');
            center.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:24px;color:' + color;
            center.textContent = sym;

            el.append(topLeft, topSuit, bottomRight, center);
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
            div.className = 'player-hand' + (i === game.currentHandIndex && game.isPlaying ? ' active-hand' : '');
            if (game.playerHands.length > 1) {
                div.style.border = i === game.currentHandIndex ? '2px solid #ffd700' : '1px solid transparent';
                div.style.padding = '4px';
                div.style.borderRadius = '4px';
            }
            const cardsDiv = document.createElement('div');
            cardsDiv.className = 'cards';
            cardsDiv.style.display = 'flex';
            cardsDiv.style.gap = '4px';
            hand.forEach(c => cardsDiv.appendChild(renderCard(c)));
            div.appendChild(cardsDiv);

            const totalDiv = document.createElement('div');
            totalDiv.className = 'hand-total';
            const total = calculateHand(hand);
            const soft = isSoft(hand);
            totalDiv.textContent = total + (soft ? ' (soft)' : '');
            div.appendChild(totalDiv);

            playerHandsEl.appendChild(div);
        });
    }

    function updateUI() {
        balanceEl.textContent = game.balance;
        currentBetEl.textContent = pendingBet;
        betAmountEl.textContent = '$' + pendingBet;
        dealBtn.disabled = pendingBet === 0;
        updateActionButtons();
        updateStats();
    }

    function updateActionButtons() {
        if (!game.isPlaying) {
            hitBtn.disabled = standBtn.disabled = doubleBtn.disabled = splitBtn.disabled = insuranceBtn.disabled = true;
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
        Object.values(btnMap).forEach(b => { b.style.fontWeight = ''; b.style.textDecoration = ''; });
        if (btnMap[optimal.action]) {
            btnMap[optimal.action].style.fontWeight = 'bold';
            btnMap[optimal.action].style.textDecoration = 'underline';
        }
    }

    function clearHints() {
        [hitBtn, standBtn, doubleBtn, splitBtn].forEach(b => {
            b.style.fontWeight = '';
            b.style.textDecoration = '';
        });
    }

    // --- Stats Display ---
    function updateStats() {
        $('hands-played').textContent = stats.handsPlayed;
        $('session-result').textContent = '$' + (game.balance - stats.startBalance);
        const pct = stats.totalPlays > 0 ? Math.round(stats.optimalPlays / stats.totalPlays * 100) : null;
        $('accuracy-pct').textContent = pct !== null ? pct + '%' : '--';

        ['hard', 'soft', 'pair', 'double'].forEach(type => {
            const s = stats.byType[type];
            const el = $(type + '-accuracy');
            el.textContent = s.total > 0 ? Math.round(s.correct / s.total * 100) + '%' : '--';
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

    function showFeedback(correct, optimalAction) {
        const toast = document.createElement('div');
        toast.className = 'feedback-toast ' + (correct ? 'correct' : 'incorrect');
        toast.textContent = correct ? 'Optimal!' : 'Optimal: ' + optimalAction.toUpperCase();
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 1200);
    }

    function showResult(text) {
        resultMsg.textContent = text;
        resultMsg.style.display = 'block';
    }
    function hideResult() {
        resultMsg.style.display = 'none';
    }

    // --- Game Flow ---
    function startDeal() {
        hideResult();
        clearHints();
        game.placeBet(pendingBet);
        const result = game.deal();
        if (!result.success) return;

        bettingZone.style.display = 'none';
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
        const dealerResult = game.playDealer();
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

            bettingZone.style.display = '';
            pendingBet = game.balance >= pendingBet ? pendingBet : 0;
            updateUI();
        }, 400);
    }

    // --- Chip / Betting ---
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            if (game.isPlaying) return;
            const val = parseInt(chip.dataset.value);
            if (pendingBet + val <= game.balance) {
                pendingBet += val;
                updateUI();
            }
        });
    });

    clearBetBtn.addEventListener('click', () => { pendingBet = 0; updateUI(); });
    dealBtn.addEventListener('click', startDeal);
    hitBtn.addEventListener('click', () => doAction('hit'));
    standBtn.addEventListener('click', () => doAction('stand'));
    doubleBtn.addEventListener('click', () => doAction('double'));
    splitBtn.addEventListener('click', () => doAction('split'));
    insuranceBtn.addEventListener('click', () => {
        const result = game.takeInsurance();
        if (result.success) updateUI();
    });

    // --- Strategy Chart ---
    $('show-strategy').addEventListener('click', () => {
        renderStrategyChart();
        strategyModal.style.display = 'flex';
        strategyModal.style.position = 'fixed';
        strategyModal.style.inset = '0';
        strategyModal.style.alignItems = 'center';
        strategyModal.style.justifyContent = 'center';
        strategyModal.style.zIndex = '9999';
    });
    $('close-strategy').addEventListener('click', () => { strategyModal.style.display = 'none'; });

    function renderStrategyChart() {
        const dealerCols = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'A'];
        const colors = { H: '#ddf', S: '#fdd', D: '#dfd', P: '#ffd', Ds: '#bfb' };

        // Build chart using DOM methods - all data from engine constants
        strategyChart.replaceChildren();

        function makeTable(title, chart, rows) {
            const wrapper = document.createElement('div');
            wrapper.style.marginBottom = '8px';
            const heading = document.createElement('b');
            heading.style.fontSize = '11px';
            heading.textContent = title;
            wrapper.appendChild(heading);

            const table = document.createElement('table');
            table.style.cssText = 'border-collapse:collapse;font-size:10px;width:100%';

            const headerRow = table.insertRow();
            const emptyTh = document.createElement('th');
            emptyTh.style.cssText = 'padding:2px 4px';
            headerRow.appendChild(emptyTh);
            dealerCols.forEach(d => {
                const th = document.createElement('th');
                th.style.cssText = 'padding:2px 4px;border:1px solid #888';
                th.textContent = d;
                headerRow.appendChild(th);
            });

            rows.forEach(r => {
                const tr = table.insertRow();
                const label = tr.insertCell();
                label.style.cssText = 'padding:2px 4px;border:1px solid #888;font-weight:bold';
                label.textContent = r;
                dealerCols.forEach(d => {
                    const td = tr.insertCell();
                    const a = chart[r] && chart[r][d] ? chart[r][d] : '';
                    td.style.cssText = 'padding:2px 4px;border:1px solid #888;text-align:center;background:' + (colors[a] || '#fff');
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

    // --- Mistakes Panel ---
    $('toggle-mistakes').addEventListener('click', () => {
        const vis = mistakesPanel.style.display === 'none';
        mistakesPanel.style.display = vis ? 'block' : 'none';
        if (vis) renderMistakes();
    });

    function renderMistakes() {
        mistakesList.replaceChildren();
        if (stats.mistakes.length === 0) {
            const msg = document.createElement('div');
            msg.style.cssText = 'font-size:11px;color:#666';
            msg.textContent = 'No mistakes yet!';
            mistakesList.appendChild(msg);
            return;
        }
        stats.mistakes.slice(0, 10).forEach(m => {
            const div = document.createElement('div');
            div.style.cssText = 'font-size:10px;margin-bottom:4px;padding:2px 4px;background:#fff;border:1px solid #ccc';
            div.textContent = m.hand + ' vs ' + m.dealer + ' (' + m.type + ') \u2014 played ' + m.played + ', optimal ' + m.optimal;
            mistakesList.appendChild(div);
        });
    }

    // --- Reset Stats ---
    $('reset-stats').addEventListener('click', () => {
        if (confirm('Reset all training stats?')) {
            stats = defaultStats();
            stats.startBalance = game.balance;
            saveStats();
            updateStats();
        }
    });

    // Init
    updateUI();
})();
