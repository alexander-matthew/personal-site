/**
 * Blackjack Engine Unit Tests
 */

const {
    createCard,
    createDeck,
    shuffle,
    calculateHand,
    isSoft,
    isPair,
    isBlackjack,
    isBusted,
    getOptimalAction,
    determineWinner,
    getPayoutMultiplier,
    BlackjackGame
} = require('./blackjack-engine');

describe('Card Creation', () => {
    test('createCard creates a valid card', () => {
        const card = createCard('A', 'spades');
        expect(card.rank).toBe('A');
        expect(card.suit).toBe('spades');
        expect(card.value).toBe(11);
        expect(card.faceDown).toBe(false);
    });

    test('createCard with faceDown', () => {
        const card = createCard('K', 'hearts', true);
        expect(card.faceDown).toBe(true);
    });

    test('face cards have value 10', () => {
        expect(createCard('J', 'hearts').value).toBe(10);
        expect(createCard('Q', 'hearts').value).toBe(10);
        expect(createCard('K', 'hearts').value).toBe(10);
    });
});

describe('Deck Creation', () => {
    test('createDeck creates 52 cards per deck', () => {
        const deck = createDeck(1);
        expect(deck.length).toBe(52);
    });

    test('createDeck creates 6-deck shoe by default', () => {
        const deck = createDeck();
        expect(deck.length).toBe(312);
    });

    test('deck contains all ranks and suits', () => {
        const deck = createDeck(1);
        const hearts = deck.filter(c => c.suit === 'hearts');
        expect(hearts.length).toBe(13);
        const aces = deck.filter(c => c.rank === 'A');
        expect(aces.length).toBe(4);
    });
});

describe('Shuffle', () => {
    test('shuffle returns same length array', () => {
        const deck = createDeck(1);
        const shuffled = shuffle(deck);
        expect(shuffled.length).toBe(deck.length);
    });

    test('shuffle does not modify original array', () => {
        const deck = createDeck(1);
        const original = [...deck];
        shuffle(deck);
        expect(deck).toEqual(original);
    });

    test('shuffle produces different order (probabilistic)', () => {
        const deck = createDeck(1);
        const shuffled = shuffle(deck);
        // Very unlikely that first 5 cards are in same position
        const samePosition = deck.slice(0, 5).every((card, i) =>
            card.rank === shuffled[i].rank && card.suit === shuffled[i].suit
        );
        expect(samePosition).toBe(false);
    });
});

describe('Hand Calculation', () => {
    test('calculateHand adds card values', () => {
        const hand = [
            createCard('5', 'hearts'),
            createCard('7', 'spades')
        ];
        expect(calculateHand(hand)).toBe(12);
    });

    test('calculateHand handles face cards', () => {
        const hand = [
            createCard('K', 'hearts'),
            createCard('Q', 'spades')
        ];
        expect(calculateHand(hand)).toBe(20);
    });

    test('calculateHand adjusts ace from 11 to 1 when busting', () => {
        const hand = [
            createCard('A', 'hearts'),
            createCard('8', 'spades'),
            createCard('5', 'clubs')
        ];
        expect(calculateHand(hand)).toBe(14); // 11 + 8 + 5 = 24, so ace becomes 1: 1 + 8 + 5 = 14
    });

    test('calculateHand adjusts multiple aces', () => {
        const hand = [
            createCard('A', 'hearts'),
            createCard('A', 'spades'),
            createCard('A', 'clubs')
        ];
        expect(calculateHand(hand)).toBe(13); // 11 + 1 + 1 = 13
    });

    test('calculateHand ignores face-down cards by default', () => {
        const hand = [
            createCard('K', 'hearts'),
            createCard('7', 'spades', true) // Face down
        ];
        expect(calculateHand(hand)).toBe(10);
    });

    test('calculateHand counts face-down when countHidden is true', () => {
        const hand = [
            createCard('K', 'hearts'),
            createCard('7', 'spades', true)
        ];
        expect(calculateHand(hand, true)).toBe(17);
    });
});

describe('Hand Type Detection', () => {
    test('isSoft detects soft hands', () => {
        const softHand = [
            createCard('A', 'hearts'),
            createCard('6', 'spades')
        ];
        expect(isSoft(softHand)).toBe(true);
    });

    test('isSoft returns false for hard hands', () => {
        const hardHand = [
            createCard('10', 'hearts'),
            createCard('7', 'spades')
        ];
        expect(isSoft(hardHand)).toBe(false);
    });

    test('isSoft returns false when ace must count as 1', () => {
        const hand = [
            createCard('A', 'hearts'),
            createCard('8', 'spades'),
            createCard('7', 'clubs')
        ];
        expect(isSoft(hand)).toBe(false); // 1 + 8 + 7 = 16 (hard)
    });

    test('isPair detects pairs', () => {
        const pair = [
            createCard('8', 'hearts'),
            createCard('8', 'spades')
        ];
        expect(isPair(pair)).toBe(true);
    });

    test('isPair returns false for non-pairs', () => {
        const nonPair = [
            createCard('8', 'hearts'),
            createCard('9', 'spades')
        ];
        expect(isPair(nonPair)).toBe(false);
    });

    test('isPair returns false for hands with more than 2 cards', () => {
        const hand = [
            createCard('8', 'hearts'),
            createCard('8', 'spades'),
            createCard('5', 'clubs')
        ];
        expect(isPair(hand)).toBe(false);
    });

    test('isBlackjack detects blackjack', () => {
        const blackjack = [
            createCard('A', 'hearts'),
            createCard('K', 'spades')
        ];
        expect(isBlackjack(blackjack)).toBe(true);
    });

    test('isBlackjack returns false for 21 with more than 2 cards', () => {
        const hand = [
            createCard('7', 'hearts'),
            createCard('7', 'spades'),
            createCard('7', 'clubs')
        ];
        expect(isBlackjack(hand)).toBe(false);
    });

    test('isBusted detects bust', () => {
        const bust = [
            createCard('K', 'hearts'),
            createCard('Q', 'spades'),
            createCard('5', 'clubs')
        ];
        expect(isBusted(bust)).toBe(true);
    });

    test('isBusted returns false for valid hands', () => {
        const hand = [
            createCard('K', 'hearts'),
            createCard('Q', 'spades')
        ];
        expect(isBusted(hand)).toBe(false);
    });
});

describe('Optimal Strategy', () => {
    test('hard 16 vs dealer 10 should hit', () => {
        const hand = [createCard('10', 'hearts'), createCard('6', 'spades')];
        const dealerUpcard = createCard('10', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('hit');
        expect(result.handType).toBe('hard');
    });

    test('hard 16 vs dealer 6 should stand', () => {
        const hand = [createCard('10', 'hearts'), createCard('6', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('stand');
    });

    test('11 vs dealer 6 should double', () => {
        const hand = [createCard('5', 'hearts'), createCard('6', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('double');
        expect(result.handType).toBe('double');
    });

    test('11 vs dealer 6 should hit if cannot double', () => {
        const hand = [createCard('5', 'hearts'), createCard('6', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard, false);
        expect(result.action).toBe('hit');
    });

    test('soft 17 (A,6) vs dealer 6 should double', () => {
        const hand = [createCard('A', 'hearts'), createCard('6', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('double');
        expect(result.handType).toBe('double');
    });

    test('soft 18 (A,7) vs dealer 7 should stand', () => {
        const hand = [createCard('A', 'hearts'), createCard('7', 'spades')];
        const dealerUpcard = createCard('7', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('stand');
    });

    test('pair of 8s vs any should split', () => {
        const hand = [createCard('8', 'hearts'), createCard('8', 'spades')];
        const dealerUpcard = createCard('10', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('split');
        expect(result.handType).toBe('pair');
    });

    test('pair of 10s should stand (never split)', () => {
        const hand = [createCard('10', 'hearts'), createCard('K', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('stand');
    });

    test('pair of Aces should split', () => {
        const hand = [createCard('A', 'hearts'), createCard('A', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('split');
    });

    test('pair of 5s vs dealer 6 should double (not split)', () => {
        const hand = [createCard('5', 'hearts'), createCard('5', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('double');
    });
});

describe('Winner Determination', () => {
    test('player wins with higher total', () => {
        const playerHand = [createCard('K', 'hearts'), createCard('9', 'spades')];
        const dealerHand = [createCard('K', 'clubs'), createCard('8', 'diamonds')];
        expect(determineWinner(playerHand, dealerHand)).toBe('player');
    });

    test('dealer wins with higher total', () => {
        const playerHand = [createCard('K', 'hearts'), createCard('7', 'spades')];
        const dealerHand = [createCard('K', 'clubs'), createCard('9', 'diamonds')];
        expect(determineWinner(playerHand, dealerHand)).toBe('dealer');
    });

    test('push on equal totals', () => {
        const playerHand = [createCard('K', 'hearts'), createCard('8', 'spades')];
        const dealerHand = [createCard('K', 'clubs'), createCard('8', 'diamonds')];
        expect(determineWinner(playerHand, dealerHand)).toBe('push');
    });

    test('player busts, dealer wins', () => {
        const playerHand = [createCard('K', 'hearts'), createCard('Q', 'spades'), createCard('5', 'clubs')];
        const dealerHand = [createCard('K', 'clubs'), createCard('8', 'diamonds')];
        expect(determineWinner(playerHand, dealerHand)).toBe('dealer');
    });

    test('dealer busts, player wins', () => {
        const playerHand = [createCard('K', 'hearts'), createCard('8', 'spades')];
        const dealerHand = [createCard('K', 'clubs'), createCard('Q', 'diamonds'), createCard('5', 'hearts')];
        expect(determineWinner(playerHand, dealerHand)).toBe('player');
    });

    test('player blackjack beats dealer 21', () => {
        const playerHand = [createCard('A', 'hearts'), createCard('K', 'spades')];
        const dealerHand = [createCard('7', 'clubs'), createCard('7', 'diamonds'), createCard('7', 'hearts')];
        expect(determineWinner(playerHand, dealerHand, true, false)).toBe('blackjack');
    });

    test('both blackjack is push', () => {
        const playerHand = [createCard('A', 'hearts'), createCard('K', 'spades')];
        const dealerHand = [createCard('A', 'clubs'), createCard('Q', 'diamonds')];
        expect(determineWinner(playerHand, dealerHand, true, true)).toBe('push');
    });
});

describe('Payout Calculation', () => {
    test('blackjack pays 2.5x', () => {
        expect(getPayoutMultiplier('blackjack')).toBe(2.5);
    });

    test('win pays 2x', () => {
        expect(getPayoutMultiplier('player')).toBe(2);
    });

    test('push returns 1x', () => {
        expect(getPayoutMultiplier('push')).toBe(1);
    });

    test('loss returns 0', () => {
        expect(getPayoutMultiplier('dealer')).toBe(0);
    });
});

describe('BlackjackGame Class', () => {
    let game;

    beforeEach(() => {
        game = new BlackjackGame({ startingBalance: 1000 });
    });

    test('initializes with correct balance', () => {
        expect(game.balance).toBe(1000);
    });

    test('placeBet deducts from balance on deal', () => {
        game.placeBet(100);
        game.deal();
        expect(game.balance).toBe(900);
    });

    test('placeBet fails with insufficient balance', () => {
        const result = game.placeBet(2000);
        expect(result.success).toBe(false);
        expect(result.error).toBe('Insufficient balance');
    });

    test('deal creates player and dealer hands', () => {
        game.placeBet(100);
        const result = game.deal();
        expect(result.success).toBe(true);
        expect(result.playerHand.length).toBe(2);
        expect(result.dealerHand.length).toBe(2);
    });

    test('deal sets dealer hole card face down', () => {
        game.placeBet(100);
        const result = game.deal();
        expect(result.dealerHand[0].faceDown).toBe(false); // Upcard
        expect(result.dealerHand[1].faceDown).toBe(true);  // Hole card
    });

    test('hit adds card to current hand', () => {
        game.placeBet(100);
        game.deal();
        const initialLength = game.getCurrentHand().length;
        game.hit();
        expect(game.getCurrentHand().length).toBe(initialLength + 1);
    });

    test('double doubles bet and adds one card', () => {
        game.placeBet(100);
        game.deal();
        const initialBet = game.handBets[0];
        const result = game.double();
        expect(result.success).toBe(true);
        expect(game.handBets[0]).toBe(initialBet * 2);
        expect(game.getCurrentHand().length).toBe(3);
    });

    test('split creates two hands', () => {
        // Create a controlled scenario with a pair
        game.placeBet(100);
        game.deal();

        // Force a pair for testing
        game.playerHands[0] = [createCard('8', 'hearts'), createCard('8', 'spades')];

        const result = game.split();
        expect(result.success).toBe(true);
        expect(game.playerHands.length).toBe(2);
        expect(game.handBets.length).toBe(2);
    });

    test('canDouble returns correct state', () => {
        game.placeBet(100);
        game.deal();
        expect(game.canDouble()).toBe(true);

        game.hit(); // After hit, can't double
        expect(game.canDouble()).toBe(false);
    });

    test('canSplit returns correct state', () => {
        game.placeBet(100);
        game.deal();

        // Force a pair
        game.playerHands[0] = [createCard('8', 'hearts'), createCard('8', 'spades')];
        expect(game.canSplit()).toBe(true);

        // Force non-pair
        game.playerHands[0] = [createCard('8', 'hearts'), createCard('9', 'spades')];
        expect(game.canSplit()).toBe(false);
    });

    test('takeInsurance works when dealer shows ace', () => {
        game.placeBet(100);
        game.deal();

        // Force dealer to show ace
        game.dealerHand[0] = createCard('A', 'hearts');

        const result = game.takeInsurance();
        expect(result.success).toBe(true);
        expect(result.amount).toBe(50);
        expect(game.insuranceBet).toBe(50);
    });

    test('takeInsurance fails when dealer not showing ace', () => {
        game.placeBet(100);
        game.deal();

        // Force dealer to show non-ace
        game.dealerHand[0] = createCard('K', 'hearts');

        const result = game.takeInsurance();
        expect(result.success).toBe(false);
    });

    test('playDealer reveals hole card', () => {
        game.placeBet(100);
        game.deal();
        game.stand();
        const result = game.playDealer();
        expect(result.dealerHand[1].faceDown).toBe(false);
    });

    test('playDealer draws to 17', () => {
        game.placeBet(100);
        game.deal();

        // Force dealer to have 15
        game.dealerHand = [createCard('10', 'hearts'), createCard('5', 'spades', true)];

        game.stand();
        const result = game.playDealer();
        expect(result.dealerTotal).toBeGreaterThanOrEqual(17);
    });

    test('resolveHands calculates correct payouts', () => {
        game.placeBet(100);
        game.deal();

        // Force player to have 20, dealer to have 18
        game.playerHands[0] = [createCard('K', 'hearts'), createCard('Q', 'spades')];
        game.dealerHand = [createCard('K', 'clubs'), createCard('8', 'diamonds')];

        const result = game.resolveHands();
        expect(result.results[0].result).toBe('player');
        expect(result.results[0].payout).toBe(200); // 2x bet
    });

    test('game flow: bet, deal, hit, stand, resolve', () => {
        game.placeBet(100);
        expect(game.balance).toBe(1000);

        game.deal();
        expect(game.balance).toBe(900);
        expect(game.isPlaying).toBe(true);

        // Force specific hands for deterministic test
        game.playerHands[0] = [createCard('10', 'hearts'), createCard('9', 'spades')];
        game.dealerHand = [createCard('7', 'clubs'), createCard('Q', 'diamonds', true)];

        game.stand();
        game.playDealer();
        const result = game.resolveHands();

        expect(game.isPlaying).toBe(false);
        // Player has 19, dealer has 17, player wins
        expect(result.results[0].result).toBe('player');
        expect(game.balance).toBe(1100); // Started with 900, won 200
    });

    test('auto re-up uses last bet', () => {
        game.placeBet(100);
        game.deal();
        game.playerHands[0] = [createCard('K', 'hearts'), createCard('Q', 'spades')];
        game.dealerHand = [createCard('7', 'clubs'), createCard('8', 'diamonds')];
        game.stand();
        game.playDealer();
        game.resolveHands();

        // Now deal again without placing bet
        game.currentBet = 0;
        const result = game.deal();
        expect(result.success).toBe(true);
        expect(game.handBets[0]).toBe(100); // Should use last bet
    });
});

describe('Edge Cases', () => {
    test('multiple aces scenario', () => {
        const hand = [
            createCard('A', 'hearts'),
            createCard('A', 'spades'),
            createCard('A', 'clubs'),
            createCard('A', 'diamonds')
        ];
        expect(calculateHand(hand)).toBe(14); // 11 + 1 + 1 + 1
    });

    test('ace switches from 11 to 1 correctly', () => {
        const hand = [
            createCard('A', 'hearts'),
            createCard('5', 'spades')
        ];
        expect(calculateHand(hand)).toBe(16); // Soft 16

        hand.push(createCard('8', 'clubs'));
        expect(calculateHand(hand)).toBe(14); // 1 + 5 + 8 = 14 (hard)
    });

    test('21 with three 7s is not blackjack', () => {
        const hand = [
            createCard('7', 'hearts'),
            createCard('7', 'spades'),
            createCard('7', 'clubs')
        ];
        expect(calculateHand(hand)).toBe(21);
        expect(isBlackjack(hand)).toBe(false);
    });

    test('pair of face cards is a pair of 10s for strategy', () => {
        const hand = [createCard('J', 'hearts'), createCard('Q', 'spades')];
        const dealerUpcard = createCard('6', 'clubs');
        const result = getOptimalAction(hand, dealerUpcard);
        expect(result.action).toBe('stand'); // Never split 10s
    });
});
