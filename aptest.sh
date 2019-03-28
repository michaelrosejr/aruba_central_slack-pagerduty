#!/bin/sh
curl -H "Content-Type: application/json" -X POST -d @$1.json http://appaccess.ngrok.io.ngrok.io/webhook
