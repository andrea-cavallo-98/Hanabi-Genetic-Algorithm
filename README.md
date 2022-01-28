# Hanabi-Genetic-Algorithm

Final project for the course `Computational Intelligence`: implementation of a genetic algorithm using an island model to evolve a player for the cooperative game Hanabi. The rules of the game can be found [here](https://www.spillehulen.dk/media/102616/hanabi-card-game-rules.pdf).

## Usage
To start the server for the game:
```
python server.py <min-number-of-players>
```
To start the client for the genetic player:
```
python client.py <IP-address> <port> <player-name>
```
The player will automatically send a message to the server saying he is ready to play and he will perform his move when his turn comes. To create a manually controlled player, which will wait for user input before playing:
```
python client_human.py <IP-address> <port> <player-name>
```
It is possible to create games with any combination of genetic and human players.

## Algorithm
The folder [`training`](training) contains the files to train the genetic algorithm to evolve the player. In particular, the file containing the algorithm is [`island_model_ga.py`](training/island_model_ga.py). The goal of the algorithm is to select the best order for a set of predefined rules to play the game. The performances are evaluated by simulating 50 games for each individual and averaging the results. Individuals are evaluated both in self-play and in mixed-play (i.e. playing with players using different strategies).
