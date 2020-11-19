*[Прочитайте это на русском.](README.md)*

# Mafia Host
[This repository](https://gitlab.com/r4rdsn/mafia_host_bot) contains a source code for a [@mafia_host_bot](https://t.me/mafia_host_bot) Telegram bot.  
Mafia Host can host party games of the famous mafia in groups or supergroups.


# How to use
Add [@mafia_host_bot](https://t.me/mafia_host_bot) to your group or supergroup, give it permission to delete messages and use commands listed below to create 
and start the game.


# Available commands
* ```/create``` - create a request for a mafia game  
* ```/cancel``` - delete a request for a mafia game  
* ```/start``` - start a game from existing request  
* ```/skip``` - create a voting to skip day discussion  
* ```/end``` - create a voting to end the mafia game  
* ```/croco``` - start crocodile game  
* ```/gallows``` - start hangman game  
* ```/stats``` - print statistics  
* ```/rating``` - print rating  
* ```/help``` - print help text


# Rules 
There are four roles in this version of Mafia Host:  
* __Innocent__ - a player who doesn't have special abilities;  
* __Mafioso__ - a player who may kill one innocent every night;  
* __Don__ - a mafioso who may learn whether one player is sheriff or not every night;  
* __Sheriff__ - an innocent who may learn the team of one player every night;

Mafia Host uses callback buttons to provide smooth gameplay, you don't have to switch chats or send anything to make your turn.  

To give mafia's turns, shooting approach is used. Firstly, at the beginning of the game, don is giving the order to his teammates in which the mafia should 
shoot players. Every night, there is a phase of shooting, when all members of mafia should press inline button at the same time when bot's messages have name 
of the one they should kill. If they succeed, this player will die the next morning. The order itself doesn't influence mafia's hit, so you may use this to 
come up with your tactic.  

It is strongly recommended to use a feature that allows Mafia Host to delete any message that are not sent from dying player during his last words or during 
the 3-minute-long common discussion. To turn it on, promote it to administrator with permission to delete messages.  


# Rules of crocodile
Rules of crocodile in this version of Mafia Host are similar to rules of the board game "Alias". Player has to explain a random noun in 2 minutes without using words with same root or derivatives. To say the word one should just type it in the chat.  


# Rules of hangman
Players have to guess a random noun within 6 attempts by letters of which it is composed. To suggest the letter or the word one should just type it in the chat.


# Rating
Each game influences players' statistics, which rating comprises: 5 players of mafia and 3 players of crocodile. By default each player of winning team in mafia gets 1 point and each player of losing team in mafia loses 1 point; after each guessed word in crocodile player who was explaining the word gets 0.12 points and player who guessed the word gets 0.04 points.


# Instruction for installation and startup on GNU/Linux server
* Install [Python](https://www.python.org/downloads) version no less than 3.6.0
* Clone repository:  
```$ git clone https://gitlab.com/r4rdsn/mafia_host_bot```
* Install requirements:  
```# pip install -r mafia_host_bot/requirements.txt```
* Copy file ```config.py.sample``` in local repository:  
```$ cp config.py.sample config.py```
* Personalize file ```config.py```:  
```$ $EDITOR config.py``` (replacing ```$EDITOR``` with preferable text editor)
* Install and start MongoDB server.
* Start bot:  
```$ python mafia_host_bot```


# License
Mafia Host is distributed under the terms of [GNU General Public License v3](COPYING).
