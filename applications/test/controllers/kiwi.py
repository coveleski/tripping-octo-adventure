from atools import *
from apagetools import *

@auth.requires_login()
def editgame():
	#Make sure the requested game is valid
	game = getGame(request.args)
	if game is None:
		redirect(URL('default', 'current'))

	#The current user should be the host of the game.
	if auth.user.id != game.host_id:
		redirect(URL('default', 'game', args=request.args(0)))

	#Page information
	polaroid   = getEditgamePolaroid(game)
	players    = getEditgamePlayers(game, auth.user)
	gameStats  = getGameStats(game)
	btn        = getEditgameBtn(game, auth.user)
	updateForm = getEditgameUpdateForm(game)

	return dict(polaroid=polaroid, players=players, gameStats=gameStats, updateForm=updateForm, btn=btn)
