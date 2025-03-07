# script-automation
python3 -m venv venv2

source venv2/bin/activate

pip install -r requirements.txt

# Ako dobijes error google.auth.exceptions.RefreshError: 

Treba napraviti novi token tako da izbrises stari(ne json) i novi iz terminala base64 i kopirat u secret

# Ako trebaš reset baze izbrisat sve cacheve sa skriptom clear.sh
