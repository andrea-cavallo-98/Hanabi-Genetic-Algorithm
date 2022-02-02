#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
import GameData
import socket
from constants import *
import os
from genetic_player import Player
from rules import print_state

###
# File to define a client that interacts with the server to play
# according to the strategy evolved with the genetic algorithm
###



if len(argv) < 4:
    print("You need the player name to start the game.")
    #exit(-1)
    playerName = "Test" # For debug
    ip = HOST
    port = PORT
else:
    playerName = argv[3]
    ip = argv[1]
    port = int(argv[2])

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

def manageInput():
    global run
    global status
    while run:
        command = input()
        # Choose data to send
        if command == "exit":
            run = False
            os._exit(0)
        elif command == "ready" and status == statuses[0]:
            s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
        elif command == "show" and status == statuses[1]:
            s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
        elif command.split(" ")[0] == "discard" and status == statuses[1]:
            try:
                cardStr = command.split(" ")
                cardOrder = int(cardStr[1])
                s.send(GameData.ClientPlayerDiscardCardRequest(playerName, cardOrder).serialize())
            except:
                print("Maybe you wanted to type 'discard <num>'?")
                continue
        elif command.split(" ")[0] == "play" and status == statuses[1]:
            try:
                cardStr = command.split(" ")
                cardOrder = int(cardStr[1])
                s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())
            except:
                print("Maybe you wanted to type 'play <num>'?")
                continue
        elif command.split(" ")[0] == "hint" and status == statuses[1]:
            try:
                destination = command.split(" ")[2]
                t = command.split(" ")[1].lower()
                if t != "colour" and t != "color" and t != "value":
                    print("Error: type can be 'color' or 'value'")
                    continue
                value = command.split(" ")[3].lower()
                if t == "value":
                    value = int(value)
                    if int(value) > 5 or int(value) < 1:
                        print("Error: card values can range from 1 to 5")
                        continue
                else:
                    if value not in ["green", "red", "blue", "yellow", "white"]:
                        print("Error: card color can only be green, red, blue, yellow or white")
                        continue
                s.send(GameData.ClientHintData(playerName, destination, t, value).serialize())
            except:
                print("Maybe you wanted to type 'hint <type> <destinatary> <value>'?")
                continue
        elif command == "":
            print("[" + playerName + " - " + status + "]: ", end="")
        else:
            print("Unknown command: " + command)
            continue
        stdout.flush()

def play(s, playerName, player, strategy):
    """
    Player performs an action 
    """
    # Get state
    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
    state = s.recv(DATASIZE)
    state = GameData.GameData.deserialize(state)
    while type(state) is not GameData.ServerGameStateData:
        print(f"Received object of type: {type(state)}")
        state = s.recv(DATASIZE)
    # Choose move according to strategy and current state
    data = player.play(state, strategy)
    print(f"Player {playerName} performs action: {type(data)}")
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
    #Thread(target=manageInput).start()
    s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
    player = None
    strategy = None

    while run:
        
        dataOk = False
        data = s.recv(DATASIZE)
        if not data:
            continue
        data = GameData.GameData.deserialize(data)

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
                strategy = genetic_strategies[len(data.players)]
                first_player = data.players[0]

            if first_player == playerName: # If I have to start, I play a move
                play(s, playerName, player, strategy)

        if type(data) is GameData.ServerGameStateData:
            dataOk = True
            
        if type(data) is GameData.ServerActionInvalid:
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)

        if type(data) is GameData.ServerActionValid:
            dataOk = True
            # Only possible action is discard
            assert data.action == "discard"
            
            ### POSSIBLE BUG: could ignore other players' actions while waiting for my state
            if data.lastPlayer != playerName:
                # Get current state
                s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                state = s.recv(DATASIZE)
                state = GameData.GameData.deserialize(state)
                while type(state) is not GameData.ServerGameStateData:
                    print(f"Received object of type: {type(state)} while discarding")
                    state = s.recv(DATASIZE)
                # Update internal state according to performed action
                player.update_other_players(GameData.ClientPlayerDiscardCardRequest(data.lastPlayer, data.cardHandIndex), state)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy)

        if type(data) is GameData.ServerPlayerMoveOk:
            dataOk = True
            ### POSSIBLE BUG: could ignore other players' actions while waiting for my state

            if data.lastPlayer != playerName:
                # Get current state
                s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                state = s.recv(DATASIZE)
                state = GameData.GameData.deserialize(state)
                while type(state) is not GameData.ServerGameStateData:
                    print(f"Received object of type: {type(state)} while playing ok")
                    state = s.recv(DATASIZE)
                # Update internal state according to performed action
                player.update_other_players(GameData.ClientPlayerPlayCardRequest(data.lastPlayer, data.cardHandIndex), state)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy)

        if type(data) is GameData.ServerPlayerThunderStrike:
            dataOk = True
            ### POSSIBLE BUG: could ignore other players' actions while waiting for my state

            if data.lastPlayer != playerName:
                # Get current state
                s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                state = s.recv(DATASIZE)
                state = GameData.GameData.deserialize(state)
                while type(state) is not GameData.ServerGameStateData:
                    print(f"Received object of type: {type(state)} while playing wrong")
                    state = s.recv(DATASIZE)
                # Update internal state according to performed action
                player.update_other_players(GameData.ClientPlayerPlayCardRequest(data.lastPlayer, data.cardHandIndex), state)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy)
            
        if type(data) is GameData.ServerHintData:
            dataOk = True
            ### POSSIBLE BUG: could ignore other players' actions while waiting for my state

            if data.source != playerName:
                # Get current state
                s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                state = s.recv(DATASIZE)
                state = GameData.GameData.deserialize(state)
                while type(state) is not GameData.ServerGameStateData:
                    print(f"Received object of type: {type(state)} while hinting")
                    state = s.recv(DATASIZE)
                # Update internal state according to performed action
                if data.destination == playerName:
                    player.receive_hint(data.type, data.value, data.positions) 
                else:
                    player.update_other_players(GameData.ClientHintData(data.source, data.destination, data.type, data.value), state)
            # Check if it's my turn and, if so, play
            if data.player == playerName:
                play(s, playerName, player, strategy)
        
        if type(data) is GameData.ServerInvalidDataReceived:
            dataOk = True
            print(data.data)
        if type(data) is GameData.ServerGameOver:
            dataOk = True
            print(data.message)
            print(data.score)
            print(data.scoreMessage)
            stdout.flush()
            
            game_over = True
            
            print("Ready for a new game!")
        if not dataOk:
            print("Unknown or unimplemented data type: " +  str(type(data)))
        #print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()