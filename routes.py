import os
import flask
from flask.ext.bower import Bower
import psycopg2
import urlparse
import random
import names
import hashlib

from pulp import *

app = flask.Flask(__name__)

Bower(app)

# Set up our connection for global use
conn = psycopg2.connect(database = os.environ["DATABASE_URL"])
cur = conn.cursor()

# Random billet generator.
def hash(my_str):
	h = hashlib.new("md5")
	h.update(my_str)
	return h.hexdigest()

@app.route('/')
def main():

	cur.execute("select * from airmen;")
	airmen = cur.fetchall()
	cur.execute("select left(name, 4), afsc, aad from billets;")
	billets = cur.fetchall()

	return flask.render_template("main.html", airmen=airmen, billets=billets, matches = [])

@app.route('/updateSize')
def updateSize():

	cur.execute("select count(*) from airmen;")
	res = cur.fetchone()
	n = res[0]

	cur.execute("select count(*) from billets;")
	res = cur.fetchone()
	m = res[0]

	# return 'Hello World from Flask! y=' + str(y.varValue)
	return flask.render_template("updateSize.html", n = n, m = m)

@app.route("/refresh", methods = ["POST"])
def refresh():
	n = int(flask.request.form["n"])
	m = int(flask.request.form["m"])
	## Init our database.
	cur.execute("drop table if exists airmen;")
	conn.commit()
	cur.execute("""create table airmen (
		name varchar(50),
		afsc varchar(3),
		aad varchar(3));""")
	conn.commit()

	cur.execute("drop table if exists billets;")
	conn.commit()
	cur.execute("""create table billets (
		name varchar(50),
		afsc varchar(3),
		aad varchar(3));""")
	conn.commit()

	allowable_afscs = ["61A", "61C", "61D"]
	allowable_aads  = ["BS", "MS", "PhD"]

	namelist = []
	billets = []

	for i in range(n):
		name = names.get_full_name()
		namelist.append(name)
		cur.execute("insert into airmen values (%s, %s, %s)", 
			(
				name,
				random.choice(allowable_afscs), 
				random.choice(allowable_aads)
			))
		conn.commit()

	for i in range(m):
		billet = hash(names.get_full_name())
		billets.append(billet)
		cur.execute("insert into billets values (%s, %s, %s)", 
			(
				billet, 
				random.choice(allowable_afscs),
				random.choice(allowable_aads)
			))
		conn.commit()

	# Randomly generate preferences
	cur.execute("drop table if exists amnPrefs;")
	conn.commit()
	cur.execute("""create table amnPrefs (
			amn varchar(50),
			bil varchar(50),
			pref int);
		""")
	conn.commit()

	cur.execute("drop table if exists bilPrefs;")
	conn.commit()
	cur.execute("""create table bilPrefs (
			amn varchar(50),
			bil varchar(50),
			pref int);
		""")
	conn.commit()

	for amn in namelist:
		remaining_billets = billets[:] # get copy of list, not reference.
		for i in range(random.randint(1, 10)):
			choice = random.choice(remaining_billets)
			remaining_billets.remove(choice)
			cur.execute("insert into amnPrefs values (%s, %s, %s)", (amn, choice, i+1))
			conn.commit()

	for bil in billets:
		remaining_amn = namelist[:] # get copy of list, not reference. 
		for i in range(random.randint(1, 10)):
			choice = random.choice(remaining_amn)
			remaining_amn.remove(choice)
			cur.execute("insert into amnPrefs values (%s, %s, %s)", (choice, bil, i+1))
			conn.commit()


	return flask.redirect("/")

# Final run.
port = os.getenv('PORT', '8000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
