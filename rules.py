import random

def print_state(data):
    print("Current player: " + data.currentPlayer)
    print("Player hands: ")
    for p in data.players:
        print(p.toClientString())
    print("Table cards: ")
    for pos in data.tableCards:
        print(pos + ": [ ")
        for c in data.tableCards[pos]:
            print(c.toClientString() + " ")
        print("]")
    print("Discard pile: ")
    for c in data.discardPile:
        print("\t" + c.toClientString())            
    print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
    print("Storm tokens used: " + str(data.usedStormTokens) + "/3")

###
# Select action according to a strategy
###


def select_action(self, strategy, state):
    action = None
    cardOrder = None
    t = None
    val = None
    dest = None

    for rule in strategy:
        #print(rule)
        if rule == 0:
            action, cardOrder = play_if_certain(self, state)
        elif rule == 1:
            action, cardOrder = play_probably_safe_card(self, state, 0.8)
        elif rule == 2:
            action, cardOrder = play_probably_safe_card(self, state, 0.6)
        elif rule == 3:
            action, cardOrder = play_probably_safe_card(self, state, 0.4)
        elif rule == 4:
            action, cardOrder = play_probably_safe_card_with_lives(self, state, 0.8)
        elif rule == 5:
            action, cardOrder = play_probably_safe_card_with_lives(self, state, 0.6)
        elif rule == 6:
            action, cardOrder = play_probably_safe_card_with_lives(self, state, 0.4)
        elif rule == 7:
            action, cardOrder = play_recently_hinted(self, state, 0.01, 0)
        elif rule == 8:
            action, cardOrder = play_recently_hinted(self, state, 0.2, 0)
        elif rule == 9:
            action, cardOrder = play_recently_hinted(self, state, 0.01, 1)
        elif rule == 10:
            action, cardOrder = play_recently_hinted(self, state, 0.2, 1)
        elif rule == 11:
            action, cardOrder = play_most_probable_if_deck_empty(self, state)
        elif rule == 12:
            action, t, val, dest = complete_tell_playable_card(self, state)
        elif rule == 13:
            action, t, val, dest = tell_about_ones(self, state)
        elif rule == 14:
            action, t, val, dest = tell_about_fives(self, state)
        elif rule == 15:
            action, t, val, dest = tell_playable_card(self, state)
        elif rule == 16:
            action, t, val, dest = tell_useless_card(self, state)
        elif rule == 17:
            action, t, val, dest = tell_most_information(self, state)
        elif rule == 18:
            action, t, val, dest = tell_random_hint(self, state)
        elif rule == 19:
            action, t, val, dest = tell_unknown_card(self, state)
        elif rule == 20:
            action, t, val, dest = tell_unambiguous(self, state)
        elif rule == 21:
            action, cardOrder = discard_random_card(self, state)
        elif rule == 22:
            action, cardOrder = discard_useless_card(self, state)
        elif rule == 23:
            action, cardOrder = discard_highest_known(self, state)
        elif rule == 24:
            action, cardOrder = discard_unidentified_card(self, state)
        elif rule == 25:
            action, cardOrder = discard_probably_useless(self, state, 0.8)
        elif rule == 26:
            action, cardOrder = discard_probably_useless(self, state, 0.6)
        elif rule == 27:
            action, cardOrder = discard_probably_useless(self, state, 0.4)
        elif rule == 28:
            action = random_hint_discard(self, state)
            if action[0] == "hint":
                t = action[1]
                val = action[2]
                dest = action[3]
                action = action[0]
            else:
                cardOrder = action[1]
                action = action[0]

        if action is not None:
            """
            print()
            print("---------------------------------")
            print(f"--- Played rule number {rule} ---")
            print(f"--- Player {self.id} makes action {action}: cardOrder {cardOrder}, type {t}, val {val}, dest {dest}")
            print("---------------------------------")
            print()
            """
            break
    if action is None:
        print("+++ ACTION IS NONE +++")
        print("Strategy: ", strategy)
        print_state(state)
    return action, cardOrder, t, val, dest




###
# Rules
###

def is_playable(color, value, state):
    return len(state.tableCards[color]) == value - 1

def is_useless(color, value, state):
    if len(state.tableCards[color]) > value - 1: # card already played
        return True
    # count how many cards with same color have been discarded
    discarded = {}
    for v in range(1, value):
        discarded[v] = 0
    for c in state.discardPile:
        if c.color == color and c.value < value:
            discarded[c.value] += 1
    for v in range(1, value):
        if v == 1 and discarded[v] == 3:
            return True
        elif discarded[v] == 2:
            return True
    return False         

def play_if_certain(self, state):
    playable_cards = [i for i in range(self.n_cards) if self.cards[i].is_playable(state.tableCards)]
    if playable_cards:
        return "play", playable_cards[0]
    else:
        return None, None

# play card if probability of being playable is > prob
def play_probably_safe_card(self, state, prob):
    prob_playable_cards = [c.score_playable(state.tableCards) for c in self.cards]
    if max(prob_playable_cards) >  prob:
        return "play", prob_playable_cards.index(max(prob_playable_cards))
    else:
        return None, None

# play card if probability of being playable is > prob and lives > 1
def play_probably_safe_card_with_lives(self, state, prob):
    if state.usedStormTokens >= 2:
        return None, None
    prob_playable_cards = [c.score_playable(state.tableCards) for c in self.cards]
    if max(prob_playable_cards) >  prob:
        return "play", prob_playable_cards.index(max(prob_playable_cards))
    else:
        return None, None

def play_recently_hinted(self, state, prob, lives):
    if state.usedStormTokens >= 3 - lives or len(self.recent_hints) == 0: 
        return None, None
    highest_prob = 0.0
    best_card = None
    for h in self.recent_hints: 
        score = self.cards[h].score_playable(state.tableCards)
        if score > highest_prob:
            highest_prob = score
            best_card = h
    if highest_prob >= prob:
        return "play", best_card
    return None, None

def play_most_probable_if_deck_empty(self, state):
    if state.usedStormTokens >= 2:
        return None, None
    if self.compute_played_cards(state) == 50:
        prob_playable_cards = [c.score_playable(state.tableCards) for c in self.cards]
        return "play", prob_playable_cards.index(max(prob_playable_cards))
    return None, None
    

# hint about a partially known playable card
def complete_tell_playable_card(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    for p in state.players:
        # find player in local list
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        # try color hint
        available_colors = set([c.color for c in p.hand])
        for c in available_colors:
            score = loc_p.score_hint("color", c, [i for i in range(len(p.hand)) if p.hand[i].color == c], state)
            if score == 100: # hint made card playable!
                return "hint", "color", c, p.name
        # try value hint
        available_values = set([c.value for c in p.hand])
        for v in available_values:
            score = loc_p.score_hint("value", v, [i for i in range(len(p.hand)) if p.hand[i].value == v], state)
            if score == 100:
                return "hint", "value", v, p.name
        return None, None, None, None

# hint about ones
def tell_about_ones(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    max_ones = 0
    p_max_ones = ""
    for p in state.players:
        # find player in local list
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        available_values = [c.value for c in p.hand]
        ones = available_values.count(1)
        if ones > max_ones:
            max_ones = ones
            p_max_ones = p.name
    if max_ones != 0:
        return "hint", "value", 1, p_max_ones
    else:
        return None, None, None, None

# hint about fives
def tell_about_fives(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    max_fives = 0
    p_max_fives = ""
    for p in state.players:
        # find player in local list
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        available_values = [c.value for c in p.hand]
        fives = available_values.count(5)
        if fives > max_fives:
            max_fives = fives
            p_max_fives = p.name
    if max_fives != 0:
        return "hint", "value", 5, p_max_fives
    else:
        return None, None, None, None

# tell a player about a playable card
def tell_playable_card(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    for p in state.players:
        # find player in local list
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        for i, c in enumerate(p.hand):
            if is_playable(c.color, c.value, state) and not loc_p.cards[i].is_playable(state.tableCards):
                if len(loc_p.cards[i].value) != 1:
                    return "hint", "value", c.value, p.name
                if len(loc_p.cards[i].color) != 1:
                    return "hint", "color", c.color, p.name
    return None, None, None, None

# tell a player about a useless card
def tell_useless_card(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    for p in state.players:
        # find player in local list
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        #if len(p.hand) != len(loc_p.cards):
        #    print("Error in Tell Useless: Players: ", len(state.players), " Cards: ", len(loc_p.cards), len(p.hand), " Played cards: ", self.compute_played_cards(state))
        for i, c in enumerate(p.hand):
            if is_useless(c.color, c.value, state):
                if len(loc_p.cards[i].value) != 1:
                    return "hint", "value", c.value, p.name
                if len(loc_p.cards[i].color) != 1:
                    return "hint", "color", c.color, p.name
    return None, None, None, None

# tell hint that gives most information
def tell_most_information(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    best_score = 0
    best_hint = None
    for p in state.players:
        # find player in local list
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        # try color hint
        available_colors = set([c.color for c in p.hand])
        for c in available_colors:
            score = loc_p.score_hint("color", c, [i for i in range(len(p.hand)) if p.hand[i].color == c], state)
            if score > best_score:
                best_score = score
                best_hint = { "t": "color", "val": c, "dest": p.name }
        # try value hint
        available_values = set([c.value for c in p.hand])
        for v in available_values:
            score = loc_p.score_hint("value", v, [i for i in range(len(p.hand)) if p.hand[i].value == v], state)
            if score > best_score:
                best_score = score
                best_hint = { "t": "value", "val": v, "dest": p.name }
    if best_hint is not None:
        return "hint", best_hint["t"], best_hint["val"], best_hint["dest"]
    return None, None, None, None

# give random hint 
def tell_random_hint(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    p = random.choice(state.players)
    t = random.choice(["color", "value"])

    if t == "color":
        available_colors = list(set([c.color for c in p.hand]))
        v = random.choice(available_colors)
    else:    
        available_values = list(set([c.value for c in p.hand]))
        v = random.choice(available_values)
    
    return "hint", t, v, p.name
    
# tell hint about unknown card
def tell_unknown_card(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    p = random.choice(state.players)
    # find player in local list
    for loc_p in self.other_players:
        if str(loc_p.id) == p.name:
            break
    for i, c in enumerate(loc_p.cards):
        #print(len(loc_p.cards), len(p.hand))
        #if len(loc_p.cards) != len(p.hand):
        #    print("Error in Tell Unknown: Current player: ", p.name, " Players: ", len(state.players), " Cards: ", len(loc_p.cards), len(p.hand), " Played cards: ", self.compute_played_cards(state))
        #    print_state(state)
        #    for c in self.cards:
        #        print(c.value, c.color)
        if len(c.value) != 1:
            return "hint", "value", p.hand[i].value, p.name
        if len(c.color) != 1:
            return "hint", "color", p.hand[i].color, p.name
    return None, None, None, None

# tell card that maximizes probability of playable cards for a player
def tell_unambiguous(self, state):
    if state.usedNoteTokens >= 8:
        return None, None, None, None
    best_score = 0.0
    best_hint = None
    for p in state.players:
        for loc_p in self.other_players:
            if str(loc_p.id) == p.name:
                break
        # try color hint
        available_colors = set([c.color for c in p.hand])
        for c in available_colors:
            score = loc_p.score_unambiguous_hint("color", c, [i for i in range(len(p.hand)) if p.hand[i].color == c], 
                                                    state, [i for i in range(len(p.hand)) if is_playable(p.hand[i].color, p.hand[i].value, state)])
            #print(f"Score for hint color: {c}, player: {p.name} --> score: {score}")
            if score > best_score:
                best_score = score
                best_hint = { "t": "color", "val": c, "dest": p.name }
        # try value hint
        available_values = set([c.value for c in p.hand])
        for v in available_values:
            score = loc_p.score_unambiguous_hint("value", v, [i for i in range(len(p.hand)) if p.hand[i].value == v], 
                                                    state, [i for i in range(len(p.hand)) if is_playable(p.hand[i].color, p.hand[i].value, state)])
            #print(f"Score for hint value: {v}, player: {p.name} --> score: {score}")
            if score > best_score:
                best_score = score
                best_hint = { "t": "value", "val": v, "dest": p.name }
    if best_hint is not None:
        return "hint", best_hint["t"], best_hint["val"], best_hint["dest"]
    return None, None, None, None

# discard random card
def discard_random_card(self, state):
    if state.usedNoteTokens == 0:
        return None, None
    return "discard", random.randint(0, len(self.cards) - 1)

# discard useless card (already played or not playable anymore)
def discard_useless_card(self, state):
    if state.usedNoteTokens == 0:
        return None, None
    for i, c in enumerate(self.cards):
        if c.is_useless(state):
            return "discard", i
    return None, None

# discard card with highest known value
def discard_highest_known(self, state):
    if state.usedNoteTokens == 0:
        return None, None
    highest = 0
    highest_i = None
    for i, c in enumerate(self.cards):
        if len(c.value) == 1:
            if c.value[0] > highest:
                highest = c.value[0]
                highest_i = i
    if highest_i is None:
        return None, None
    return "discard", highest_i

# discard unidentified card
def discard_unidentified_card(self, state):
    if state.usedNoteTokens == 0:
        return None, None
    for i, c in enumerate(self.cards):
        if len(c.value) > 1 and len(c.color) > 1:
            return "discard", i
    return None, None

# discard card that is useless with probability > prob
def discard_probably_useless(self, state, prob):
    if state.usedNoteTokens == 0:
        return None, None
    for i, c in enumerate(self.cards):
        if c.score_useless(state) > prob:
            return "discard", i
    return None, None

# random hint or discard -> always returns something!!
def random_hint_discard(self, state):
    action = None
    if state.usedNoteTokens == 0: # forced to hint
        action = "hint" 
    if state.usedNoteTokens == 8: # forced to discard
        action = "discard"
    if action is None:
        action = random.choice(["hint", "discard"])
    if action == "hint":
        return tell_random_hint(self, state)
    else:
        return discard_random_card(self, state)


