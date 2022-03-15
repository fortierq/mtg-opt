import copy
import random
from collections import Counter
import pandas as pd
import dask
from dask.distributed import Client
import webbrowser


def keep_hand(hand, keep, n_cc):
    if 'DW' not in hand:
        return False
    if 'Sw' not in hand:
        return False
    if hand.count('DR') < 2:
        return False
    if (n_cc - max(0, hand.count('CC') - (7 - keep))) < 7:
        return False
    return True


def london_mulligan(hand, keep):
    base_hand = Counter({'CC': 0, 'DW': 1, 'Sw': 1, 'DR': 2})
    hand_counter = Counter(hand)
    excess = []
    while sum(hand_counter.values()) > keep:
        for card in base_hand:
            if hand_counter[card] > base_hand[card]:
                hand_counter[card] -= 1
                excess.append(card)
    return list(hand_counter.elements()), excess


def kill(deck):
    life_me = 20
    life_op = 20
    while life_me > 2:
        life_me -= 2
        for _ in range(2):
            try:
                card = deck.pop(0)
            except IndexError:
                return False
            if card == 'CC':
                life_me += 3
                life_op -= 3
            if life_op <= 0:
                return True
    return False


def run_iteration(deck, n_cc):
    for hand_size in list(range(4, 8))[::-1]:
        random.shuffle(deck)
        deck_tmp = copy.copy(deck)
        if keep_hand(deck_tmp[:7], hand_size, n_cc):
            hand, excess = london_mulligan(deck_tmp[:7], hand_size)
            return kill(deck_tmp[hand_size:] + excess)
    return False


def run_simulation(n_dw, n_sw, n_dr, n_cc, iters):
    deck = ['DW'] * n_dw + ['Sw'] * n_sw + ['DR'] * n_dr + ['CC'] * n_cc
    success = [run_iteration(deck, n_cc) for _ in range(iters)]
    return {
        'DW': n_dw,
        'Sw': n_sw,
        'DR': n_dr,
        'CC': n_cc,
        'Success_Rate':  sum(success) / iters
    }


def get_decks():
    decks = []
    for n_dw in range(41):
        for n_sw in range(41 - n_dw):
            for n_dr in range(41 - (n_dw + n_sw)):
                decks.append({
                    'DW': n_dw,
                    'Sw': n_sw,
                    'DR': n_dr,
                    'CC': (40 - (n_dw + n_sw + n_dr)),
                })
    decks = pd.DataFrame(decks)
    return decks


def main(iters=100):
    client = Client()
    webbrowser.open(client.dashboard_link)
    decks = get_decks()
    results = [dask.delayed(run_simulation)(*counts, iters) for counts in decks.values]
    results = pd.DataFrame(dask.compute(*results))
    return results


if __name__ == '__main__':
    df = main(10000)
    print(df.sort_values(by='Success_Rate', ascending=False).head(10))
    df.to_csv('~/Desktop/fnm_hero.csv')