"""
General purpose getters and tools.
"""

def getImage (image):
	"""
	Gets an image or gets a default image if the image does not exist.

	Keyword Arguments:
	image -- file path of the image to get

	Return Values:
	out -- file path of the image
	    -- file path of a default image if the image does not exist
	"""

	from gluon import URL

	out = URL('static', 'images/default.png')
	if image is not None and image is not '':
		out = URL('default', 'download', args=image)

	return out

def getGame (args):
	"""
	Takes an argument and tries to get a row from db.game with it.

	Keyword Arguments:
	args -- url argument that corresponds to an id of a game

	Return Values:
	out -- row corresponding to the game
	    -- none if a game could not be retrieved or the argument is invalid
	"""

	from gluon import current
	db = current.db

	#There needs to be at least 1 argument
	if len(args) == 0:
		return None

	#The argument should be an integer
	if not args(0).isdigit():
		return None

	#Get the current game information references by the argument
	game_id = int(args(0))
	out = db.game(game_id)

	return out

def getPlayers (game):
	"""
	Gets a sorted list of players for a game.

	Keyword Arguments:
	game_id -- id of the game to get the players from

	Return Values:
	out -- list of dictionaries representing players
	    -- 'name'  the full name of the player
	    -- 'status' the status of the player
	    -- 'player_id' the id of the player
	    -- 'user_id' the auth_user id of the player
	"""

	from gluon import current
	db = current.db

	#Rows for the current player's list
	players = db( (db.player.player_id==db.auth_user.id) & (db.player.game_id==game.id) ).select(db.player.id, db.player.status, db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name)

	out = []
	for player in players:
		row = {'name':'name', 'status':'ALIVE', 'player_id':'0', 'user_id':'0'}

		row['name'] = player.auth_user.first_name + ' ' + player.auth_user.last_name
		if game.game_status == 'STARTED':
			row['status'] = player.player.status
		row['player_id'] = player.player.id
		row['user_id'] = player.auth_user.id
		out.append(row)
	#End for player in players:

	#Sort players by status, then by name
	out.sort(key = lambda n: (n['status'], n['name']))

	return out

def hideFields (table, fields):
	"""
	Hides fields in a form.

	Keyword Arguments:
	table  -- the table in a database
	fields -- list of strings that represent fields within the database
	       -- ['field1', 'field2', 'etc...']
	"""

	#How does this even work?  Does this change some sort of global variable?

	for field in fields:
		field = table[field]
		field.readable = field.writable = False
	#End for field in fields:

	return

def resizeImage(table, id):
	"""
	Resizes an image to 200x200 pixels

	Keyword Arguments:
	table -- the table in a database
	id    -- if of a row within the database
	"""

	from gluon import current
	db = current.db
	request = current.request

	#HURRRR just put 'try' around everything
	try:
		#Get the image from the database
		thisImage=db(table.id==id).select()[0]

		import os, uuid
		from PIL import Image

		#Load the image from the uploads folder.
		im=Image.open(request.folder + '/uploads/' + thisImage.image)

		#Get the image dimenions
		width = im.size[0]
		height = im.size[1]

		#The image id taller than it is wide
		if width < height:
			top    = int((height-width)/2)
			bottom = int(height-((height-width)/2))
			im = im.crop((0,top,width,bottom))
		
		#The image is wider than it is tall
		elif height < width:
			left  = int((width-height)/2)
			right = int(width-((width-height)/2))
			im = im.crop((left,0,right,height))

		#Scale the image down to 200x200
		size = (200, 200)
		im.thumbnail(size, Image.ANTIALIAS)

		#Save the image
		im.save(request.folder + '/uploads/' + thisImage.image)
	except:
		return
	return
