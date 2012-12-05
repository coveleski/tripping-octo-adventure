"""
Functions for getting information for the various pages.

These functions are specific to the pages they serve.
"""

from atools import *
from aactions import *

def getCurrentPolaroid (user):
	"""
	Gets the information to be shown on the polaroids for the current games page.

	Keyword Arguments:
	user     -- row representing the current user

	Return Values:
	out -- list containing dictionary for each game the user is participating in.
	    -- 'image'  file path of the image to show
	    -- 'text1'  string of the name of the game
	"""

	from gluon import current
	db = current.db

	#Get all the current games of the current player
	games = db((db.player.player_id==user.id) & (db.player.game_id==db.game.id)).select(db.game.id, db.game.name, db.game.game_status, db.game.image, db.game.winner_id, db.player.status, db.player.target_id)

	#The list that is being returned.
	out = []

	#Add an entry to the list for each game
	for game in games:
		row = {'game_id':'', 'image':'', 'text1':'', 'text2':'', 'status':'status'}

		row['game_id'] = game.game.id
		row['text2']   = game.game.name

		if game.game.game_status == 'NOT_STARTED':
			row['image'] = getImage(game.game.image)
		elif game.game.game_status == 'STARTED' and game.player.status == 'DEAD':
			row['image']  = getImage(user.image)
			row['text1']  = 'You are dead.'
			row['status'] = 'DEAD'
		elif game.game.game_status == 'STARTED' and game.player.status != 'DEAD':
			row['image'] = getImage(db.auth_user(game.player.target_id).image)
			row['text1'] = db.auth_user(game.player.target_id).first_name + ' ' + db.auth_user(game.player.target_id).last_name
			#Get the user's target
			target = db((db.player.player_id==game.player.target_id) & (db.player.game_id==game.game.id)).select()[0]
			row['status'] = target.status
		elif game.game.game_status == 'FINISHED':
			query = db.auth_user(game.game.winner_id)
			row['image'] = getImage(query.image)
			row['text1'] = query.first_name + ' ' + query.last_name
			row['status'] = 'FINISHED'

		#Add the row to the list
		out.append(row)
	#End for game in games:

	#Sort the games by alphabetical order of game name
	out.sort(key = lambda n: n['text2'] )

	return out

def getCurrentFlash (games, user):
	"""
	Gets a message to flash for the current games page.

	Keyword Arguments:
	games -- list containing rows representing games

	Return Values:
	out -- string containing the message to flash
	    -- none if there is no string
	"""

	string = None

	for i in range(0, len(games)):
		game = db.game(games[i]['game_id'])
		checkGameStatus(game)
		#TODO Use ^ instead?
		if(game.game_status == "STARTED"):
			currUser = db((db.player.game_id==game) & (db.player.player_id==auth.user.id)).select()
			currUserDb = db.player(currUser[0].id)
			currTarget = db((db.player.game_id==game) & (db.player.player_id==currUser[0].target_id)).select()
			if(currTarget[0].id != None and currTarget[0].id != currUser[0].id):
				if(currTarget[0].status == "DEAD"):
					string = "You have a dead target!"

	return string




def getEditgamePolaroid (game):
	"""
	Gets the information to be shown on the polaroid for the edit game page.

	Keyword Arguments:
	game     -- row representing the current game

	Return Values:
	polaroid -- dictionary containing game related information about the user
	         -- 'image'  file path of the image to show
	         -- 'text1'  string of the name of the game
	"""

	polaroid = {'image':'', 'text1':'', 'text2':'', 'status':'status'}

	polaroid['image'] = getImage(game.image)
	polaroid['text2'] = game.name

	return polaroid

def getEditgamePlayers (game, user):
	"""
	Gets a list of players and buttons for the edit game page.

	Keyword Arguments:
	game    -- row representing the current game
	user    -- row representing the current user

	Return Values:
	out -- list containing dictionaries for each player
	    -- 'name'   string of the full name of the player
	    -- 'status' string of the status of the player
	    -- 'kill'   '' or a button to kill the player
	    -- 'kick'   '' or a button to kick the player
	"""

	from gluon import current, INPUT, FORM, redirect, URL
	db = current.db

	#Rows for the current player's list
	players = db( (db.player.player_id==db.auth_user.id) & (db.player.game_id==game.id) ).select(db.player.status, db.player.id, db.player.player_id, db.auth_user.first_name, db.auth_user.last_name)

	out = []
	for player in players:
		row = {'name':'name', 'status':'status', 'kill':'', 'kick':''}

		action1 = 'Kill'
		action2 = 'Kick'
		if game.rules == 'Assassins':
			action1 = 'Eliminate'
		elif game.rules == 'Humans v. Zombies':
			action1 = 'Zombify'

		row['name']   = player.auth_user.first_name + ' ' + player.auth_user.last_name
		if game.host_id == player.player.player_id:
			row['name'] = row['name'] + ' (Host)'

		if game.game_status == "STARTED":
			row['status'] = player.player.status

		if row['status'] != 'DEAD' and game.game_status == 'STARTED':
			action = 'action'

			id   = INPUT(_name='id', _type='text', _value=player.player.player_id, _class='hidden')
			kill = INPUT(_type='submit', _value=action1, _class='btn btn-mini', _onclick='return confirm(\'Are you sure you want to ' + action1.lower() + ' this player?\');')
			row['kill'] = FORM(id, kill)

			if row['kill'].process(formname='formBtnKill').accepted:
				player
				killPlayer(game.id, row['kill'].vars.id, user)
				redirect(URL('kiwi', 'editgame', args=game.id))

		if player.player.player_id != user.id:
			id   = INPUT(_name='id', _type='text', _value=player.player.id, _class='hidden')
			kick = INPUT(_type='submit', _value=action2, _class='btn btn-mini btn-danger', _onclick='return confirm(\'Are you sure you want to ' + action2.lower() + ' this player?\');')
			row['kick'] = FORM(id, kick)

			if row['kick'].process(formname='formBtnKick').accepted:
				kickPlayer(row['kick'].vars.id, user)
				redirect(URL('kiwi', 'editgame', args=game.id))

		out.append(row)
	#End for player in players:

	#Sort players by status, then by name
	out.sort(key = lambda n: (n['status'], n['name']))

	return out

def getEditgameBtn (game, user):
	"""
	Gets a dictionary of buttons that do stuff for the edit game page.

	Keyword Arguments:
	game -- row representing the current game
	user -- row representing the current user

	Return Values:
	btn -- dictionary of web2py forms
	        -- 'back'   Back To Game
	        -- 'delete' Delete Game
	"""

	from gluon import URL, INPUT, FORM, A, redirect

	btn = {'back':'back', 'delete':'delete'}

	link = A('Back to Game', _class='btn btn-large btn-inverse btn-block', _href=URL('default', 'game', args=game.id))
	btn['back'] = link

	button = INPUT(_type='submit', _value='(Host) Delete Game', _class='btn btn-small btn-block abtn-small', _onclick='return confirm(\'Are you sure you want to delete this game?\');')
	formDelete = FORM(button)
	btn['delete'] = formDelete

	if btn['delete'].process().accepted:
		deleteGame(game.id, user)
		redirect(URL('default', 'current'))

	return btn

def getEditgameUpdateForm (game):
	"""
	Gets an update for the edit game page.

	Keyword Arguments:
	game -- row representing the current game

	Return Values:
	formUpdate -- web2py form
	"""

	from gluon import current, redirect, URL, SQLFORM
	db = current.db

	#Hide some fields of the form
	hideFields (db.game, ['id', 'rules', 'host_id', 'game_status', 'password', 'winner_id'])

	formUpdate = SQLFORM(db.game, game.id)
	formUpdate.add_class('assassins-form')

	if formUpdate.process().accepted:
		resizeImage(db.game, game.id)
		redirect(URL('kiwi', 'editgame', args=game.id))

	return formUpdate




def getGameStats (game):
	"""
	Gets statistics about the game.

	Keyword Arguments:
	game    -- row representing the current game

	Return Values:
	out -- dictionary containing game statistics
	    -- 'rules'   string representing the type of the game (Assassins or Humans v. Zombies)
	    -- 'players' total number of players
	    -- 'alive'   number of players alive
	    -- 'dead'    number of players dead
	"""

	from gluon import current
	db = current.db

	players = db(db.player.game_id==game.id).select()

	out = {'rules':'', 'players':0, 'alive':0, 'dead':0}

	out['rules'] = game.rules
	out['players'] = len(players)

	dead    = 0
	notDead = 0

	for player in players:
		if player.status == 'DEAD':
			dead = dead+1
		else:
			notDead = notDead+1
	#End for player in players:

	out['alive'] = notDead
	out['dead']  = dead

	return out

"""Deprecated - use getPlayers from atools"""
def getGamePlayers (game):
	"""
	Gets a list of players for a game.

	Keyword Arguments:
	game    -- row representing the current game

	Return Values:
	out -- list of dictionaries representing players
	    -- 'name'  the full name of the player
	    -- 'status' the status of the player
	    -- 'id' the id of the player (not the id of the user)
	"""

	from gluon import current
	db = current.db

	#Rows for the current player's list
	players = db( (db.player.player_id==db.auth_user.id) & (db.player.game_id==game.id) ).select(db.player.id, db.player.status, db.auth_user.first_name, db.auth_user.last_name)

	out = []
	for player in players:
		row = {'name':'name', 'status':'status', 'id':'0'}
		row['name'] = player.auth_user.first_name + ' ' + player.auth_user.last_name
		if game.game_status == 'STARTED':
			row['status'] = player.player.status
		row['id'] = player.player.id
		out.append(row)
	#End for player in players:

	#Sort players by status, then by name
	out.sort(key = lambda n: (n['status'], n['name']))

	return out

def getGameUserInfo (game, user):
	"""
	Gets game related information about the current user.

	Keyword Arguments:
	game    -- row representing the current game
	user    -- row representing the current user

	Return Values:
	out -- dictionary containing game related information about the user
	    -- 'name'   the current user's full name
	    -- 'host'   if the user is the host of the game
	    -- 'status' the status of the user as it appears in the database
	    -- 'joined' weather the user has joined the game
	"""

	from gluon import current
	db = current.db

	out = {'name':'name', 'host':False, 'status':'status', 'joined':False}

	out['name'] = user.first_name + ' ' + user.last_name

	if user.id == game.host_id:
		out['host'] = True
	status = db((db.player.player_id==user.id) & (db.player.game_id==game.id)).select(db.player.status)
	if len(status) > 0:
		out['joined'] = True
		out['status'] = status[0].status

	return out

def getGamePolaroid (game, userInfo, user):
	"""
	Gets the information to be shown on the polaroid for the game page.

	Keyword Arguments:
	game     -- row representing the current game
	userInfo -- dictionary representing game related information about the current user
	user     -- row representing the current user

	Return Values:
	polaroid -- dictionary containing game related information about the user
	         -- 'name'   the current user's full name
	         -- 'host'   if the user is the host of the game
	         -- 'status' the status of the user as it appears in the database
	         -- 'joined' weather the user has joined the game

	"""

	from gluon import current
	db = current.db

	polaroid = {'image':'', 'text1':'', 'text2':'', 'status':'status', 'gameFinished':''}

	polaroid['text2'] = game.name
	polaroid['gameFinished'] = 0

	if game.game_status == 'NOT_STARTED':
		polaroid['image'] = getImage(game.image)

	elif game.game_status == 'STARTED' and not userInfo['joined']:
		polaroid['image'] = getImage(game.image)
		polaroid['text1'] = 'The game has started.'

	elif game.game_status == 'STARTED' and userInfo['status'] == 'DEAD':
		polaroid['image']  = getImage(user.image)
		polaroid['text1']  = 'You are dead.'
		polaroid['status'] = 'DEAD'

	elif game.game_status == 'STARTED' and userInfo['status'] != 'DEAD':
		target = db((db.player.player_id == user.id) & (db.player.game_id == game.id) & (db.player.target_id == db.auth_user.id)).select(db.auth_user.first_name, db.auth_user.last_name, db.auth_user.image)[0]
		polaroid['image'] = getImage(target.image)
		polaroid['text1'] = target.first_name + ' ' + target.last_name

	elif game.game_status == 'FINISHED':
		query = db.auth_user(game.winner_id)
		polaroid['image'] = getImage(query.image)
		polaroid['text1'] = query.first_name + ' ' + query.last_name
		polaroid['status'] = 'FINISHED'

	return polaroid

def getGameBtns (game, userInfo):
	"""
	Gets which buttons should be visible on the game page.

	Keyword Arguments:
	game     -- row representing the current game
	userInfo -- dictionary representing game related information about the current user

	Return Values:
	btn -- dictionary containing booleans for buttons
	    -- 'all'    Show the button pad
	    -- 'start'  Start Game
	    -- 'join'   Join Game
	    -- 'leave'  Leave Game
	    -- 'target' Target Eliminated
	    -- 'dead'   I have been eliminated
	    -- 'edit'   Edit Game
	"""

	btn = {'all':False, 'start':False, 'join':False, 'leave':False, 'target':False, 'dead':False, 'edit':False}

	if game.game_status == 'NOT_STARTED' and userInfo['host']:
		btn['all'] = True
		btn['start'] = True

	if game.game_status == 'NOT_STARTED' and not userInfo['joined']:
		btn['all'] = True
		btn['join'] = True

	if not userInfo['host'] and userInfo['joined']:
		btn['all'] = True
		btn['leave'] = True

	if game.game_status == 'STARTED' and userInfo['joined'] and userInfo['status'] != 'DEAD':
		btn['all'] = True
		btn['target'] = True
		btn['dead'] = True

	if userInfo['host']:
		btn['all'] = True
		btn['edit'] = True

	return btn

def getGameFormBtn (game, user, gameStats):
	"""
	Gets a dictionary of form buttons that do stuff for the game page.

	Keyword Arguments:
	game    -- row representing the current game
	user    -- row representing the current user

	Return Values:
	formBtn -- dictionary of web2py forms
	        -- 'start'  Start Game button
	        -- 'join'   Join Game button
	        -- 'leave'  Leave Game button
	        -- 'target' Target Eliminated button
	        -- 'dead'   I have been eliminated button
	"""

	from gluon import current, INPUT, FORM, redirect, URL, BUTTON
	db = current.db

	formBtn = {'start':'start', 'join':'join', 'leave':'leave', 'target':'target', 'dead':'dead'}

	if gameStats['players'] > 1:
		formBtn['start']  = FORM(INPUT(_type='submit', _value='(Host) Start Game', _class='btn btn-large btn-block btn-inverse abtn-large', _onclick='return confirm(\'Are you sure you want to start this game?\');'))
	else:
		formBtn['start']  = BUTTON('(Host) Start Game', _class='btn btn-large btn-block btn-inverse abtn-large', _onclick='alert(\'You need at least 2 players to start a game?\');')

	formBtn['join']   = FORM(INPUT(_type='submit', _value='Join Game', _class='btn btn-large btn-block btn-inverse abtn-large'))
	formBtn['leave']  = FORM(INPUT(_type='submit', _value='Leave Game', _class='btn btn-block abtn-small', _onclick='return confirm(\'Are you sure you want to leave this game?\');'))
	formBtn['target'] = FORM(INPUT(_type='submit', _value='Target Eliminated', _class='btn btn-large btn-block btn-inverse abtn-large'))
	formBtn['dead']   = FORM(INPUT(_type='submit', _value='I am dead.', _class='btn btn-block abtn-small', _onclick='return confirm(\'Are you sure you want to eliminate yourself?\');'))

	if gameStats['players'] > 1 and formBtn['start'].process(formname='formBtnStart').accepted:
		startGameAssassins(game.id, user)
		redirect(URL('default', 'game', args=game.id))

	if formBtn['join'].process(formname='formBtnJoin').accepted:
		joinGame(game.id, user)
		redirect(URL('default', 'game', args=game.id))

	if formBtn['leave'].process(formname='formBtnLeave').accepted:
		leaveGame(game.id, user)
		redirect(URL('default', 'game', args=game.id))

	if formBtn['target'].process(formname='formBtnTarget').accepted:
		killCompletedAssassins(game.id, user.id)
		redirect(URL('default', 'game', args=game.id))

	if formBtn['dead'].process(formname='formBtnDead').accepted:
		query = db( (db.player.game_id==game.id) & (db.player.player_id==user.id) ).select(db.player.id)[0]
		killPlayer(game.id, user.id)
		#wasKilledAssassins()
		redirect(URL('default', 'game', args=game.id))

	return formBtn
