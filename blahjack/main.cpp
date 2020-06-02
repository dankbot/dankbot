#include <vector>
#include <string.h>
#include <stdexcept>
#include <iostream>
#include <algorithm>
#include <string>

const char *const BJ_SYMBOLS[] = {
        "♥", "♠", "♦", "♣"
};

#define BJ_RANK_COUNT 13
const char *const BJ_RANKS[] = {
        nullptr, "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"
};
const int BJ_RANK_VALUES[] = {
        0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11
};

using BjSymbol = char;
using BjRank = char;

struct BjCard {
    BjSymbol symbol = 0;
    BjRank rank = 0;

    operator bool() const { return rank != 0; }
    const char *symbolStr() const { return BJ_SYMBOLS[symbol]; }
    const char *rankStr() const { return BJ_RANKS[rank]; }
    int value() const { return BJ_RANK_VALUES[rank]; }
    size_t deckIndex() const { return (rank - 1) * 4 + symbol; }
};

#define BJ_DECK_N 52
BjCard BJ_DECK[BJ_DECK_N];

void initCardDeck(BjCard *arr) {
    for (BjRank rank = 1; rank <= BJ_RANK_COUNT; ++rank) {
        for (BjSymbol sym = 0; sym < 4; ++sym)
            arr[BjCard {sym, rank}.deckIndex()] = {sym, rank};
    }
}

struct BjCardHand {
    BjCard cards[5];

    void add(BjCard card) {
        for (auto &i : cards) {
            if (!i) {
                i = card;
                return;
            }
        }
        throw std::logic_error("you shouldn't be adding a sixth card");
    }

    int count() const {
        for (int i = 0; i < 5; i++) {
            if (!cards[i])
                return i;
        }
        return 5;
    }

    int sum() const {
        int ret = 0;
        for (BjCard c : cards) {
            if (c.value() != 11)
                ret += c.value();
        }
        for (BjCard c : cards) {
            if (c.value() == 11) {
                if (ret + 11 <= 21)
                    ret += 11;
                else
                    ret += 1;
            }
        }
        return ret;
    }

};

struct BjState {
    BjCardHand cardsOur, cardsOpponent;
    int roundNo;

    double getOpponentDrawCardChance() const {
        if (cardsOpponent.count() == 5)
            return 0.0;
        if (cardsOpponent.sum() <= 14)
            return 1.0;
        else
            return 0.0;
    }

    void setUsedCards(bool b[]) const {
        memset(b, 0, BJ_DECK_N * sizeof(bool));
        for (BjCard c : cardsOur.cards)
            if (c)
                b[c.deckIndex()] = true;
        for (BjCard c : cardsOpponent.cards)
            if (c)
                b[c.deckIndex()] = true;
    }

    void print() const {
        printf(  "Our Cards:      [%2i] ", cardsOur.sum());
        for (auto const &c : cardsOur.cards)
            if (c)
                printf("%s %s; ", c.symbolStr(), c.rankStr());
        printf("\nOpponent Cards: [%2i] ", cardsOpponent.sum());
        for (auto const &c : cardsOpponent.cards)
            if (c)
                printf("%s %s; ", c.symbolStr(), c.rankStr());
        printf("\nRound: %i\n\n", roundNo);
    }
};

struct BjResult {
    double hitChance, standChance;
};

template <typename Cb, typename Predicate>
BjResult getChancesWithRandomCard(BjState const &state, Cb const &cb, Predicate const &pred) {
    int optionsCount = 0;
    int lastIndex = -1;
    BjResult lastResult {0.0, 0.0};
    BjResult thisResult {0.0, 0.0};

    bool usedCards[BJ_DECK_N];
    state.setUsedCards(usedCards);
    for (int i = 0; i < BJ_DECK_N; i++) {
        if (usedCards[i] || !pred(BJ_DECK[i]))
            continue;
        ++optionsCount;

        // It does not really matter what color we pick
        if (lastIndex == -1 || BJ_DECK[lastIndex].value() != BJ_DECK[i].value()) {
            lastResult = cb(BJ_DECK[i]);
            lastIndex = i;
        }

        thisResult.hitChance += lastResult.hitChance;
        thisResult.standChance += lastResult.standChance;
    }
    thisResult.hitChance /= optionsCount;
    thisResult.standChance /= optionsCount;
    return thisResult;
}

template <typename Cb>
BjResult getChancesAfterOpponentCardDraw(BjState const &state, Cb const &cb) {
    double chance = state.getOpponentDrawCardChance();
    BjResult result {0.0, 0.0};
    if (chance > 0.0) {
        BjResult thisResult = getChancesWithRandomCard(state, [state, cb](BjCard const &card) {
            BjState tempState(state);
            tempState.cardsOpponent.add(card);
            return cb(tempState, true);
        }, [](BjCard const &) { return true; });
        result.hitChance += thisResult.hitChance * chance;
        result.standChance += thisResult.standChance * chance;
    }
    if (chance < 1.0) {
        BjResult thisResult = cb(state, false);
        result.hitChance += thisResult.hitChance * (1.0 - chance);
        result.standChance += thisResult.standChance * (1.0 - chance);
    }
    return result;
}

BjResult doAnalyze(BjState const &state);

BjResult addCardsAndAnalyze(BjState const &state) {
    auto opponentCardCount = state.cardsOpponent.count();
    if (opponentCardCount == 1) {
        auto maxValue = state.cardsOpponent.cards[0].value();
        return getChancesWithRandomCard(state, [state](BjCard const &card) {
            BjState tempState(state);
            tempState.cardsOpponent.add(card);
            return addCardsAndAnalyze(tempState);
        }, [maxValue](BjCard const &c) { return c.value() <= maxValue; });
    }

    if (opponentCardCount >= state.roundNo + 1)
        return doAnalyze(state);

    return getChancesAfterOpponentCardDraw(state, [](BjState const &state, bool cardDrawn) {
        if (!cardDrawn)
            return doAnalyze(state);
        return addCardsAndAnalyze(state);
    });
}

BjResult doAnalyze(BjState const &state) {
    auto ourCardSum = state.cardsOur.sum();
    auto opponentCardSum = state.cardsOpponent.sum();

    // state.print();

    // first check the state itself
    if (ourCardSum > 21)
        return {0.0, 0.0};
    if (state.cardsOur.count() == 5 || ourCardSum == 21 || opponentCardSum > 21)
        return {1.0, 1.0};
    if (opponentCardSum == 21)
        return {0.0, 0.0};

    // check stand
    BjResult standResult = getChancesAfterOpponentCardDraw(state, [](BjState const &state, bool) {
        auto ourCardSum = state.cardsOur.sum();
        if (state.cardsOpponent.sum() <= ourCardSum && ourCardSum <= 21)
            return BjResult {1.0, 1.0};
        else
            return BjResult {0.0, 0.0};
    });

    // check hit
    BjResult hitResult = getChancesWithRandomCard(state, [state](BjCard const &card) {
        BjState tempState(state);
        tempState.cardsOur.add(card);
        ++tempState.roundNo;
        return getChancesAfterOpponentCardDraw(tempState, [](BjState const &state, bool) {
            BjResult r = doAnalyze(state);
            return BjResult {std::max(r.hitChance, r.standChance), 0.0};
        });
    }, [](BjCard const &c) { return true; });


    return BjResult {hitResult.hitChance, standResult.standChance};
}


BjCardHand readCardHand() {
    BjCardHand ret;
    int n;
    std::cin >> n;
    if (n > 5)
        throw std::runtime_error("eww you can't have more than 5 cards in hand");
    for (int i = 0; i < n; i++) {
        std::string symbol, rank;
        std::cin >> symbol >> rank;
        BjSymbol s;
        for (s = 0; s < 4; s++) {
            if (!strcmp(BJ_SYMBOLS[s], symbol.c_str()))
                break;
        }
        BjRank r;
        for (r = 1; r <= BJ_RANK_COUNT; r++) {
            if (!strcmp(BJ_RANKS[r], rank.c_str()))
                break;
        }
        if (s == 4 || r == BJ_RANK_COUNT + 1)
            throw std::runtime_error("that's not a valid card");
        ret.add({s, r});
    }
    return ret;
}

int main() {
    initCardDeck(BJ_DECK);

    BjState state;
    state.cardsOur = readCardHand();
    state.cardsOpponent = readCardHand();
    std::cin >> state.roundNo;

    state.print();

    BjResult result = addCardsAndAnalyze(state);
    printf("Hit Chance: %lf\n", result.hitChance);
    printf("Stand Chance: %lf\n", result.standChance);

    return 0;
}