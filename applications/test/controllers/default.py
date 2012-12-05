# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
from apagetools import *
from atools import *

def user():
	from atools import hideFields

	if 'profile' in request.args:
		redirect(URL('default', 'settings'))

	hideFields (db.auth_user, ['image', 'theme'])

	return dict(form=auth())

def index():
	return dict()

def download():
	"""
	allows downloading of uploaded files
	http://..../[app]/default/download/[filename]
	"""
	return response.download(request,db)

def call():
	"""
	exposes services. for example:
	http://..../[app]/default/call/jsonrpc
	decorate with @services.jsonrpc the functions to expose
	supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
	"""
	return service()

def data():
	"""
	http://..../[app]/default/data/tables
	http://..../[app]/default/data/create/[table]
	http://..../[app]/default/data/read/[table]/[id]
	http://..../[app]/default/data/update/[table]/[id]
	http://..../[app]/default/data/delete/[table]/[id]
	http://..../[app]/default/data/select/[table]
	http://..../[app]/default/data/search/[table]
	but URLs must be signed, i.e. linked with
		A('table',_href=URL('data/tables',user_signature=True))
	or with the signed load operator
		LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
	"""
	return dict(form=crud())

def error():
	"""response.flash = T("Welcome to Assassins!")"""
	return dict(message=T('Hello World'))

def logout():
	auth.logout()
	return dict()

def login():
	redirect(URL('default', 'index'))
	return dict()

def help():
	return dict()

@auth.requires_login()
def game():
	game = getGame(request.args)

	#Make sure the requested game is valid
	if game is None:
		redirect(URL('default', 'current'))

	#Determine if there is a dead target and if the game is finished with that death
	if(game.game_status == "STARTED"):
		currUser = db((db.player.game_id==game) & (db.player.player_id==auth.user.id)).select()
		if(currUser[0] != None):
			currUserDb = db.player(currUser[0].id)
			currTarget = db((db.player.game_id==game.id) & (db.player.player_id==currUser[0].target_id)).select()
			if(currTarget[0].id != None and currTarget[0].id != currUser[0].id):
				if(currTarget[0].status == "DEAD"):
					if(currTarget[0].target_id == currUser[0].player_id):
						game.update_record(game_status = "FINISHED")
					currUserDb.update_record(target_id = currTarget[0].target_id)
					db.player(currTarget[0].id).update_record(target_id = None)

	#Modules
	userInfo  = getGameUserInfo(game, auth.user)
	polaroid  = getGamePolaroid(game, userInfo, auth.user)
	btn       = getGameBtns(game, userInfo)
	players   = getPlayers(game)
	gameStats = getGameStats(game)
	formBtn   = getGameFormBtn(game, auth.user, gameStats)

	return dict(game=game, players=players, btn=btn, polaroid=polaroid, gameStats=gameStats, formBtn=formBtn)

@auth.requires_login()
def current():
	#Modules
	games = getCurrentPolaroid(auth.user)

	#If the player has exactly one current game
	#Redirect the player to that game
	if len(games) == 1:
		redirect(URL('default', 'game', args=games[0]['game_id']))

	return dict(games=games)

@auth.requires_login()
def join():
	#Select all games as a list
	items = db(db.game.id).select(db.game.id, db.game.name, db.game.location).as_list()

	return dict(items=items)

@auth.requires_login()
def settings():
	#Set the text and picture for the polaroid
	image = getImage(auth.user.image)

	hideFields (db.auth_user, ['id', 'theme', 'password'])

	form=SQLFORM(db.auth_user, auth.user.id)
	form.add_class('assassins-form')

	if form.process().accepted:
		resizeImage(db.auth_user, form.vars.id)
		
		#update the session cache
		auth.user.first_name = form.vars.first_name
		auth.user.last_name = form.vars.last_name
		auth.user.image = form.vars.image
		redirect(URL('default', 'settings'))

	return dict(form=form, image=image)

@auth.requires_login()
def create():
	from gluon.tools import Crud

	#Hide the fields that should not be accessable by the user
	hideFields (db.game, ['host_id', 'game_status', 'password', 'winner_id', 'rules'])

	#Run the form
	#form = SQLFORM(db.game)
	#form.add_class('assassins-form')
	#form.vars.host_id=auth.user.id

	#Create the form
	crud = Crud(db)
	crud.messages.submit_button = 'Create Game'
	form = crud.create(db.game)
	form.add_class('assassins-form')
	form.vars.host_id=auth.user.id

	#When the form is submitted, add the creator as a player and go to new game
	if form.process().accepted:
		joinGame(form.vars.id, auth.user)
		resizeImage(db.game, form.vars.id)
		redirect(URL('default', 'game', args=form.vars.id))

	return dict(form=form)
	
def verify():
	return dict()
	
def reset():
	return dict()
