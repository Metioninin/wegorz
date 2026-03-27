from dataclasses import dataclass
from mgr.sims.helpers import PokerCode
from mgr.sims.helpers import TestError
import random
import json
from itertools import combinations
from collections import Counter

kolory = ["kier", "pik", "karo", "trefl"]
numerki = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
@dataclass
class Card:
    kolor: str
    numer: str

@dataclass
class PlayerInfo:
    twojIndex: int
    hajs: list[int]
    stawki: list[int]
    stawka: int
    pula: int
    ownCards: list[Card]
    mutualCards: list[Card]

@dataclass
class UnityCard:
    kolor: int
    numer: int

@dataclass
class UnityMove:
    index: int
    money: int
    bet: int
    move: str
    pula: int

@dataclass
class UnityPlayer:
    name: str
    money: int
    bet: int
    cards: list[UnityCard]

@dataclass
class Frame:
    moves: list[UnityMove]
    mutualCards: list[UnityCard]

def CardToUnityCard(card: Card):
    newCard = UnityCard(0, card.numer)
    for i in range(4):
        if card.kolor == kolory[i]:
            newCard.kolor = i
            break
    return newCard

def WyznaczUklad(cards: list, index: int):
    # Mapowanie Twoich napisów na liczby (A=14, K=13, itd.)
    wartosci_mapa = {str(i): i for i in range(2, 11)}
    wartosci_mapa.update({'J': 11, 'Q': 12, 'K': 13, 'A': 14})

    # 1. Sprawdzamy wszystkie 21 kombinacji (wybór 5 kart z 7)
    wszystkie_piatki = list(combinations(cards, 5))
    najlepszy_wynik = [-1] 

    for piatka in wszystkie_piatki:
        # Wartości liczbowe (posortowane malejąco dla stritów i kolorów)
        v = sorted([wartosci_mapa[c.numer] for c in piatka], reverse=True)
        s = [c.kolor for c in piatka]
        
        # --- ANALIZA UKŁADU (Z TWOJĄ POPRAWKĄ) ---
        c_counts = Counter(v)
        # Sortujemy: najpierw po ilości (np. 3 trójki), potem po wartości (np. Asy)
        sorted_items = sorted(c_counts.items(), key=lambda x: (-x[1], -x[0]))
        
        count_values = [x[1] for x in sorted_items] 
        val_order = [x[0] for x in sorted_items] 
        
        is_flush = len(set(s)) == 1
        is_straight = len(set(v)) == 5 and all(v[i] - v[i+1] == 1 for i in range(4))
        
        # Specjalny przypadek: Mały Strit (A, 2, 3, 4, 5)
        # Traktujemy go jako strit do 5-tki
        if set(v) == {14, 5, 4, 3, 2}:
            is_straight = True
            v_for_straight = [5, 4, 3, 2, 1] 
        else:
            v_for_straight = v

        # --- RANKING (Drabinka od najsilniejszej) ---
        res = []
        
        # 10. Poker Królewski (Strit+Kolor do Asa)
        if is_straight and is_flush and v_for_straight[0] == 14:
            res = [10]
        
        # 9. Poker (Strit+Kolor)
        elif is_straight and is_flush:
            res = [9, v_for_straight[0]]
            
        # 8. Kareta
        elif count_values == [4, 1]:
            res = [8, val_order[0], val_order[1]]
            
        # 7. Full House
        elif count_values == [3, 2]:
            res = [7, val_order[0], val_order[1]]
            
        # 6. Kolor
        elif is_flush:
            res = [6] + v # Porównuje wszystkie 5 kart po kolei
            
        # 5. Strit
        elif is_straight:
            res = [5, v_for_straight[0]]
            
        # 4. Trójka
        elif count_values == [3, 1, 1]:
            res = [4, val_order[0], val_order[1], val_order[2]]
            
        # 3. Dwie Pary
        elif count_values == [2, 2, 1]:
            # val_order dzięki sortowaniu ma już [wyzsza_para, nizsza_para, kicker]
            res = [3, val_order[0], val_order[1], val_order[2]]
            
        # 2. Para
        elif count_values == [2, 1, 1, 1]:
            # val_order ma [para, kicker1, kicker2, kicker3]
            res = [2] + val_order
            
        # 1. Wysoka karta
        else:
            res = [1] + v

        # Wybieramy absolutnie najlepszą kombinację z 21 możliwych
        if res > najlepszy_wynik:
            najlepszy_wynik = res
            
    return [najlepszy_wynik, index]

def RandomCard(deck: list[Card]):
    karta = deck[random.randint(0, len(deck) - 1)]
    deck.remove(karta)
    return karta

def PlayerFold(i: int, folded: list[bool], stawki: list[int]):
    folded[i] = True
    stawki[i] = -1
    return i

def AllIn(i: int, allIned: list[bool], hajs: list[int], pula: int, stawka: int, stawki: list[int]):
    allIned[i] = True
    pula += hajs[i]
    stawki[i] += hajs[i]
    stawka = max(stawka, stawki[i])
    hajs[i] = 0
    return pula, stawka

def calc_ranking(ranking: list[tuple[str, float]], hajs: list[int], names: list[str]):
    for i in range(len(names)):
        for j in range(len(ranking)):
            if(ranking[j][0] == names[i]):
                ranking[j] = (ranking[j][0], hajs[i])
                break

def generate_notation(players: list[UnityPlayer], frames: list[Frame], ranking: list[tuple[str, float]], winnerIndex: int):
    # Budujemy główny obiekt Notation
    notation_data = {
        "players": [],
        "frames": [],
        "ranking": [],
        "winnerIndex": winnerIndex
    }

    # 1. Mapowanie graczy (PlayerInfo w C#)
    for p in players:
        notation_data["players"].append({
            "name": p.name,
            "money": p.money,
            "bet": p.bet,
            "cards": [
                {"kolor": c.kolor, "numer": c.numer} for c in p.cards
            ]
        })

    # 2. Mapowanie klatek licytacji (Frame w C#)
    for f in frames:
        moves_list = []
        for m in f.moves:
            moves_list.append({
                "index": m.index,
                "money": m.money,
                "bet": m.bet,
                "move": m.move,
                "pula": m.pula
            })
        
        mutual_cards_list = [
            {"kolor": c.kolor, "numer": c.numer} for c in f.mutualCards
        ]
        
        notation_data["frames"].append({
            "moves": moves_list,
            "mutualCards": mutual_cards_list
        })

    # 3. Mapowanie rankingu końcowego (Order w C#)
    for name, score in ranking:
        notation_data["ranking"].append({
            "name": name,
            "points": score
        })

    #with open("notka.json", "w", encoding="utf-8") as f:
        #json.dump(notation_data, f, indent=4, ensure_ascii=False)
    #return {}

    return json.dumps(notation_data, indent=4, ensure_ascii=False)

blind = 10
def simulate(playerCodes: list[PokerCode], ranking: list[tuple[str, int]], raise_errors: bool = False):

    #if raise_errors:
        #raise TestError("zlke")
    hajs = []
    stawki = []
    pCount = len(playerCodes)
    mutualCards = []
    ownCards = [[] for _ in range(pCount)]
    folded = [False] * pCount
    allIned = [False] * pCount
    stawka = blind
    pula = 0
    winner = 0
    deck = []
    frames = []
    playerNotation = []
    for kolor in kolory:
        for numer in numerki:
            deck.append(Card(kolor, numer)) #generowanie decku
    for i in range(pCount): #generowanie graczy (kazdy daje blinda)
        if ranking[i][1] == 0:
            folded[i] = True
        coStawiam = min(blind, ranking[i][1])
        hajs.append(ranking[i][1] - coStawiam)
        stawki.append(coStawiam)
        pula += coStawiam
        if coStawiam < blind and not folded[i]:
            allIned[i] = True
        for j in range(2):
            ownCards[i].append(RandomCard(deck))
        playerNotation.append(UnityPlayer(playerCodes[i].username, hajs[i], blind, [CardToUnityCard(ownCards[i][0]), CardToUnityCard(ownCards[i][1])]))
        print("Gracz " + str(i))
        print(str(ownCards[i][0].kolor) + " " + str(ownCards[i][0].numer) + " " + str(ownCards[i][1].kolor) + " " + str(ownCards[i][1].numer))

    for j in range(4):
        ruchy = 0
        i = 0
        movesNotation = []
        #dopoki kazdy nie zrobi ruchu i kazdy nie wyrowna stawki
        while ruchy < pCount or any(stawki[k] != stawka for k in range(pCount) if not (folded[k] or allIned[k])):
            ruchy += 1
            if folded[i] or allIned[i]: #jak sfoldowal albo nie ma hajsu to go nie pytamy
                i = (i + 1) % pCount
                continue
            move = playerCodes[i].get_move(PlayerInfo(i, hajs, stawki, stawka, pula, ownCards[i], mutualCards))
            print("Gracz " + str(i))
            print(move[0] + " " + str(move[1]))
            if move[0] == "Fold":
                winner = PlayerFold(i, folded, stawki) #ostatni foldujacy to winner
            elif move[0] == "Check":
                if stawki[i] < stawka:
                    if raise_errors:
                        raise TestError("Proba checka jak byla stawka wieksza od twojej")
                    winner = PlayerFold(i, folded, stawki) #nie mogl checkowac bo musial calla zrobic
                    move[0] = "Error"
            elif move[0] == "Raise":
                if stawka > move[1]:
                    if raise_errors:
                        raise TestError("Niby robisz raise a dajesz mniej niz ktos inny dal")
                    winner = PlayerFold(i, folded, stawki) #nie mogl raisowac bo ktos postawil wiecej
                    move[0] = "Error"
                elif move[1] - stawki[i] > hajs[i]:
                    if raise_errors:
                        raise TestError("Robisz raisea a nie masz tyle hajsu")
                    winner = PlayerFold(i, folded,  stawki)
                    move[0] = "Error"
                else:
                    hajs[i] -= move[1] - stawki[i]
                    pula += move[1] - stawki[i]
                    stawka = move[1]
                    stawki[i] = move[1]
            elif move[0] == "Call":
                if stawka - stawki[i] > hajs[i]:
                    if raise_errors:
                        raise TestError("Robisz calla a nie masz tyle hajsu")
                    winner = PlayerFold(i, folded,  stawki)
                    move[0] = "Error"
                else:
                    hajs[i] -= stawka - stawki[i]
                    pula += stawka - stawki[i]
                    stawki[i] = stawka
            elif move[0] == "All In":
                pula, stawka = AllIn(i, allIned, hajs, pula, stawka, stawki)

            movesNotation.append(UnityMove(i, hajs[i], move[1], move[0], pula))
            i = (i + 1) % pCount
        unityCards = []
        for myCard in mutualCards:
            unityCards.append(CardToUnityCard(myCard))
        frames.append(Frame(movesNotation, unityCards))
        if j == 0:
            for i in range(3):
                mutualCards.append(RandomCard(deck))
        elif j != 3:
            mutualCards.append(RandomCard(deck))
        stawka = 0
        stawki = [0] * pCount

        for i in range(len(mutualCards)):
            print(str(mutualCards[i].kolor) + " " + str(mutualCards[i].numer))
        print('\n')
    wszyscy = [[[0], winner]]
    for i in range(pCount):
        if folded[i]:
            continue
        wszyscy.append(WyznaczUklad(mutualCards + ownCards[i], i))
    wszyscy.sort()
    winner = wszyscy[len(wszyscy) - 1][len(wszyscy[len(wszyscy) - 1]) - 1]
    hajs[winner] += pula
    names = []
    for i in range(pCount):
        names.append(playerCodes[i].username)
    calc_ranking(ranking, hajs, names)
    ranking.sort(key=lambda x: x[1], reverse=True)
    return (generate_notation(playerNotation, frames, ranking, winner), ranking)