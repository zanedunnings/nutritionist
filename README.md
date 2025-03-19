# debug the sql table

sqlite3 meal_plans.db

# to sync code with server and deploy

`./sync_and_deplyo`


source venv/bin/activate


# add to ./bashrc
```
# Start SSH agent if not already running
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519
fi
```


#configs 
/etc/systemd/system/nutritionist.service

run `sudo systemctl daemon-reload` after changing