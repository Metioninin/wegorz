from dataclasses import dataclass
from typing import Any
from code import Code, Move, Pair
import math
import random

@dataclass
class PlayerInfo:
    n: int
    m: int
    zone: int
    me_top: Pair
    me_bot: Pair
    other_top: list[Pair]
    other_bot: list[Pair]
    def __init__(self):
        self.n = self.m = self.zone = 0
    def __init__(self, n: int, m: int, zone: int, top: list[Pair], bot: list[Pair]):
        self.n = n
        self.m = m
        self.zone = zone
        self.top = top #my position is the first in those lists
        self.bot = bot

def intersect(topa: Pair, bota: Pair, topb: Pair, botb: Pair, czy: bool) -> bool:
    if topa.x > topb.x and topa.x < botb.x and topa.y > botb.y and topa.y < topb.y:
        return True
    if bota.x > topb.x and bota.x < botb.x and topa.y > botb.y and topa.y < topb.y:
        return  True
    if czy:
        return False
    return intersect(topb, botb, topa, bota, True)

st_a = 2
st_b = 3
density = 0.1 #between  (0, 1>
odw = []

visited_indeces = []
def dfs(players: list[Code], me: int):
    visited_indeces.append(me);
    for i in range(len(players)):
        if i == me or intersect(players[i].top, players[i].bot, players[me].top, players[me].bot) == False or odw[i]:
            continue
        dfs(players, i)

def simulate(players: list[Code]) -> dict[str, Any]:
    global odw
    global visited_indeces
    players_count = len(players);
    k = math.ceil(math.sqrt(players_count/(st_a*st_b*density))) #6k^2(ilosc pol[n*m])=ilosc_graczy/denisty
    n = st_a * k
    m = st_b * k
    for i in range(players_count): #poczatkowe rozstawienie graczy na mapie
        players[i].top = Pair(random.randint(0, m-1), random.randint(1, n));
        players[i].bot = players[i].top + Pair(1, -1)
    zoneFrequency = 10
    zoneCurr = 0

    zone = 0
    while players_count > 1: #dopoki zyje co najmniej 2
        others_t = [] #listy pozycji wszystkich graczy (przed ruchami)
        others_b = []
        newMoves = []
        for i in range(players_count):
            others_t.append(players[i].top)
            others_b.append(players[i].bot)
        for i in range(players_count): 
            others_t[0], others_t[i] = others_t[i], others_t[0] #i-ty gracz musi byc pierwszy
            others_b[0], others_b[i] = others_b[i], others_b[0]

            info = PlayerInfo(n, m, zone, players[i].top, players[i].bot, others_t, others_b) 
            move = players[i].get_move(info)
            newMoves.append(move) #zapisz na pozniej jaki ruch zrobil gracz i

            others_t[0], others_t[i] = others_t[i], others_t[0]
            others_b[0], others_b[i] = others_b[i], others_b[0]

        for i in range(players_count):
            players[i].top += newMoves[i].value #rekonstrukcja ruchow i aktualizacja pozycji
            players[i].bot += newMoves[i].value

        odw = [False] * players_count
        newPositions = [0] * players_count
        for i in range(players_count):
            if odw[i] == False:
                visited_indeces = []
                dfs(players, i)
            if(len(visited_indeces) > 1):  #mamy bitke
                sumOfSides = 0
                sqSum = 0
                for j in range(len(visited_indeces)):
                    sumOfSides += players[visited_indeces[j]].top.y - players[visited_indeces[j]].bot.y
                    sqSum += (players[visited_indeces[j]].top.y - players[visited_indeces[j]].bot.y) * (players[visited_indeces[j]].top.y - players[visited_indeces[j]].bot.y)
                los = random.randint(1, sumOfSides) #losowanie zwyciezcy walki pod katem wielkosci
                sumOfSides = 0
                for j in range(len(visited_indeces)):
                    sumOfSides += players[visited_indeces[j]].top.y - players[visited_indeces[j]].bot.y
                    if sumOfSides >= los: #j to zwyciezca
                        sqSum -= (players[visited_indeces[j]].top.y - players[visited_indeces[j]].bot.y) * (players[visited_indeces[j]].top.y - players[visited_indeces[j]].bot.y)
                        newPositions[visited_indeces[j]] = math.ceil(math.sqrt(sqSum)) #zwiekszamy zwyciezce
                        for l in range(len(visited_indeces)): #przegranych usuwamy
                            if(l == j):
                                continue
                            newPositions[visited_indeces[l]] = -1
                        break
        i = 0
        while(i < players_count): #realizacja zwiekszania/usuwania
            while(newPositions[i] == -1):
                newPositions.pop(i)
                players.pop(i)
                players_count -= 1
            players[i].bot += Pair(newPositions[i], -newPositions[i])
            i += 1
        
    zoneCurr += 1 #co iles klatek zone sie zmniejsza
    if zoneCurr % zoneFrequency == 0:
        zoneCurr = 0
        zone += 1
    
    i = 0
    while(i < players_count): #gdy gracz w strefie odejmij mu miejsce i jak jest za maly to go usun
        while players[i].top.x < zone or players[i].top.y > n - zone or players[i].bot.x > m - zone or players[i].bot.y < zone:
            players[i].bot += Pair(-1, 1)
            if players[i].top == players[i].bot:
                players.pop(i)
                players_count -= 1
            else:
                break
        i += 1


    return {}