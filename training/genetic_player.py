import random
import GameData
from copy import deepcopy
import rules


class Card(object):
    def __init__(self) -> None:
        super().__init__()
        self.color = ["red", "yellow", "green", "blue", "white"]
        self.value = [1, 2, 3, 4, 5]

    def assign_color(self, c):
        self.color = [c]

    def remove_color(self, c):
        if len(self.color) > 1:
            if c in self.color:
                self.color.remove(c)

    def assign_value(self, v):
        self.value = [v]

    def remove_value(self, v):
        if len(self.value) > 1:
            if v in self.value:
                self.value.remove(v)

    def score_playable(self, tableCards):
        # probability of card being playable
        score = 0
        for c in self.color:
            for v in self.value:
                if len(tableCards[c]) == v - 1:
                    score += 1
        return score / (len(self.color) * len(self.value))

    def is_playable(self, tableCards):
        if len(self.value) > 1:
            return False
        for c in self.color:
            if len(tableCards[c]) != self.value[0] - 1:
                return False
        return True 

    def is_useless(self, state):
        for c in self.color:
            for val in self.value:
                if len(state.tableCards[c]) > val - 1: # card already played
                    continue
                # count how many cards with same color have been discarded
                discarded = {}
                for v in range(1, val):
                    discarded[v] = 0
                for c in state.discardPile:
                    if c.color == c and c.value < val:
                        discarded[c.value] += 1
                for v in range(1, val):
                    if v == 1 and discarded[v] == 3:
                        continue
                    elif discarded[v] == 2:
                        continue
                return False
        return True                        

    def score_useless(self, state):
        score = 0
        for col in self.color:
            for val in self.value:
                if len(state.tableCards[col]) > val - 1: # card already played
                    score += 1
                    continue
                # count how many cards with same color have been discarded
                discarded = {}
                for v in range(1, val):
                    discarded[v] = 0
                for c in state.discardPile:
                    if c.color == col and c.value < val:
                        discarded[c.value] += 1
                for v in range(1, val):
                    if v == 1 and discarded[v] == 3:
                        score += 1
                        continue
                    elif discarded[v] == 2:
                        score += 1
                        continue
        return score / (len(self.color) * len(self.value))               


class OtherPlayer(object):
    def __init__(self, id, num_players) -> None:
        super().__init__()
        self.id = id
        self.num_players = num_players
        self.cards = []
        if num_players < 4:
            self.n_cards = 5
        else:
            self.n_cards = 4
        for _ in range(self.n_cards):
            self.cards.append(Card())

    def remove_card(self, pos, played_cards):
        del self.cards[pos]
        if played_cards < 50: 
            self.cards.append(Card())
        else:
            self.n_cards -= 1

    def receive_hint(self, t, value, positions):
        #print(f"--- Player {self.id} receiving hint: type {t}, v {value}, positions {positions}")
        if t == "color":
            for p in range(self.n_cards):
                if p in positions:
                    self.cards[p].assign_color(value)
                else:
                    self.cards[p].remove_color(value)

        elif t == "value":
            for p in range(self.n_cards):
                if p in positions:
                    self.cards[p].assign_value(value)
                else:
                    self.cards[p].remove_value(value)

    def score_hint(self, t, value, positions, state):
        score = 0

        cards_copy = deepcopy(self.cards)

        if t == "color":
            for p in range(self.n_cards):
                if p in positions:
                    score += len(cards_copy[p].color) - 1
                    cards_copy[p].assign_color(value)
                else:
                    if value in cards_copy[p].color:
                        score += 1
                        cards_copy[p].remove_color(value)

        elif t == "value":
            for p in range(self.n_cards):
                if p in positions:
                    score += len(cards_copy[p].value) - 1
                    cards_copy[p].assign_value(value)
                else:
                    if value in cards_copy[p].value:
                        score += 1
                        cards_copy[p].remove_value(value)

        # hint made card playable (which was not known as playable before)
        if [i for i in range(len(cards_copy)) if cards_copy[i].is_playable(state.tableCards) and not self.cards[i].is_playable(state.tableCards)]:
            return 100
        return score
    
    
    def score_unambiguous_hint(self, t, value, positions, state, playable):
        score = 0.0

        cards_copy = deepcopy(self.cards)

        if t == "color":
            for p in range(self.n_cards):
                if p in positions:
                    cards_copy[p].assign_color(value)
                else:
                    if value in cards_copy[p].color:
                        cards_copy[p].remove_color(value)
                if not self.cards[p].is_playable(state.tableCards):
                    # if player already knows card is playable, hint is not useful
                    if p in playable:
                        score += cards_copy[p].score_playable(state.tableCards)
                    else:
                        score -= cards_copy[p].score_playable(state.tableCards)

        elif t == "value":
            for p in range(self.n_cards):
                if p in positions:
                    cards_copy[p].assign_value(value)
                else:
                    if value in cards_copy[p].value:
                        cards_copy[p].remove_value(value)
                if not self.cards[p].is_playable(state.tableCards):
                    # if player already knows card is playable, hint is not useful
                    if p in playable:
                        # if player already knows card is playable, hint is not useful
                        score += cards_copy[p].score_playable(state.tableCards)
                    else:
                        score -= cards_copy[p].score_playable(state.tableCards)

        return score



class Player(object):
    def __init__(self, id, num_players) -> None:
        super().__init__()
        self.id = id
        self.num_players = num_players
        self.cards = []
        if num_players < 4:
            self.n_cards = 5
        else:
            self.n_cards = 4
        for _ in range(self.n_cards):
            self.cards.append(Card())
        
        self.other_players = [OtherPlayer(i, num_players) for i in range(num_players) if i != id]
        self.recent_hints = []

    def compute_played_cards(self, state):
        played_cards = self.n_cards + len(state.discardPile) 
        for p in state.players:
            played_cards += len(p.hand)
        for pos in state.tableCards:
            played_cards += len(state.tableCards[pos])
        return played_cards




    def play(self, state, strategy):
        
        action = None
        cardOrder = None
        t = None
        val = None
        dest = None

        action, cardOrder, t, val, dest = rules.select_action(self, strategy, state)
        played_cards = self.compute_played_cards(state)

        # Perform selected action
        if action == "discard":
            del self.cards[cardOrder]
            if played_cards < 50:
                self.cards.append(Card())
            else:
                self.n_cards -= 1
            action = GameData.ClientPlayerDiscardCardRequest(str(self.id), cardOrder)

        elif action == "play":
            del self.cards[cardOrder]
            if played_cards < 50:
                self.cards.append(Card())
            else:
                self.n_cards -= 1
            action = GameData.ClientPlayerPlayCardRequest(str(self.id), cardOrder)

        elif action == "hint":

            for p in state.players:
                if p.name == dest:
                    break

            for loc_p in self.other_players:
                if str(loc_p.id) == dest:
                    if t == "value":
                        loc_p.receive_hint(t, val, [i for i in range(len(p.hand)) if p.hand[i].value == val])
                    elif t == "color":
                        loc_p.receive_hint(t, val, [i for i in range(len(p.hand)) if p.hand[i].color == val])
                    break
            action = GameData.ClientHintData(str(self.id), dest, t, val)

        self.recent_hints = []

        return action

    def receive_hint(self, t, value, positions):
        if t == "color":
            for p in range(self.n_cards):
                if p in positions:
                    self.cards[p].assign_color(value)
                    self.recent_hints.append(p)
                else:
                    self.cards[p].remove_color(value)

        elif t == "value":
            for p in range(self.n_cards):
                if p in positions:
                    self.cards[p].assign_value(value)
                    self.recent_hints.append(p)
                else:
                    self.cards[p].remove_value(value)

    def update_other_players(self, data, state):
        if type(data) == GameData.ClientPlayerDiscardCardRequest:
            for loc_p in self.other_players:
                if str(loc_p.id) == data.sender:
                    break
            loc_p.remove_card(data.handCardOrdered, self.compute_played_cards(state))
        
        elif type(data) == GameData.ClientPlayerPlayCardRequest:
            for loc_p in self.other_players:
                if str(loc_p.id) == data.sender:
                    break
            loc_p.remove_card(data.handCardOrdered, self.compute_played_cards(state))
        
        elif type(data) == GameData.ServerHintData:
            if int(data.destination) == self.id:
                self.receive_hint(data.type, data.value, data.positions)
            else:
                for loc_p in self.other_players:
                    if str(loc_p.id) == data.destination:
                        break
                loc_p.receive_hint(data.type, data.value, data.positions)


