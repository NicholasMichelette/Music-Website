

python manage.py makemigrations 
 python manage.py migrate
python manage.py makemigrations recommender 
 python manage.py migrate recommender


sqlite3 db.sqlite3 -cmd ".mode csv" ".import data.csv recommender_musicdata"
sqlite3 db.sqlite3 -cmd ".mode csv" ".import artist2.csv recommender_artist"

echo "*********************************************"
echo "If needed, now create super user and insert data into database"