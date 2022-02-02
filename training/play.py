
from game import Game
from genetic_player import Player
import GameData
from itertools import combinations

###
# Function to simulate Hanabi games. It is used to evaluate the fitness of the
# individuals in the genetic algorithm
###


# Define some strategies for mixed evaluation
possible_strategies = [
    [0, 22, 15, 19, 21], # Osawa outer
    [0, 15, 22, 21, 28], # Cautios
    [11, 0, 5, 15, 16, 22, 18, 21], # Piers
    [2, 0, 22, 15, 16, 17, 27, 21, 28] # Van den Bergh
] 

# Evolved strategies of genetic player
genetic_strategies = {
    2 : [1.0, 15.0, 6.0, 22.0, 24.0, 25.0, 21.0, 9.0, 10.0, 27.0, 2.0, 7.0, 
                11.0, 5.0, 26.0, 16.0, 4.0, 23.0, 17.0, 13.0, 3.0, 28.0],
    3 : [ 5., 12.,  0. , 9.,22., 15., 11. , 1. , 4., 26., 24. ,20. ,28.],
    4 : [10.0, 1.0, 22.0, 15.0, 21.0, 13.0, 5.0, 26.0, 4.0, 6.0, 12.0, 16.0, 
                9.0, 23.0, 0.0, 7.0, 17.0, 2.0, 19.0, 28.0],
    5 : [4.0, 10.0, 0.0, 11.0, 1.0, 12.0, 15.0, 24.0, 7.0, 14.0, 17.0, 28.0]
}


def evaluate_player(it, strategy, evaluation_type = "mirror"):
    score = 0
    range_players = range(2,3)
    for NUM_PLAYERS in range_players:

        if type(strategy) == list: # only one strategy as parameter
            cur_strategy = strategy
        elif type(strategy) == dict: # one strategy per each possible number of players
            cur_strategy = strategy[NUM_PLAYERS]

        if evaluation_type == "mixed":
            strategies_combinations = list(combinations(possible_strategies, NUM_PLAYERS - 1))
            strategies_combinations.append([cur_strategy for _ in range(NUM_PLAYERS - 1)]) # Play also with yourself

        for n_it in range(it):
            game = Game()
            players = []
            players_strategies = [cur_strategy for _ in range(NUM_PLAYERS)]

            if evaluation_type == "mixed":
                # select a given combination of players for mixed evaluation (all combinations will be tried)
                players_strategies[1:] = strategies_combinations[n_it % len(strategies_combinations)]
                
            for id in range(NUM_PLAYERS):    
                players.append(Player(id, NUM_PLAYERS))
                game.addPlayer(str(id))
 
            game.start(n_it)

            ### Play game
            current_player = 0
            while not game.isGameOver():
                
                state, _ = game.satisfyRequest(GameData.ClientGetGameStateRequest(str(current_player)), str(current_player))
                data = players[current_player].play(state, players_strategies[current_player])

                if type(data) == GameData.ClientHintData: # first perform action, then update other players' states
                    singleData, multipleData = game.satisfyRequest(data, str(current_player))
                    for p in range(len(players)):
                        if p != current_player:
                            players[p].update_other_players(multipleData, None)
                else: # first update other players' states, then perform action
                    for p in range(len(players)):
                        if p != current_player:
                            players[p].update_other_players(data, state)
                    singleData, multipleData = game.satisfyRequest(data, str(current_player))

                if singleData is not None:
                    if type(singleData) is GameData.ServerActionInvalid:
                        print(singleData.message)
                    if type(singleData) is GameData.ServerInvalidDataReceived:
                        print(singleData.data)
                if multipleData is not None:
                    if type(multipleData) is GameData.ServerGameOver:
                        score += multipleData.score

                # Move on to next turn
                current_player = (current_player + 1) % NUM_PLAYERS
    return - score / (it * len(range_players))

if __name__ == "__main__":

    #print(evaluate_player(100, genetic_strategies, "mirror"))

    print(evaluate_player(100, genetic_strategies, "mixed"))
