from django.contrib import admin
from .models import Musicdata, Playlist, Profile, Artist, Follower, Rating, Recently_Listened

# Register your models here.
admin.site.register(Musicdata)
admin.site.register(Playlist)
admin.site.register(Rating)
admin.site.register(Profile)
admin.site.register(Recently_Listened)
admin.site.register(Artist)
admin.site.register(Follower)


