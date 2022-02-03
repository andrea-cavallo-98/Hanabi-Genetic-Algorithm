#!/usr/bin/env python3

from sys import argv, stdout
import GameData
import socket
from constants import *
from genetic_player import Player

###
# File to define a client that interacts with the server to play
# according to the strategy evolved with the genetic algorithm
###


if len(argv) < 5:
    print("Wrong number of arguments. Expected <ip> <port> <playerName> <numberOfGames>")
    exit(-1)
else:
    playerName = argv[3]
    ip = argv[1]
    port = int(argv[2])
    number_of_games = int(argv[4])

run = True

statuses = ["Lobby", "Game", "GameHint"]

status = statuses[0]

hintState = ("", "")

# Define strategies of genetic player
genetic_strategies = {
    2 : [1.0, 15.0, 6.0, 22.0, 24.0, 25.0, 21.0, 9.0, 10.0, 27.0, 2.0, 7.0, 
                11.0, 5.0, 26.0, 16.0, 4.0, 23.0, 17.0, 13.0, 3.0, 28.0],
    3 : [ 5., 12.,  0. , 9.,22., 15., 11. , 1. , 4., 26., 24. ,20. ,28.],
    4 : [10.0, 1.0, 22.0, 15.0, 21.0, 13.0, 5.0, 26.0, 4.0, 6.0, 12.0, 16.0, 
                9.0, 23.0, 0.0, 7.0, 17.0, 2.0, 19.0, 28.0],
    5 : [4.0, 10.0, 0.0, 11.0, 1.0, 12.0, 15.0, 24.0, 7.0, 14.0, 17.0, 28.0]
}


def play(s, playerName, player, strategy, received_unexpected):
    """
    Player performs an action 
    """
    # Get state
    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
    state = s.recv(DATASIZE)
    state = GameData.GameData.deserialize(state)
    while type(state) is not GameData.ServerGameStateData:
        # If a different message is received, it is saved in a list and it will be processed later
        received_unexpected.append(state)
        state = s.recv(DATASIZE)
        state = GameData.GameData.deserialize(state)
    # Choose move according to strategy and current state
    data = player.play(state, strategy)
    # Perform action
    s.send(data.serialize())


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    request = GameData.ClientPlayerAddData(playerName)
    s.connect((HOST, PORT))
    s.send(request.serialize())
    data = s.recv(DATASIZE)
    data = GameData.GameData.deserialize(data)
    if type(data) is GameData.ServerPlayerConnectionOk:
        print("Connection accepted by the server. Welcome " + playerName)
    print("[" + playerName + " - " + status + "]: ", end="")

    # Send the "ready" message
    s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
    player = None
    strategy = None
    game_over = False
    first_player = None
    received_unexpected = []
    total_score = 0
    played_games = 0
    drawn_cards = 0

    while run:
        
        if game_over:
            game_over = False
            drawn_cards = 0
            player.reset()
            if first_player == playerName: # If I have to start, I play a move
                play(s, playerName, player, strategy, received_unexpected)

        dataOk = False
        if len(received_unexpected) > 0:
            data = received_unexpected.pop(0)
        else:
            data = s.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)

        if not data:
            continue
        
        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            dataOk = True
            print("Ready: " + str(data.acceptedStartRequests) + "/"  + str(data.connectedPlayers) + " players")
            data = s.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)

        if type(data) is GameData.ServerStartGameData:
            dataOk = True
            print("Game start!")
            s.send(GameData.ClientPlayerReadyData(playerName).serialize())
            status = statuses[1]
            # Initialize player object and select strategy corresponding to number of players
            if player == None:
                player = Player(playerName, data.players)
                print(f"Selecting strategy for {len(data.players)} players")
                strategy = genetic_strategies[len(data.players)]
                first_player = data.players[0]

            if first_player == playerName: # If I have to start, I play a move
                play(s, playerName, player, strategy, received_unexpected)

        if type(data) is GameData.ServerGameStateData:
            dataOk = True
            
        if type(data) is GameData.ServerActionInvalid:
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)

        if type(data) is GameData.ServerActionValid:
            drawn_cards += 1
            dataOk = True
            # Only possible action is discard
            assert data.action == "discard"
            
            if data.lastPlayer != playerName:
                # Update internal state according to performed action
                player.update_other_players(GameData.ClientPlayerDiscardCardRequest(data.lastPlayer, data.cardHandIndex), drawn_cards)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy, received_unexpected)

        if type(data) is GameData.ServerPlayerMoveOk:
            drawn_cards += 1
            dataOk = True

            if data.lastPlayer != playerName:
                player.update_other_players(GameData.ClientPlayerPlayCardRequest(data.lastPlayer, data.cardHandIndex), drawn_cards)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy, received_unexpected)

        if type(data) is GameData.ServerPlayerThunderStrike:
            drawn_cards += 1
            dataOk = True

            if data.lastPlayer != playerName:
                # Update internal state according to performed action
                player.update_other_players(GameData.ClientPlayerPlayCardRequest(data.lastPlayer, data.cardHandIndex), drawn_cards)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy, received_unexpected)
            
        if type(data) is GameData.ServerHintData:
            dataOk = True

            if data.sender != playerName:
                # Update internal state according to performed action
                if data.destination == playerName:
                    player.receive_hint(data.type, data.value, data.positions) 
                else:
                    player.update_other_players(data, drawn_cards)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy, received_unexpected)
        
        if type(data) is GameData.ServerInvalidDataReceived:
            dataOk = True
            print(data.data)
        if type(data) is GameData.ServerGameOver:
            dataOk = True
            print("Game over! Score: ", data.score)
            stdout.flush()
            
            game_over = True
            played_games += 1
            total_score += data.score
            if played_games == number_of_games:
                print("\n\n**** GAMES ARE OVER ****")
                print(f" Average score: {total_score / number_of_games}")
                break
                
        if not dataOk:
            print("Unknown or unimplemented data type: " +  str(type(data)))
        stdout.flush()