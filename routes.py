import os
import flask
import psycopg2
import urlparse
import random
import names
import hashlib
import itertools

from pulp import *

app = flask.Flask(__name__)
# Set up our connection for global use
db = os.environ["DATABASE_URL"]
if "VCAP_SERVICES" not in os.environ: # then running locally
	conn = psycopg2.connect(database=db)
else:
	res = urlparse.urlparse(os.environ["DATABASE_URL"])
	conn = psycopg2.connect(
		database=res.path[1:],
		user=res.username,
		password=res.password,
		host=res.hostname
	)
cur = conn.cursor()

constraints = ["FORCE", "FORBID", "FILL", "VACATE"]

@app.route('/addConstraint', methods = ["POST"])
def addConstraint():
	# Validate that this amn exists
	amn = flask.request.json.get("airman")
	cur.execute("select count(*) from users where name=%s;", (amn,))
	conn.commit()
	if cur.fetchall()[0][0] == 0:
		return flask.jsonify({"Status":"Error", "Msg":"Airman %s not found." % amn})

	# Validate that this billet exists.
	bil = flask.request.json.get("billet")
	# Validate that this amn exists
	cur.execute("select count(*) from billetdescs where posn=%s;", (bil,))
	conn.commit()
	if cur.fetchall()[0][0] == 0:
		return flask.jsonify({"Status":"Error", "Msg":"Billet %s not found." % bil})

	# Validate teh constraint type
	constr = flask.request.json.get("constr")
	if constr not in constraints: 
		return flask.jsonify({"Status":"Error", "Msg":"Constr %s not supported." % constr})

	cur.execute("insert into constraints values (%s, %s, %s);", (amn, bil, constr))
	conn.commit() 
	return flask.jsonify({"Status": "Success"})

@app.route('/delConstraint', methods = ["POST"])
def delConstraint():
	amn = flask.request.json.get("airman")
	bil = flask.request.json.get("billet")
	constr = flask.request.json.get("constr")
	#try:
	cur.execute("delete from constraints where name=%s and posn=%s and constr=%s;", (amn, bil, constr))
	print cur.query
	conn.commit()
	#except Exception as e:
	#	return flask.jsonify({"Status": "SQL Error"}) 
	return flask.jsonify({"Status": "Success"})

@app.route("/optimize", methods = ["GET"])
def optimize():

	cur.execute("truncate table matches;")
	conn.commit()

	cur.execute("select * from airmen;")
	airmen_tmp = cur.fetchall()

	airmen = {}
	for airman in airmen_tmp:
		airmen[airman[0]] = dict(
			afsc = airman[1],
			aad  = airman[2],
			grade= airman[3]
		)

	cur.execute("select * from billets;")
	billets_tmp = cur.fetchall()

	billets = {}
	for billet in billets_tmp:
		billets[billet[0]] = dict(
			afsc = billet[1],
			aad  = billet[2],
			grade= billet[3]
		)


	cur.execute("select * from amnprefs order by amn, pref;")
	amnPrefs_tmp = cur.fetchall()

	amnPrefs = {}
	for pref in amnPrefs_tmp:
		if pref[0] not in amnPrefs.keys():
			amnPrefs[pref[0]] = dict()
		amnPrefs[pref[0]][pref[1]] = pref[2]

	cur.execute("select * from bilprefs order by bil, pref;")
	bilPrefs_tmp = cur.fetchall()

	bilPrefs = {}
	for pref in bilPrefs_tmp:
		if pref[1] not in bilPrefs.keys():
			bilPrefs[pref[1]] = dict()
		bilPrefs[pref[1]][pref[0]] = pref[2]

	#cur.execute("select * from constraints;")
	#constraints = cur.fetchall()

	m = LpProblem("", LpMinimize)
	#matches = LpVariable.dicts("matches", [x for x in itertools.product(airmen.keys(), billets.keys())], 0, 1, LpInteger)
	matches = LpVariable.dicts("matches", (airmen.keys(), billets.keys()), 0, 1, LpInteger)

	# Define our objective function

	obj = 0.0
	for airman in airmen:
		for billet in billets:
			if billet in amnPrefs[airman].keys():
				amnPref = amnPrefs[airman][billet]
			else: 
				amnPref = 15
			if airman in bilPrefs[billet].keys():
				bilPref = bilPrefs[billet][airman]
			else:
				bilPref = 15

			out = float(amnPref + bilPref)

			airmand = airmen[airman]
			billetd = billets[billet]

			if airmand["grade"] == billetd["grade"] and \
			   airmand["aad"]   == billetd["aad"] and \
			   airmand["afsc"]  == billetd["afsc"]:
			   out *= 0.9
			obj += out * matches[airman][billet]
	
	m += obj

	for airman in airmen:
		m += lpSum([matches[airman][billet] for billet in billets]) == 1

	for billet in billets:
		m += lpSum([matches[airman][billet] for airman in airmen]) <= 1

	m.solve()
	print "Status:" + str(LpStatus[m.status])

	matches_dict = {}
	for airman in airmen:
		for billet in billets:
			if value(matches[airman][billet]) > 0.0:
				matches_dict[airman] = billet
				cur.execute("insert into matches values (%s, %s)", (airman, billet))
				conn.commit()

	return flask.jsonify({"Status":"Success", "matches":matches_dict})
# Final run.
port = os.getenv('PORT', '8000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
