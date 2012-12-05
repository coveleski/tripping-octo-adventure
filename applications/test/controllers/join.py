@auth.requires_login()
def index():
	items = db(db.game.id).select(db.game.id, db.game.name, db.game.location).as_list()

	#Sort the games by name
	items.sort(key = lambda n: n['name'])

	return dict(items=items)