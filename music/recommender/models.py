from django.db import models
from django.contrib.auth.models import User

class Musicdata(models.Model):
    acousticness = models.FloatField()
    artists = models.TextField()
    danceability = models.FloatField()
    duration_ms = models.FloatField()
    energy = models.FloatField()
    explicit = models.FloatField()
    id = models.TextField(primary_key=True)
    instrumentalness = models.FloatField()
    key = models.FloatField()
    liveness = models.FloatField()
    loudness = models.FloatField()
    mode = models.FloatField()
    name = models.TextField()
    popularity = models.FloatField()
    speechiness = models.FloatField()
    tempo = models.FloatField()
    valence = models.FloatField()
    year = models.IntegerField()
    likes = models.IntegerField(default=0)
    


    def __str__(self):
        return self.name

class Playlist(models.Model):
    title = models.CharField(max_length=255)
    likes = models.IntegerField(default=0)
    creatorid= models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ManyToManyField(User, related_name = 'filler')
    datecreated = models.DateTimeField(auto_now_add=True)
    songs = models.ManyToManyField(Musicdata)
    recentylistenedplaylist= models.BooleanField(default=False)

    def __str__(self):
        return self.title

# Liked songs, more or less
class Rating(models.Model):
    rating = models.IntegerField(null=True, blank=True)
    userid= models.ForeignKey(User, on_delete=models.CASCADE)
    songid = models.ForeignKey(Musicdata, on_delete=models.CASCADE)

    def __str__(self):
        return self.userid.username + " " + self.songid.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profilepic = models.ImageField(upload_to='recommender/images/', blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.user)

class Artist(models.Model):
    id = models.TextField(primary_key=True)
    genres = models.TextField()
    follows = models.IntegerField(default=0)
    
    def __str__(self):
        return self.id

class Follower(models.Model):
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'followed')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Followers(models.Model):
    name = models.TextField()

class Followed_Artist(models.Model):
    userid = models.ForeignKey(User, on_delete=models.CASCADE)
    artistid = models.ForeignKey(Artist, on_delete=models.CASCADE)

class Recently_Listened(models.Model):
    userid = models.ForeignKey(User, on_delete=models.CASCADE)
    songid = models.ForeignKey(Musicdata, on_delete=models.CASCADE)
    datelistened = models.DateTimeField(auto_now_add=True)



