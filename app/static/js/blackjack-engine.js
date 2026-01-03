/**
 * Blackjack Game Engine
 * Pure game logic separated from UI for testability
 */

const SUITS = ['hearts', 'diamonds', 'clubs', 'spades'];
const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
const VALUES = { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11 };

// ===== Basic Strategy Charts =====
const HARD_STRATEGY = {
    5:  { 2: 'H', 3: 'H', 4: 'H', 5: 'H', 6: 'H', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    6:  { 2: 'H', 3: 'H', 4: 'H', 5: 'H', 6: 'H', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    7:  { 2: 'H', 3: 'H', 4: 'H', 5: 'H', 6: 'H', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    8:  { 2: 'H', 3: 'H', 4: 'H', 5: 'H', 6: 'H', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    9:  { 2: 'H', 3: 'D', 4: 'D', 5: 'D', 6: 'D', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    10: { 2: 'D', 3: 'D', 4: 'D', 5: 'D', 6: 'D', 7: 'D', 8: 'D', 9: 'D', 10: 'H', A: 'H' },
    11: { 2: 'D', 3: 'D', 4: 'D', 5: 'D', 6: 'D', 7: 'D', 8: 'D', 9: 'D', 10: 'D', A: 'D' },
    12: { 2: 'H', 3: 'H', 4: 'S', 5: 'S', 6: 'S', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    13: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    14: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    15: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    16: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    17: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' },
    18: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' },
    19: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' },
    20: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' },
    21: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' }
};

const SOFT_STRATEGY = {
    13: { 2: 'H', 3: 'H', 4: 'H', 5: 'D', 6: 'D', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    14: { 2: 'H', 3: 'H', 4: 'H', 5: 'D', 6: 'D', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    15: { 2: 'H', 3: 'H', 4: 'D', 5: 'D', 6: 'D', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    16: { 2: 'H', 3: 'H', 4: 'D', 5: 'D', 6: 'D', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    17: { 2: 'H', 3: 'D', 4: 'D', 5: 'D', 6: 'D', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    18: { 2: 'Ds', 3: 'Ds', 4: 'Ds', 5: 'Ds', 6: 'Ds', 7: 'S', 8: 'S', 9: 'H', 10: 'H', A: 'H' },
    19: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'Ds', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' },
    20: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' }
};

const PAIR_STRATEGY = {
    2:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'P', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    3:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'P', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    4:  { 2: 'H', 3: 'H', 4: 'H', 5: 'P', 6: 'P', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    5:  { 2: 'D', 3: 'D', 4: 'D', 5: 'D', 6: 'D', 7: 'D', 8: 'D', 9: 'D', 10: 'H', A: 'H' },
    6:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'H', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    7:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'P', 8: 'H', 9: 'H', 10: 'H', A: 'H' },
    8:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'P', 8: 'P', 9: 'P', 10: 'P', A: 'P' },
    9:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'S', 8: 'P', 9: 'P', 10: 'S', A: 'S' },
    10: { 2: 'S', 3: 'S', 4: 'S', 5: 'S', 6: 'S', 7: 'S', 8: 'S', 9: 'S', 10: 'S', A: 'S' },
    A:  { 2: 'P', 3: 'P', 4: 'P', 5: 'P', 6: 'P', 7: 'P', 8: 'P', 9: 'P', 10: 'P', A: 'P' }
};

// ===== Expected Value Tables (approximate EV per $1 bet) =====
// These values represent the EV of the optimal action for each hand
const HARD_EV = {
    5:  { 2: -0.12, 3: -0.09, 4: -0.06, 5: -0.02, 6: 0.01, 7: -0.11, 8: -0.15, 9: -0.18, 10: -0.23, A: -0.35 },
    6:  { 2: -0.14, 3: -0.11, 4: -0.08, 5: -0.04, 6: -0.01, 7: -0.13, 8: -0.17, 9: -0.20, 10: -0.24, A: -0.36 },
    7:  { 2: -0.11, 3: -0.08, 4: -0.05, 5: -0.01, 6: 0.02, 7: -0.08, 8: -0.12, 9: -0.17, 10: -0.21, A: -0.34 },
    8:  { 2: -0.05, 3: -0.01, 4: 0.02, 5: 0.06, 6: 0.09, 7: -0.01, 8: -0.05, 9: -0.11, 10: -0.17, A: -0.30 },
    9:  { 2: 0.07, 3: 0.11, 4: 0.15, 5: 0.19, 6: 0.23, 7: 0.08, 8: 0.03, 9: -0.04, 10: -0.11, A: -0.22 },
    10: { 2: 0.26, 3: 0.30, 4: 0.34, 5: 0.38, 6: 0.42, 7: 0.26, 8: 0.18, 9: 0.09, 10: -0.03, A: -0.14 },
    11: { 2: 0.34, 3: 0.38, 4: 0.42, 5: 0.46, 6: 0.50, 7: 0.34, 8: 0.26, 9: 0.17, 10: 0.05, A: 0.05 },
    12: { 2: -0.25, 3: -0.23, 4: -0.21, 5: -0.17, 6: -0.15, 7: -0.21, 8: -0.24, 9: -0.27, 10: -0.30, A: -0.40 },
    13: { 2: -0.29, 3: -0.25, 4: -0.21, 5: -0.17, 6: -0.15, 7: -0.27, 8: -0.30, 9: -0.32, 10: -0.34, A: -0.43 },
    14: { 2: -0.29, 3: -0.25, 4: -0.21, 5: -0.17, 6: -0.15, 7: -0.33, 8: -0.36, 9: -0.38, 10: -0.40, A: -0.47 },
    15: { 2: -0.29, 3: -0.25, 4: -0.21, 5: -0.17, 6: -0.15, 7: -0.39, 8: -0.42, 9: -0.44, 10: -0.46, A: -0.52 },
    16: { 2: -0.29, 3: -0.25, 4: -0.21, 5: -0.17, 6: -0.15, 7: -0.42, 8: -0.45, 9: -0.48, 10: -0.50, A: -0.54 },
    17: { 2: -0.15, 3: -0.12, 4: -0.08, 5: -0.04, 6: 0.01, 7: -0.11, 8: -0.18, 9: -0.24, 10: -0.42, A: -0.48 },
    18: { 2: 0.12, 3: 0.15, 4: 0.18, 5: 0.22, 6: 0.28, 7: 0.40, 8: 0.11, 9: -0.18, 10: -0.24, A: -0.10 },
    19: { 2: 0.38, 3: 0.40, 4: 0.42, 5: 0.44, 6: 0.46, 7: 0.62, 8: 0.59, 9: 0.29, 10: -0.04, A: 0.07 },
    20: { 2: 0.64, 3: 0.65, 4: 0.67, 5: 0.68, 6: 0.70, 7: 0.77, 8: 0.79, 9: 0.76, 10: 0.55, A: 0.37 },
    21: { 2: 0.88, 3: 0.89, 4: 0.89, 5: 0.90, 6: 0.90, 7: 0.93, 8: 0.95, 9: 0.96, 10: 0.92, A: 0.84 }
};

const SOFT_EV = {
    13: { 2: -0.02, 3: 0.02, 4: 0.06, 5: 0.11, 6: 0.18, 7: 0.01, 8: -0.04, 9: -0.11, 10: -0.19, A: -0.24 },
    14: { 2: 0.01, 3: 0.05, 4: 0.10, 5: 0.15, 6: 0.22, 7: 0.04, 8: -0.01, 9: -0.08, 10: -0.16, A: -0.21 },
    15: { 2: 0.04, 3: 0.09, 4: 0.14, 5: 0.19, 6: 0.26, 7: 0.07, 8: 0.02, 9: -0.05, 10: -0.13, A: -0.18 },
    16: { 2: 0.07, 3: 0.12, 4: 0.17, 5: 0.23, 6: 0.30, 7: 0.10, 8: 0.05, 9: -0.02, 10: -0.10, A: -0.15 },
    17: { 2: 0.10, 3: 0.15, 4: 0.21, 5: 0.27, 6: 0.34, 7: 0.08, 8: 0.02, 9: -0.06, 10: -0.14, A: -0.19 },
    18: { 2: 0.12, 3: 0.15, 4: 0.18, 5: 0.22, 6: 0.28, 7: 0.40, 8: 0.11, 9: -0.10, 10: -0.24, A: -0.10 },
    19: { 2: 0.38, 3: 0.40, 4: 0.42, 5: 0.44, 6: 0.46, 7: 0.62, 8: 0.59, 9: 0.29, 10: -0.04, A: 0.07 },
    20: { 2: 0.64, 3: 0.65, 4: 0.67, 5: 0.68, 6: 0.70, 7: 0.77, 8: 0.79, 9: 0.76, 10: 0.55, A: 0.37 }
};

/**
 * Get the expected value for a hand situation
 * @param {number} total - Hand total
 * @param {string|number} dealerUpcard - Dealer upcard value or 'A'
 * @param {boolean} isSoftHand - Whether the hand is soft
 * @returns {number} Expected value (approximate)
 */
function getHandEV(total, dealerUpcard, isSoftHand) {
    const evTable = isSoftHand ? SOFT_EV : HARD_EV;
    const evRow = evTable[total];
    if (!evRow) return 0;
    return evRow[dealerUpcard] || 0;
}

/**
 * Create a card object
 */
function createCard(rank, suit, faceDown = false) {
    return {
        rank,
        suit,
        value: VALUES[rank],
        faceDown
    };
}

/**
 * Create a fresh deck (or multi-deck shoe)
 */
function createDeck(numDecks = 6) {
    const deck = [];
    for (let d = 0; d < numDecks; d++) {
        for (const suit of SUITS) {
            for (const rank of RANKS) {
                deck.push(createCard(rank, suit));
            }
        }
    }
    return deck;
}

/**
 * Fisher-Yates shuffle
 */
function shuffle(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

/**
 * Calculate the total value of a hand
 * @param {Array} hand - Array of card objects
 * @param {boolean} countHidden - Whether to count face-down cards
 */
function calculateHand(hand, countHidden = false) {
    let total = 0;
    let aces = 0;

    for (const card of hand) {
        if (card.faceDown && !countHidden) continue;
        total += card.value;
        if (card.rank === 'A') aces++;
    }

    // Adjust for aces (count as 1 instead of 11 if needed)
    while (total > 21 && aces > 0) {
        total -= 10;
        aces--;
    }

    return total;
}

/**
 * Check if a hand is soft (has an ace counting as 11)
 */
function isSoft(hand) {
    let total = 0;
    let aces = 0;

    for (const card of hand) {
        if (card.faceDown) continue;
        total += card.value;
        if (card.rank === 'A') aces++;
    }

    while (total > 21 && aces > 0) {
        total -= 10;
        aces--;
    }

    // Calculate hard total (all aces as 1)
    let hardTotal = 0;
    for (const card of hand) {
        if (card.faceDown) continue;
        hardTotal += card.rank === 'A' ? 1 : card.value;
    }

    return total <= 21 && total !== hardTotal;
}

/**
 * Check if a hand is a pair (two cards of same rank)
 */
function isPair(hand) {
    return hand.length === 2 && hand[0].rank === hand[1].rank;
}

/**
 * Check if a hand is a blackjack (21 with 2 cards)
 */
function isBlackjack(hand) {
    if (hand.length !== 2) return false;
    const total = calculateHand(hand, true); // Count all cards
    return total === 21;
}

/**
 * Check if a hand is busted
 */
function isBusted(hand) {
    return calculateHand(hand) > 21;
}

/**
 * Get the dealer's upcard value for strategy lookup
 */
function getDealerUpcardKey(upcard) {
    if (upcard.rank === 'A') return 'A';
    return upcard.value;
}

/**
 * Get the optimal action for a given hand and dealer upcard
 * @param {Array} hand - Player's hand
 * @param {Object} dealerUpcard - Dealer's face-up card
 * @param {boolean} canDouble - Whether doubling is allowed
 * @param {boolean} canSplit - Whether splitting is allowed
 * @returns {Object} - { action: string, handType: string }
 */
function getOptimalAction(hand, dealerUpcard, canDouble = true, canSplit = true) {
    const total = calculateHand(hand);
    const soft = isSoft(hand);
    const pair = isPair(hand);
    const dealerKey = getDealerUpcardKey(dealerUpcard);

    let action;
    let handType;

    // Check pairs first
    if (pair && canSplit) {
        const pairKey = hand[0].rank === 'A' ? 'A' :
                       (hand[0].rank === 'J' || hand[0].rank === 'Q' || hand[0].rank === 'K' ? 10 :
                        parseInt(hand[0].rank) || hand[0].value);
        action = PAIR_STRATEGY[pairKey]?.[dealerKey];
        handType = 'pair';

        if (action === 'P') {
            return { action: 'split', handType };
        }
        // If not splitting, fall through to soft/hard strategy
    }

    // Check soft hands
    if (soft && SOFT_STRATEGY[total]) {
        action = SOFT_STRATEGY[total][dealerKey];
        handType = 'soft';
    } else {
        // Hard hands
        const hardTotal = Math.min(21, Math.max(5, total));
        action = HARD_STRATEGY[hardTotal]?.[dealerKey] || 'S';
        handType = 'hard';
    }

    // Convert action codes to readable actions
    if (action === 'H') return { action: 'hit', handType };
    if (action === 'S') return { action: 'stand', handType };
    if (action === 'D') {
        return { action: canDouble ? 'double' : 'hit', handType: 'double' };
    }
    if (action === 'Ds') {
        return { action: canDouble ? 'double' : 'stand', handType: 'double' };
    }
    if (action === 'P') return { action: 'split', handType: 'pair' };

    return { action: 'stand', handType };
}

/**
 * Determine the winner between player and dealer
 * @returns {string} - 'player', 'dealer', 'push', or 'blackjack'
 */
function determineWinner(playerHand, dealerHand, playerHasBlackjack = false, dealerHasBlackjack = false) {
    const playerTotal = calculateHand(playerHand, true);
    const dealerTotal = calculateHand(dealerHand, true);
    const playerBusted = playerTotal > 21;
    const dealerBusted = dealerTotal > 21;

    // Check blackjacks
    if (playerHasBlackjack && dealerHasBlackjack) return 'push';
    if (playerHasBlackjack) return 'blackjack';
    if (dealerHasBlackjack) return 'dealer';

    // Check busts
    if (playerBusted) return 'dealer';
    if (dealerBusted) return 'player';

    // Compare totals
    if (playerTotal > dealerTotal) return 'player';
    if (dealerTotal > playerTotal) return 'dealer';
    return 'push';
}

/**
 * Calculate payout multiplier
 */
function getPayoutMultiplier(result) {
    switch (result) {
        case 'blackjack': return 2.5; // 3:2 payout (original bet + 1.5x)
        case 'player': return 2;      // 1:1 payout (original bet + 1x)
        case 'push': return 1;        // Return original bet
        case 'dealer': return 0;      // Lose bet
        default: return 0;
    }
}

/**
 * Game state manager
 */
class BlackjackGame {
    constructor(options = {}) {
        this.numDecks = options.numDecks || 6;
        this.startingBalance = options.startingBalance || 1000;
        this.reset();
    }

    reset() {
        this.deck = shuffle(createDeck(this.numDecks));
        this.balance = this.startingBalance;
        this.playerHands = [];
        this.dealerHand = [];
        this.currentHandIndex = 0;
        this.handBets = [];
        this.currentBet = 0;
        this.insuranceBet = 0;
        this.isPlaying = false;
        this.lastBet = 0;
    }

    dealCard(faceDown = false) {
        // Reshuffle if less than 25% of cards remain
        if (this.deck.length < (52 * this.numDecks * 0.25)) {
            this.deck = shuffle(createDeck(this.numDecks));
        }
        const card = this.deck.pop();
        card.faceDown = faceDown;
        return card;
    }

    placeBet(amount) {
        if (this.isPlaying) return { success: false, error: 'Game in progress' };
        if (amount > this.balance) return { success: false, error: 'Insufficient balance' };
        if (amount <= 0) return { success: false, error: 'Invalid bet amount' };

        this.currentBet = amount;
        return { success: true };
    }

    deal() {
        if (this.currentBet === 0) {
            // Try to re-up with last bet
            if (this.lastBet > 0 && this.lastBet <= this.balance) {
                this.currentBet = this.lastBet;
            } else {
                return { success: false, error: 'No bet placed' };
            }
        }

        this.lastBet = this.currentBet;
        this.balance -= this.currentBet;
        this.isPlaying = true;
        this.playerHands = [[]];
        this.dealerHand = [];
        this.handBets = [this.currentBet];
        this.currentHandIndex = 0;
        this.insuranceBet = 0;

        // Deal cards: player, dealer up, player, dealer hole
        this.playerHands[0].push(this.dealCard());
        this.dealerHand.push(this.dealCard()); // Upcard
        this.playerHands[0].push(this.dealCard());
        this.dealerHand.push(this.dealCard(true)); // Hole card

        const playerBJ = isBlackjack(this.playerHands[0]);
        const dealerBJ = isBlackjack(this.dealerHand);

        return {
            success: true,
            playerHand: [...this.playerHands[0]],
            dealerHand: [...this.dealerHand],
            playerBlackjack: playerBJ,
            dealerBlackjack: dealerBJ,
            dealerShowsAce: this.dealerHand[0].rank === 'A'
        };
    }

    hit() {
        if (!this.isPlaying) return { success: false, error: 'No game in progress' };

        const hand = this.playerHands[this.currentHandIndex];
        const newCard = this.dealCard();
        hand.push(newCard);

        const total = calculateHand(hand);
        const busted = total > 21;

        return {
            success: true,
            card: newCard,
            total,
            busted,
            handComplete: busted || total === 21
        };
    }

    stand() {
        if (!this.isPlaying) return { success: false, error: 'No game in progress' };
        return { success: true, handComplete: true };
    }

    double() {
        if (!this.isPlaying) return { success: false, error: 'No game in progress' };

        const hand = this.playerHands[this.currentHandIndex];
        if (hand.length !== 2) return { success: false, error: 'Can only double on first two cards' };

        const additionalBet = this.handBets[this.currentHandIndex];
        if (additionalBet > this.balance) return { success: false, error: 'Insufficient balance' };

        this.balance -= additionalBet;
        this.handBets[this.currentHandIndex] *= 2;

        const newCard = this.dealCard();
        hand.push(newCard);

        const total = calculateHand(hand);

        return {
            success: true,
            card: newCard,
            total,
            busted: total > 21,
            handComplete: true
        };
    }

    split() {
        if (!this.isPlaying) return { success: false, error: 'No game in progress' };

        const hand = this.playerHands[this.currentHandIndex];
        if (!isPair(hand)) return { success: false, error: 'Cannot split - not a pair' };
        if (this.playerHands.length >= 4) return { success: false, error: 'Maximum splits reached' };

        const additionalBet = this.handBets[this.currentHandIndex];
        if (additionalBet > this.balance) return { success: false, error: 'Insufficient balance' };

        this.balance -= additionalBet;

        const splitCard = hand.pop();
        const newHand = [splitCard];

        // Insert new hand after current hand
        this.playerHands.splice(this.currentHandIndex + 1, 0, newHand);
        this.handBets.splice(this.currentHandIndex + 1, 0, additionalBet);

        // Deal one card to each hand
        hand.push(this.dealCard());
        newHand.push(this.dealCard());

        const isSplitAces = splitCard.rank === 'A';

        return {
            success: true,
            hands: this.playerHands.map(h => [...h]),
            splitAces: isSplitAces,
            handComplete: isSplitAces // Split aces only get one card each
        };
    }

    takeInsurance() {
        if (!this.isPlaying) return { success: false, error: 'No game in progress' };
        if (this.dealerHand[0].rank !== 'A') return { success: false, error: 'Dealer not showing Ace' };
        if (this.insuranceBet > 0) return { success: false, error: 'Insurance already taken' };

        const insuranceAmount = Math.floor(this.handBets[0] / 2);
        if (insuranceAmount > this.balance) return { success: false, error: 'Insufficient balance' };

        this.balance -= insuranceAmount;
        this.insuranceBet = insuranceAmount;

        return { success: true, amount: insuranceAmount };
    }

    moveToNextHand() {
        this.currentHandIndex++;
        return this.currentHandIndex < this.playerHands.length;
    }

    playDealer() {
        // Reveal hole card
        this.dealerHand[1].faceDown = false;

        // Check for insurance payout
        let insurancePayout = 0;
        if (this.insuranceBet > 0 && isBlackjack(this.dealerHand)) {
            insurancePayout = this.insuranceBet * 3;
            this.balance += insurancePayout;
        }

        // Check if all player hands busted
        const allBusted = this.playerHands.every(h => isBusted(h));
        if (allBusted) {
            return {
                dealerHand: [...this.dealerHand],
                dealerTotal: calculateHand(this.dealerHand, true),
                cardsDrawn: [],
                insurancePayout
            };
        }

        // Dealer draws to 17
        const cardsDrawn = [];
        while (calculateHand(this.dealerHand, true) < 17) {
            const card = this.dealCard();
            this.dealerHand.push(card);
            cardsDrawn.push(card);
        }

        return {
            dealerHand: [...this.dealerHand],
            dealerTotal: calculateHand(this.dealerHand, true),
            cardsDrawn,
            insurancePayout
        };
    }

    resolveHands() {
        const results = [];
        const dealerTotal = calculateHand(this.dealerHand, true);
        const dealerBJ = isBlackjack(this.dealerHand);

        for (let i = 0; i < this.playerHands.length; i++) {
            const hand = this.playerHands[i];
            const bet = this.handBets[i];
            const playerBJ = isBlackjack(hand) && this.playerHands.length === 1;

            const result = determineWinner(hand, this.dealerHand, playerBJ, dealerBJ);
            const payout = Math.floor(bet * getPayoutMultiplier(result));

            this.balance += payout;

            results.push({
                handIndex: i,
                hand: [...hand],
                playerTotal: calculateHand(hand),
                bet,
                result,
                payout
            });
        }

        this.isPlaying = false;
        this.currentBet = 0;

        return {
            results,
            dealerTotal,
            newBalance: this.balance
        };
    }

    getState() {
        return {
            balance: this.balance,
            currentBet: this.currentBet,
            isPlaying: this.isPlaying,
            playerHands: this.playerHands.map(h => [...h]),
            dealerHand: [...this.dealerHand],
            currentHandIndex: this.currentHandIndex,
            handBets: [...this.handBets],
            insuranceBet: this.insuranceBet
        };
    }

    getCurrentHand() {
        return this.playerHands[this.currentHandIndex] || null;
    }

    canDouble() {
        const hand = this.getCurrentHand();
        return hand && hand.length === 2 && this.balance >= this.handBets[this.currentHandIndex];
    }

    canSplit() {
        const hand = this.getCurrentHand();
        return hand && isPair(hand) && this.playerHands.length < 4 && this.balance >= this.handBets[this.currentHandIndex];
    }

    canTakeInsurance() {
        return this.isPlaying &&
               this.playerHands[0].length === 2 &&
               this.playerHands.length === 1 &&
               this.dealerHand[0].rank === 'A' &&
               this.insuranceBet === 0 &&
               this.balance >= Math.floor(this.handBets[0] / 2);
    }
}

// Export for Node.js (testing) and browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SUITS,
        RANKS,
        VALUES,
        HARD_STRATEGY,
        SOFT_STRATEGY,
        PAIR_STRATEGY,
        HARD_EV,
        SOFT_EV,
        createCard,
        createDeck,
        shuffle,
        calculateHand,
        isSoft,
        isPair,
        isBlackjack,
        isBusted,
        getOptimalAction,
        getHandEV,
        determineWinner,
        getPayoutMultiplier,
        BlackjackGame
    };
}
