"""
Any action that modifies the database.  Form updates are handled by web2py.

These functions should not return data.
"""

from atools import *

def killPlayer (player_id, user=-1):
	"""
	Sets a row from db.players to DEAD.  This eliminates or zombifies a player.

	Keyword Arguments:
	player_id  -- id of the row in db.players that needs to be DEAD
	user_id    -- the current user to check permissions
	           -- the default of -1 means don't check user permissions
	"""

	from gluon import current
	db = current.db

	#the player should exist
	if db.player[player_id] is None:
		return

	#don't check permissions
	if user == -1:
		pass
	#the host has permission to edit the player
	elif db((db.player.id==player_id)&(db.player.game_id==db.game.id)&(db.game.host_id==user.id)).count() > 0:
		pass
	#the player has permission to edit the player
	elif db.player(player_id).player_id == user.id:
		pass
	#no one else should be able to edit the player
	else:
		return

	#Reassign new target here?

	#kill the player
	player = db.player(player_id)
	player.update_record(status = "DEAD")
	return

def kickPlayer (player_id, user=-1):
	"""
	Deletes a row from db.players.  This causes a player to leave a game.

	Keyword Arguments:
	player_id  -- id of the row in db.players that needs to be deleted
	user_id    -- the current user to check permissions
	           -- the default of -1 means don't check user permissions
	"""

	from gluon import current
	db = current.db

	#the player should exist
	if db.player[player_id] is None:
		return

	#don't check permissions
	if user == -1:
		pass
	#the host has permission to edit the player
	elif db((db.player.id==player_id)&(db.player.game_id==db.game.id)&(db.game.host_id==user.id)).count() > 0:
		pass
	#the player has permission to edit the player
	elif db.player(player_id).player_id == user.id:
		pass
	#no one else should be able to edit the player
	else:
		return

	#Reassign new target here?

	#kick the player
	db(db.player.id == player_id).delete()
	return

def deleteGame (game_id, user):
	"""
	Deletes a row from db.game.  This deletes the game.

	Keyword Arguments:
	game_id -- id of the row in db.game that needs to be deleted
	user_id -- the current user to check permissions
	"""

	from gluon import current
	db = current.db

	#the game should exist
	if db.game[game_id] is None:
		return

	#the host has permission to delete the game
	if db.game[game_id].host_id == user.id:
		pass
	#no one else should be able to delete the game
	else:
		return

	#Delete the game
	db(db.game.id==game_id).delete()
	return

def joinGame (game_id, user):
	"""
	Adds a row to db.players.  This causes a player to join a game.

	Keyword Arguments:
	game_id -- id of the row in db.game
	user_id -- the user that will be added to the game
	"""

	from gluon import current
	db = current.db

	db.player.insert(game_id=game_id, player_id=user.id, target_id=user.id, status="ALIVE")
	return

def leaveGame (game_id, user):
	"""
	Deletes a row from db.players.  This causes a player to leave a game.

	Keyword Arguments:
	game_id -- id of the row in db.game
	user_id -- the user that will leave the game
	"""

	from gluon import current
	db = current.db

	db( (db.player.player_id==user.id) & (db.player.game_id==game_id) ).delete()
	return




def startGameAssassins(game_id, user):
	"""
	Starts a game using the assassins rule set.  Exits if the game is invalid.

	Keyword Arguments:
	game_id  -- id of the game that needs to be started
	user_id  -- the current user to check permissions
	"""

	from random import shuffle
	from gluon import current
	db = current.db

	#Get the game
	game = db.game(game_id)

	#The game should exist
	if game is None:
		return

	#Get the players of a game
	players = getPlayers(game)

	#The game needs at least 2 players
	if len(players) < 2:
		return

	#You can only start a game that has not started
	if game.game_status != 'NOT_STARTED':
		return

	#Only the host has permission to start a game
	if db.game(game_id).host_id != user.id:
		return

	#Randomize the targets
	shuffle(players)

	#Update targets in database
	#The last player in the list targets the first player in the list
	target_id = players[0]['user_id']
	player = db.player(players[len(players)-1]['player_id'])
	player.update_record(target_id = target_id)

	#Each player targets the next player in the list
	for i in range (0, len(players)-1):
		target_id = players[i+1]['user_id']
		player = db.player(players[i]['player_id'])
		player.update_record(target_id = target_id)
	#End for i in range (0, len(players)-1):

	#Set the game as having started
	game.update_record(game_status = "STARTED")

	return

#TODO: How to get who is target/who is starting zombie?
def startGameZombies(game_id, user):
	"""
	Starts a game using the humans v. zombies rule set.  Exits if the game is invalid.

	Keyword Arguments:
	game_id  -- id of the game that needs to be started
	user_id  -- the current user to check permissions
	"""

	game = db.game(game_id)
	#Set timer on first zombie(s)
	#TODO hardcoded zombie
	zombiePlayers = db((db.player.game_id==game) & (db.player.target_id==12)).select()
	for i in range (0, len(zombiePlayers)-1):
		"""Set timer"""
	#Set the game as having started
	game.update_record(game_status = "STARTED")

	return

"""deprecated - use killPlayer from aactions"""
def wasKilledAssassins(game_id, user):
	"""
	Kills a player.

	Keyword Arguments:
	game_id  -- id of the game
	user_id  -- the current user
	"""

	game = db.game(game_id)
	currUser = db((db.player.game_id==game) & (db.player.player_id==user.id)).select()
	currUserDb = db.player(currUser[0].id)
	#Only need to set this here because it is completed once the targeting user checks and sees their target has died
	currUserDb.update_record(status = "DEAD")

	return

def killCompletedZombies(game_id, user):
	"""
	Function that is called when a zombie successfully kills a human.

	Keyword Arguments:
	game_id  -- id of the game
	user_id  -- the current user
	"""

	#For the zombies, restart starvation timer
	#TODO once this is all integrated with timeline, could prolly use that data as the timer...
	game = db.game(game_id)
	return

def wasKilledZombies(game_id, user):
	"""
	Function that is called when a human is killed by a zombie.

	Keyword Arguments:
	game_id  -- id of the game
	user_id  -- the current user
	"""

	#For the humans, turn into zombie
	#None for the zombies, because they starve on a timer

	response.flash = "You suck"
	game_id = int(request.args(0))
	game = db.game(game_id)
	currUser = db((db.player.game_id==game) & (db.player.player_id==user.id)).select()
	currUserDb = db.player(currUser[0].id)
	#TODO hardcoded zombie
	response.flash = currUserDb.target_id
	currUserDb.update_record(target_id = 12)
	return

def killCompletedAssassins(game_id, user_id):
	"""
	Targets a player for death.

	Keyword Arguments:
	game_id -- id of the game
	user_id -- id of the user that is targeting
	"""

	from gluon import current
	db = current.db

	#Get the game
	game = db.game(game_id)

	#Get a row representing the player
	currUser = db((db.player.game_id==game.id) & (db.player.player_id==user_id)).select()[0]

	#Get a row representing the target
	currTarget = db((db.player.game_id==game) & (db.player.player_id==currUser.target_id)).select()[0]

	#If the row does not have an id
	if currTarget.id == None:
		return

	#If the user is targetting him or herself
	if currTarget.id == currUser.id:
		return

	#The target is dead
	if(currTarget.status == "DEAD"):
		#TODO Inform user that they have a DEAD target
		currUser.update_record(target_id = currTarget.target_id)
		db.player(currTarget.id).update_record(target_id = None)

	#The target is not dead
	else:
		currTargetDb = db.player(currTarget.id)
		currTargetDb.update_record(status = "HALF_DEAD")
		#TODO: SET TIMER

	return

def gameWon(game):
	"""
	Checks if a game has been won

	Keyword Arguments:
	game -- row representing a game
	"""

	#TODO THIS

	response.flash = "YOU WON!"
	return

def checkGameStatus(game):
	"""
	Checks the status of a game.

	Keyword Arguments:
	game -- row representing a game
	"""

	# Maybe ^ Can prolly handle all inside function

	currUser = db((db.player.game_id==game.id) & (db.player.player_id==auth.user.id)).select()
	currUserDb = db.player(currUser[0].id)
	currTarget = db((db.player.game_id==game.id) & (db.player.player_id==currUser[0].target_id)).select()

	#Check to see if the game is over
	if(game.game_status == "STARTED" and game.rules == "Standard"):
		living_players = db((db.player.game_id==game.id) & (db.player.status=="ALIVE")).select()
		if(len(living_players) <= 1 and game.game_status != "FINISHED"):
			if(currUserDb.status == "ALIVE"):
				gameWon()
				db.game[game_id].winner_id = db.auth_user[living_players[0].player_id].id
			game.update_record(game_status = "FINISHED")
			return 1
	if(game.game_status == "STARTED" and game.rules == "Humans v. Zombies"):
		#TODO survival_target
		humans_remaining = db((db.player.game_id==game.id) & (db.player.target_id==survival_target)).select()
		if(len(humans_remaining) < 1):
			"""TODO If #humans == 0"""
	return
