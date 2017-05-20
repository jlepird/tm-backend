#!/bin/bash

# post="curl -i -H 'Content-Type: application/json' -X POST -d"

curl -i -s -H "Content-Type: application/json" -X POST -d '{"airman":"Capt Smith", "billet":"abc", "constr": "FORBID"}' http://0.0.0.0:8000/addConstraint | grep "Success"
curl -i -s -H "Content-Type: application/json" -X POST -d '{"airman":"Capt Smith", "billet":"abc", "constr": "FORBID"}' http://0.0.0.0:8000/delConstraint | grep "Success"
curl -i -s -H "Content-Type: application/json" -X POST -d '{"airman":"Capt Smith", "billet":"xyz", "constr": "FORBID"}' http://0.0.0.0:8000/addConstraint | grep "Error"
curl -i -s -H "Content-Type: application/json" -X POST -d '{"airman":"Capt Smith", "billet":"abc", "constr": "foo"}' http://0.0.0.0:8000/addConstraint | grep "Error"

curl -i -s -X GET http://0.0.0.0:8000/optimize | grep Success

echo "All tests successful."