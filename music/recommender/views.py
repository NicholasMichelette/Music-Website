from recommender.forms import SearchForm
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpRequest, HttpResponse
from .models import *
from .forms import *
from django.views.decorators.http import require_POST, require_GET
import numpy as np
import spotipy
import json
import random
from datetime import datetime, timedelta, date
from django.db.models import Q, Count
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse
from django.utils import timezone
import random


def find_albums(artist, from_year = None, to_year = None):
    query = Musicdata.objects.filter(artists__contains = artist)
    if from_year is not None:
        query = query.filter(year__gte = from_year)
    if to_year is not None:
        query = query.filter(year__lte = to_year)
    return list(query.order_by('-popularity'))

def find_song(songid):
   return Musicdata.objects.filter(id = songid)

def createPlaylist(request):
    form = PlaylistForm()

    context = {'form': form}
    return render(request, 'recommender/playlist.html', context)
    

@require_POST
def searchform_post(request):
    # create a form instance and populate it with data from the request:
    form = SearchForm(request.POST)
    # check whether it's valid:
    if form.is_valid():
        # process the data in form.cleaned_data as required
        from_year = None if form.cleaned_data['from_year'] == None else int(form.cleaned_data['from_year'])
        to_year = None if form.cleaned_data['to_year'] == None else int(form.cleaned_data['to_year'])
        albums = find_albums(
                form.cleaned_data['artist'],
                from_year,
                to_year
            )
            
        # Random 3 of top 10 popular albums
        albums = list(np.random.permutation(albums[:10]))[:3] 
        return render(request, 'recommender/searchform.html', {'form': form, 'albums': albums})
    else:
        raise Http404('Something went wrong')


@require_GET
def searchform_get(request):
    form = SearchForm()
    return render(request, 'recommender/searchform.html', {'form': form})


# HOME PAGE
def home(request):
    assert isinstance(request, HttpRequest)
    
    userAuth = request.user.is_authenticated 

    
    likeRating = None
    dislikeRating= None
    if not(userAuth):  
        albums = Musicdata.objects.order_by('-popularity')[1:50] # Sorts Songs by popularity gets 50
        albums = list(np.random.permutation(albums))[:12] #shows 12
        
        return render(
            request,
            'recommender/home.html',
            {
                'title':'Home Page',
                'year':datetime.now().year,
                'albums': albums,
                'likeRating':likeRating, 
                'dislikeRating': dislikeRating
            }
        )
    else:
        artistList = Artist.objects.order_by('follows') # Sorts Artist by followers
        artistList = artistList.reverse()[:6] # Cuts list off at first 6
        

        currentUser = request.user

        recentSongsQuery = Recently_Listened.objects.all().filter(id=currentUser.id)
        recentArtist = list()


        for obj in recentSongsQuery:
            songid = obj.songid.id
            song = Musicdata.objects.get(id=songid)
            recentArtist += song.artists

        followQuery = get_random_playlists(currentUser)

        albums = get_recomendations(currentUser)

        all_followers = Follower.objects.filter(user = request.user)
        for f in all_followers:
            fliked = Rating.objects.filter(userid = f.followed, rating = 1)
            if len(fliked) > 0:
                albums.append(random.choice(fliked).songid)

        likeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=1)
        dislikeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=(-1))
        
        return render(
            request,
            'recommender/home.html',
            {
                'title':'Home Page',
                'year':datetime.now().year,
                'artistList': artistList,
                'albums': albums,
                'recentArtist': recentArtist,
                'likeRating':likeRating, 
                'dislikeRating': dislikeRating,
                'followQuery': followQuery
            }
        )


# EXTENDED PLAYLIST PAGE
def extendedplaylist(request, playlistID = 1):
    assert isinstance(request, HttpRequest)

    if request.user.is_authenticated:
        update_likes_playlist(request.user)

    query = Playlist.objects.get(id = playlistID) # Assigns query to a given playlists id
    query2 = query.songs.all() #Gets list of songs in playlist
    listofUsers = query.user.all().values() # retuns a queryset of user objects from the user field of the playlist
    followerCount = len(listofUsers)
    
    
    
    followStatus = (request.user in query.user.all())
    isCreator = (query.creatorid == request.user)

    if request.method == 'POST':
        if 'SubmitFollow' in request.POST:
            if followStatus:
                query.user.remove(request.user)
            else:
                query.user.add(request.user)
        elif 'SubmitCopy' in request.POST:
            createdPlaylistName = request.POST.get("title")
            if (createdPlaylistName != 'Likes') and createdPlaylistName.strip(): ## does not let you name the playlist likes because of the way the likes playlist is created
                createdPlaylist = Playlist.objects.create(title = createdPlaylistName, creatorid = request.user)
                createdPlaylist.user.add(request.user)            
                createdPlaylist.songs.set(query2)
        elif 'Delete' in request.POST:     
            if isCreator and (query.title != 'Likes'):
                query.delete()
                query.save()
                return redirect(playlist)

        return redirect(request.META.get('HTTP_REFERER'))
    
    albums2 = list()
    minutes = 0
    seconds = 0
    songCounter = 0

    for song in query2:
        albums2 += find_song(song.id) #adds songs to albums list by id
        minutes += song.duration_ms
        songCounter += 1
    
    minutes = round((minutes/60000), 2)
    seconds = int((minutes - int(minutes)) * 60)
    minutes = int(minutes)

    likeRating = None
    dislikeRating= None
    if request.user.is_authenticated:
        likeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=1)
        dislikeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=(-1))



    return render(
        request,
        'recommender/extendedplaylist.html',
        {
            'title':'Extended Playlist',
            'page_percent': 100,
            'albums2': albums2,
            'query': query,
            'minutes': minutes,
            'seconds': seconds,
            'songCounter': songCounter,
            'playlistID':playlistID,
            'listofUsers': listofUsers,
            'followerCount': followerCount,
            'followStatus': followStatus,
            'isCreator': isCreator,
            'likeRating':likeRating, 
            'dislikeRating': dislikeRating
        }
    )


# PLAYLIST PAGE
def playlist(request):
    assert isinstance(request, HttpRequest)

    

    query = Playlist.objects.all() # this will be the default playlist that someone will see if they are not signed in and try to access the playlist page, could also be a redirect


    if request.method == 'POST':
        createdPlaylistName = request.POST.get("title")
        if (createdPlaylistName != 'Likes') and createdPlaylistName.strip(): ## does not let you name the playlist likes because of the way the likes playlist is created
            createdPlaylist = Playlist.objects.create(title = createdPlaylistName, creatorid = request.user)
            createdPlaylist.user.add(request.user)
        return redirect(request.META.get('HTTP_REFERER'))


    currUser = None
    userAuth = request.user.is_authenticated
    followQuery = list()
    if userAuth:
        currUser = request.user
        create_recent_playlist(currUser)
        create_likes_playlist(currUser)
        query = Playlist.objects.filter( user__exact= currUser)
        followQuery = get_followee_playlists(currUser)

    return render(
        request,
        'recommender/playlist.html',
        {
            'title':'Playlist',
            'page_percent': 100,
            'query': query,
            'currUser': currUser,
            'followQuery': followQuery
        }
    )


# ABOUT PAGE
def about(request):
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'recommender/about.html',
        {
            'title':'About Page',
            'year':datetime.now().year,
        }
    )

# SUPPORT PAGE
def contact(request):
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'recommender/contact.html',
        {
            'title':'Contact Page',
            'message':'This is a test message',
            'year':datetime.now().year,
        }
    )


# FOLLOWER AND FOLLOWING PAGES
def follow(request, name = 'nickmichelette', followtype = 'followers'):
    assert isinstance(request, HttpRequest)
    name_user = User.objects.get(username = name)
    all_followers = []
    all_users = []
    if followtype == 'followers':
        all_followers = Follower.objects.filter(followed = name_user)
        for follower in all_followers:
            # userp = Profile.objects.get(user=follower.user)
            # all_users.append(userp.value)
            pfp = None
            prof = Profile.objects.filter(user = follower.user)
            if len(prof) > 0:
                pfp = prof[0].profilepic
            all_users.append({'fuser': follower.user, 'pic': pfp})
    elif followtype == 'following':
        all_followers = Follower.objects.filter(user = name_user)
        for follower in all_followers:
            # userp = Profile.objects.get(user=follower.followed)
            # all_users.append(userp)
            pfp = None
            prof = Profile.objects.filter(user = follower.followed)
            if len(prof) > 0:
                pfp = prof[0].profilepic
            all_users.append({'fuser': follower.followed, 'pic': pfp})
    followtype = followtype.capitalize()

    return render(
        request,
        'recommender/follow.html',
        {
            'title': followtype + ' Page',
            'message':'This is a test message', # Not used anywhere
            'year':datetime.now().year,
            'all_followers': all_users,
            'page_percent': 70,
        }
    )


# REMOVE BUTTON: called when remove button is clicked
def removebutton(request):
   
    
    playlistID = request.POST['playlistID']
    songid = request.POST['song']

    currSong = Musicdata.objects.get(id=songid)

    query = Playlist.objects.get(id = playlistID)

    query.songs.remove(currSong)
    query.save()

    return JsonResponse({'text' : songid})


# LIKE BUTTON: called when like button is clicked 
def likebutton(request):
    song = request.POST['song']
    allsongs = Musicdata.objects.all().filter(id=song)
    music = allsongs[0]
    musicid = allsongs[0].id
    likestatus=  'Like'

    #get current user then checks the database to see if user has already liked this song
    if request.user.is_authenticated:
        user= request.user
        likedsong = Rating.objects.all().filter(userid=user) & Rating.objects.all().filter(songid__id=musicid) & Rating.objects.all().filter(rating=1)
        #if user has already liked the song delete like from database and lower the like count
        if likedsong.exists():
           likedsong[0].delete()
           likestatus = 'Like'
           music.likes = music.likes - 1
           music.save()
        #if user has not already liked the song add like to database and raise the like count 
        else:
            likedsong = Rating.objects.all().filter(userid=user) & Rating.objects.all().filter(songid=musicid)
            #checks to see if song is disliked if it is replace with a like
            if likedsong.exists():
                 likedsong[0].delete()
            likedsong =  Rating(userid=user, songid=music, rating=1)
            likedsong.save()
            likestatus = 'Liked'
            music.likes = music.likes + 1
            music.save()

    return JsonResponse({'text' : likestatus})


# DISLIKE BUTTON: called when dislike button is clicked 
def dislikebutton(request):
    song = request.POST['song']
    allsongs = Musicdata.objects.all().filter(id=song)
    music = allsongs[0]
    likestatus=  'Dislike'

    #get current user then checks the database to see if user has already disliked this song
    if request.user.is_authenticated:
        user= request.user
        dislikedsong = Rating.objects.all().filter(userid=user) & Rating.objects.all().filter(songid=music) & Rating.objects.all().filter(rating=(-1))
        #if user has already disliked delete dislike from database
        if dislikedsong.exists():
           dislikedsong[0].delete()
           likestatus   = 'Dislike'
        #if user has not already disliked the song add dislike to database
        else:
            dislikedsong = Rating.objects.all().filter(userid=user) & Rating.objects.all().filter(songid=music)
            #checks to see if song is liked if it is replace with a dislike
            if dislikedsong .exists():
                dislikedsong[0].delete()
            dislikedsong  =  Rating(userid=user, songid=music, rating=(-1))
            dislikedsong.save()
            likestatus  = 'Disliked'
    return JsonResponse({'text' : likestatus})


# RECENTLY LISTENED: called when a spotify iframe is clicked
def recentlylistened(request):
    song = request.POST['song']
    if request.user.is_authenticated:
        mdo = Musicdata.objects.get(id = song)
        if len(Recently_Listened.objects.filter(songid = song)) == 0:
            Recently_Listened.objects.create(userid = request.user, songid = mdo)
        else:
            rlo = Recently_Listened.objects.get(songid = song)
            rlo.datelistened = timezone.now()
            rlo.save()
        print(Recently_Listened.objects.get(songid = song).datelistened)
    return HttpResponse('')


# SEARCH PAGE: called when a user types a term in search bar in nav bar
def searchpage(request):       
     #checks to see if add to playlist button was clicked
     if request.method == 'POST':
         song = request.POST.get('song')
         return HttpResponseRedirect(reverse('playlistbutton', args=[song]))

    # searchs the database for songs that match the term entered
     else:
        term = request.GET.get('search')
        songs = Musicdata.objects.filter(Q(name__icontains=term)).distinct()[:9]
        likeRating = None
        dislikeRating= None
        if request.user.is_authenticated:
            likeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=1)
            dislikeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=(-1))
        return render(request, 'recommender/searchpage.html',{'songs': songs, 'searched': term, 'likeRating':likeRating, 'dislikeRating': dislikeRating})


# SONG_ARTIST PAGE
def song_artist(request, songid):
    assert isinstance(request, HttpRequest)
    song = Musicdata.objects.get(id = songid)
    songname = song.name

    
    #songs = Musicdata.objects.filter(Q(name__icontains=songname)).distinct()[:9]

    albums = song_recomendations(song)
    artistname = song.artists
    artistname = artistname[1:-1]


    likeRating = None
    dislikeRating= None
    if request.user.is_authenticated:
        likeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=1)
        dislikeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=(-1))
    return render(
        request, 
        'recommender/song_artist.html', 
        {
            'song': songid,
            'artist': songname,
            'albums': albums,
            'likeRating':likeRating, 
            'dislikeRating': dislikeRating,
            'artistname': artistname,
        }
    )


# Searches all of the database for an object where the string name matches the toString of a profile
# Very slow, but I'm not sure of a faster way to search via the String name
def getUserByName(name): #couldn't you do Profile.objects.filter(name = name) or something?
    for profile in Profile.objects.all():
        if(str(profile) == name):
            return profile
    return None

# Filters the query set to find all songs that the given user likes, then returns a list of songs
def getLikesByUser(userid):
    query = Rating.objects.filter(userid=userid) # Should be matching the foreign key to the primary key
    songs = []
    for song in query:
        songs.append(song.songid)
    return songs

def getNumFollower(userid):
    count = 0

    query = Follower.objects.filter(followed=userid)
    for person in query:
        count += 1
    return count

def getNumFollowing(userid):
    count = 0

    query = Follower.objects.filter(user=userid)
    for person in query:
        count += 1
    return count

# USER PAGE: Render's the page with the url /user/<name>, where the name is a variable
def userpage(request, name):
    assert isinstance(request, HttpRequest)
    userp = getUserByName(name)

    if(userp != None):
        bio = userp.bio
        profilePic = userp.profilepic
        birthday = userp.birth_date
    else:
        bio = None
        profilePic = None
        birthday = None

    # Find the user's liked songs, and then pick a random 3 of them.
    likedSongs = getLikesByUser(User.objects.get(username = name)) # Passing the user should work
    likedSongs = list(np.random.permutation(likedSongs[:10]))[:3] #Should return 4 random liked songs


    #checks to see if a user is following another user or not
    isfollowing = False
    obj = User.objects.get(username = name)
    if request.user.is_authenticated:
        if Follower.objects.filter(user = request.user, followed = User.objects.get(username = name)):
            isfollowing = True

    followerCount = getNumFollower(User.objects.get(username = name))
    followingCount = getNumFollowing(User.objects.get(username = name))

    likeRating = None
    dislikeRating= None
    if request.user.is_authenticated:
        likeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=1)
        dislikeRating = Rating.objects.all().filter(userid=request.user) & Rating.objects.all().filter(rating=(-1))

    return render(request, 'recommender/profile.html', {'usern': name,
                                                        'bio': bio,
                                                        'profilePic': profilePic,
                                                        'birthday': birthday,
                                                        'followed': isfollowing,
                                                        'followerobj': obj,
                                                        'songs': likedSongs, 
                                                        'likeRating':likeRating, 
                                                        'dislikeRating': dislikeRating,
                                                        'followerCount': followerCount,
                                                        'followingCount': followingCount})


# FOLLOW/UNFOLLOW: called when follow or unfollow button is pressed
def follow_unfollow_profile(request):
    if request.method=="POST":
        followed_user = User.objects.get(username = request.POST.get("followed_name"))
        obj = Follower.objects.filter(user = request.user, followed = followed_user)

        if obj:
            Follower.objects.get(user = request.user, followed = followed_user).delete()
        else:
            Follower.objects.create(user = request.user, followed = followed_user)
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect(home)


# LOGIN PAGE
def login(request):
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'recommender/login.html',
        {
            'title':'User Login',
        }
    )


# REGISTER PAGE
def registerpage(request):
    # if this is a POST request we need to process the form data
    template = 'registration/register.html'

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Username already exists.'
                })
            elif User.objects.filter(email=form.cleaned_data['email']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Email already exists.'
                })
            elif form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form,
                    'error_message': 'Passwords do not match.'
                })
            elif form.cleaned_data['birthday'] > date(datetime.now().year-13, datetime.now().month, datetime.now().day):
                return render(request, template, {
                    'form': form,
                    'error_message': 'You must be over 13 years old to register'
                })
            else:
                # Create the user:
                user = User.objects.create_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    form.cleaned_data['password'],
                )
                user.date_joined = form.cleaned_data['birthday'];
                user.save()

                # Login the user
                auth_login(request, user)

                # redirect to accounts page:
                return redirect( 'surveyquestion')

    else:
        form = RegisterForm()

    return render(request, template, {'form': form})
  

@login_required
def edit_profile(request, name):
    player, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        # request.FILES is show the selected image or file
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if form.is_valid() and profile_form.is_valid():
            name = form.cleaned_data['username']
            user_form = form.save()
            custom_form = profile_form.save(False)
            custom_form.user = user_form
            custom_form.save()
            messages.success(request, ('Settings have been saved'))
            return render(request, 'recommender/profilesettings.html', {'usern' : name, 'form' : form, 'profile_form' : profile_form})
        else:
                messages.error(request, ('Error saving profile settings'))
                return render(request, 'recommender/profilesettings.html', {'usern' : name, 'form' : form, 'profile_form' : profile_form})
    else:
        form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        return render(request, 'recommender/profilesettings.html', {'usern' : name, 'form' : form, 'profile_form' : profile_form})


#searchs the database for songs based on anwsers from a survey if there are no matches most popular songs are used
@login_required
def surveyquestion(request):

   if request.method == 'POST':
        form = SurveyForm(request.POST)

        # gets most popular songs in case user input does not match
        popularsongs = Musicdata.objects.order_by('-popularity')

        if form.is_valid():
            # bring in the data entered by the user
            question1 = form.cleaned_data['question1']
            question2 = form.cleaned_data['question2']
            question3 = form.cleaned_data['question3']
            question4 = form.cleaned_data['question4']

            #search for songs that are song by the users chosen artist
            artists = Musicdata.objects.filter(Q(artists__icontains=question1))
            artists = artists.order_by('-popularity')[:3]
            if artists.exists():
                song1 = artists[0]
                song2 = artists[1]
                song3 = artists[2]
            else:
                song1 = popularsongs[3]
                song2 = popularsongs[4]
                song3 = popularsongs[5]

            # search for songs that are in the decade chosen by the user 
            endOfDecade = int(question2) +10
            startOfDecade = int(question2)
            if endOfDecade < 1900:
                endOfDecade = endOfDecade + 1900
                startOfDecade = startOfDecade + 1900
            decade = Musicdata.objects.filter(year__gte =  startOfDecade)
            decade = decade.filter(year__lte = endOfDecade)
            if decade.exists():
                decade = decade.order_by('-popularity')[:3]
                song4 = decade[0]
                song5 = decade[1]
                song6 = decade[2]
            else:
                song4 = popularsongs[0]
                song5 = popularsongs[1]
                song6 = popularsongs[2]


            # search for songs that match the genre chosen by the user
            genre = Artist.objects.filter(Q(genres__icontains=question3))
            if genre.exists():
                genre = genre.order_by('-follows')[:3]
                artist1= genre[0].id
                artists1 = Musicdata.objects.filter(Q(artists__icontains=artist1)).order_by('-popularity')[:1]
                song7= artists1[0]

                artist2= genre[1].id
                artists2 = Musicdata.objects.filter(Q(artists__icontains=artist2)).order_by('-popularity')[:1]
                song8= artists2[0]

                artist3= genre[2].id
                artists3 = Musicdata.objects.filter(Q(artists__icontains=artist3)).order_by('-popularity')[:1]
                song9= artists3[0]
            else:
                song7 = popularsongs[6]
                song8 = popularsongs[7]
                song9 = popularsongs[8]



            # add the users favorite song to the users likes if it exists
            favoriteSong= Musicdata.objects.filter(Q(name__icontains=question4)).order_by('-popularity')
            if favoriteSong.exists():
                favoriteSong[0].likes = favoriteSong[0].likes +1
                favoriteSong[0].save()
                likedsong =  Rating(userid=request.user, songid=favoriteSong[0], rating=1)
                likedsong.save()

            return render(request, 'registration/surveysongs.html', 
                 {
                     'song1' : song1,
                     'song2' : song2,
                     'song3' : song3,
                     'song4' : song4,
                     'song5' : song5,
                     'song6' : song6,
                     'song7' : song7,
                     'song8' : song8,
                     'song9' : song9,
                     
                 })
    
   else:
        form = SurveyForm()
        return render(request,'registration/surveyquestion.html', {'form': form } )


@login_required
def surveysongs(request):

    if request.method == 'GET':
        user= request.user
        song1 = request.GET.get('song1')
        song2 = request.GET.get('song2')
        song3 = request.GET.get('song3')
        song4 = request.GET.get('song4')
        song5 = request.GET.get('song5')
        song6 = request.GET.get('song6')
        song7 = request.GET.get('song7')
        song8 = request.GET.get('song8')
        song9 = request.GET.get('song9')

        # loop through each song and find which songs were selcted by user
        # each selected song gets a like and is added to the ratings table 
        songs = [song1, song2, song3, song4, song5, song6, song7, song8, song9]
        for song in songs:
             if (song != None):
                 allsongs = Musicdata.objects.all().filter(id=song)
                 music = allsongs[0]
                 music.likes = music.likes +1
                 music.save()
                 likedsong =  Rating(userid=user, songid=music, rating=1)
                 likedsong.save()
        return redirect( 'home')
    
    else:
        return render(request,'registration/surveysongs.html', {'songs': songs}  )


# PLAYLIST BUTTONS
@login_required
def playlistbutton(request, song):
    currentuser = request.user
    name = currentuser.username
    allplaylists = Playlist.objects.filter(creatorid=request.user).exclude(recentylistenedplaylist=True).exclude(title="Likes")
    return render(request, 'recommender/playlistbutton.html', {'allplaylists': allplaylists, 'song' : song})

@login_required
def playlistbutton2(request):
    if request.method == 'POST':
        currentuser = request.user
        name = currentuser.username
        songid = request.POST.get('songid')
        allsongs = Musicdata.objects.all().filter(id=songid)
        song = allsongs[0]
        allplaylists = Playlist.objects.filter(user__username=name)
        for playlist in allplaylists:
            currentPlaylist = request.POST.get(playlist.title)
            if(currentPlaylist != None):
                playlist.songs.add(song)
                playlist.save()
        return redirect( 'home')

def test(request):
    return render(request, test.html, {'song1': song1} )


@login_required
def change_password(request, name):
    player, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, ('Password has been saved'))
            return render(request, 'recommender/changepassword.html', {'usern' : name, 'form' : form})
        else:
            messages.error(request, ('Error saving new password'))
            return render(request, 'recommender/changepassword.html', {'usern' : name, 'form' : form})
    else:
        form = PasswordChangeForm(request.user)
        return render(request, 'recommender/changepassword.html', {'usern' : name, 'form' : form})


# takes in a user object and creates and returns a new recentylistenedplaylist by 
# populating it with songs from the Recently_Listened table
def create_recent_playlist(currentUser):
    #deletes old recentplaylist if it exists
    recentPlaylists = Playlist.objects.all().filter(creatorid=currentUser)
    recentPlaylists = Playlist.objects.all().filter(recentylistenedplaylist=True)
    if recentPlaylists.exists():
        recentPlaylists[0].delete()

    #creates a new recentplaylist
    recentPlaylist = Playlist.objects.create(title = 'Recently Listened', creatorid = currentUser, recentylistenedplaylist=True)
    recentPlaylist.user.add(currentUser)

    #populates new playlist with songs from the Recently_Listened table
    recentSongs = Recently_Listened.objects.all().filter(userid=currentUser)
    for song in recentSongs:
        songid = song.songid.id
        music = Musicdata.objects.get(id=songid)
        recentPlaylist.songs.add(music)

    recentPlaylist.save()
    return recentPlaylist


def create_likes_playlist(currentUser):
    # finds and deletes old playlist named Likes for the user, Likes should be a reserved name
    query = Playlist.objects.filter( user__exact= currentUser)
    likesPlaylist = query.filter(title__exact= 'Likes')

    if likesPlaylist.exists():
        likesPlaylist[0].delete()
    # creates likesPlaylist
    likesPlaylist = Playlist.objects.create(title = 'Likes', creatorid = currentUser)
    likesPlaylist.user.add(currentUser)

    #populates likesPlaylist with songs from the rating table with a rating of 1
    likedSongs = Rating.objects.all().filter(userid = currentUser.id)
    for song in likedSongs:
        if song.rating == 1:
            songid = song.songid.id
            track = Musicdata.objects.get(id=songid)
            likesPlaylist.songs.add(track)
    
    likesPlaylist.save()
    return likesPlaylist

def update_likes_playlist(currentUser):
    query = Playlist.objects.filter( user__exact= currentUser)
    likesPlaylist = query.filter(title__exact= 'Likes')[0]


    likesPlaylist.songs.clear()


    likedSongs = Rating.objects.all().filter(userid = currentUser.id)
    
    for song in likedSongs:
        if song.rating == 1:
            songid = song.songid.id
            track = Musicdata.objects.get(id=songid)
            likesPlaylist.songs.add(track)
    
    likesPlaylist.save()
    return likesPlaylist


# returns 1 playlist from every follower
def get_followee_playlists(currentUser):
    followingQuery = Follower.objects.filter(user = currentUser)
    followeePlaylists = list()

    mylist = list()
    
    for x in followingQuery:
        followeePlaylists = Playlist.objects.filter( creatorid__exact= x.followed.id)
        if followeePlaylists:
            mylist.append(list(np.random.permutation(followeePlaylists))[0])

    if len(mylist) < 5:
        mylist = list()
        for x in followingQuery:
            followeePlaylists = Playlist.objects.filter( creatorid__exact= x.followed.id)
            if followeePlaylists:
                mylist += list(followeePlaylists)
    return mylist

def get_random_playlists(currentUser):
    myPlaylist = Playlist.objects.all().exclude(creatorid = currentUser)
    mylist = list(np.random.permutation(myPlaylist))[:10]
    return mylist

#returns a list of songs based on a users liked songs,  if a user has no liked songs returns random songs
def get_recomendations(user):
    # get a queryset of all liked song of the current user
    likedsongs = Rating.objects.filter(userid=user) & Rating.objects.all().filter(rating=1)
    if likedsongs.exists():
        totalTempo= 0
        totalDanceability=0
        totalLoudness =0
        numSongs = 0
        totalAcousticness = 0
        totalLiveness= 0

        
        # search the liked song list to find a users top artist
        referenced_songs = Musicdata.objects.filter(id__in=likedsongs.values('songid'))
        mostCommon = referenced_songs.values("artists").annotate(count=Count('artists')).order_by("-count")[0]
        topArtist = mostCommon['artists']
        Artiststr= topArtist.split(',')
        Artiststr= Artiststr[0].strip('[]')
        Artiststr= Artiststr.strip("''")
        artists = Artist.objects.filter(Q(id__icontains=Artiststr))[0]

        # get a users top genre based on their top artists genre
        topGenre = artists.genres
        topGenre = topGenre.split(',')
        topGenre = topGenre[0].strip("'[")


        # calculate a users prefered music taste
        for song in likedsongs:
            numSongs = numSongs + 1
            totalTempo = totalTempo + song.songid.tempo
            totalDanceability = totalDanceability + song.songid.danceability
            totalLoudness = totalLoudness + song.songid.loudness
            totalAcousticness = totalAcousticness + song.songid.acousticness
            totalLiveness = totalLiveness + song.songid.liveness
        
        if numSongs != 0:
            tempo = totalTempo/numSongs
            danceability =  totalDanceability/numSongs
            loudness = totalLoudness/numSongs
            acousticness = totalAcousticness/numSongs
            liveness = totalLiveness/numSongs



        songsList = [] 
        genreList = []
        x=0
        y=0


        # search the database for two songs from the users top artist
        matches = Musicdata.objects.filter(artists=topArtist)
        topArtistMatch= random.sample(list(matches),2)

        # search the database for two songs from two random liked artists
        if(referenced_songs.count()>= 2):
            while x<2 :
                artists = referenced_songs[x].artists
                songs = Musicdata.objects.filter(artists=artists)
                random_song = random.choice(songs)
                songsList.append(random_song)
                x = x + 1

        # Search the database for two songs that match the users top genre
        artists = Artist.objects.filter(Q(genres__icontains=topGenre))
        while y<2:
            random_artist = random.choice(artists)
            artist = random_artist.id
            song = Musicdata.objects.filter(Q(artists__icontains=artist))[0]
            genreList.append(song)
            y = y + 1

        # Search the database for six songs that match the users music taste
        matches= Musicdata.objects.filter(tempo__range=((tempo-10),(tempo+10)))  & Musicdata.objects.filter(danceability__range=((danceability-.1),(danceability+.1)))   & Musicdata.objects.filter(loudness__range=((loudness-3),(loudness+3)))  & Musicdata.objects.filter(acousticness__range=((acousticness-.1),(acousticness+.1)))  & Musicdata.objects.filter(danceability__range=((danceability-.1),(danceability+.1)))   & Musicdata.objects.filter(loudness__range=((loudness-3),(loudness+3)))  & Musicdata.objects.filter(liveness__range=((liveness-.1),(liveness+.1))) & Musicdata.objects.order_by('-popularity')
        tasteMatch = random.sample(list(matches),6)

        allSongs= topArtistMatch + songsList + genreList + tasteMatch
    else:
        topSongs = Musicdata.objects.order_by('-popularity')[1:50]
        allSongs =  list(np.random.permutation(topSongs))[:12]
         
        

    return allSongs


# returns a list of songs based on the song passed in 
def song_recomendations(song):
    # save song data to variables
    tempo = song.tempo
    danceability =  song.danceability
    loudness = song.loudness
    acousticness = song.acousticness
    liveness = song.liveness

    # get the artist of the song
    artist = song.artists
    artist = artist.split(',')
    artist = artist[0].strip("'[]'")
    artists = Artist.objects.filter(Q(id__icontains=artist))[0]

    # get the genre of the song 
    topGenre = artists.genres
    topGenre = topGenre.split(',')
    topGenre = topGenre[0].strip("'[]'")

    # search the database for three songs from the same artist
    artistMatch= []
    matches = Musicdata.objects.filter(Q(artists__icontains=artist))
    if(matches.count()>= 3):
        artistMatch= random.sample(list(matches),3)

    # search the database for three songs from the same genre
    artists = Artist.objects.filter(Q(genres__icontains=topGenre))
    genreList = []
    x=0
    while x<3:
            random_artist = random.choice(artists)
            artist = random_artist.id
            song = Musicdata.objects.filter(Q(artists__icontains=artist))[0]
            genreList.append(song)
            x = x + 1

    
    # search the database for song with similar data
    matches= Musicdata.objects.filter(tempo__range=((tempo-10),(tempo+10)))  & Musicdata.objects.filter(danceability__range=((danceability-.1),(danceability+.1)))   & Musicdata.objects.filter(loudness__range=((loudness-3),(loudness+3)))  & Musicdata.objects.filter(acousticness__range=((acousticness-.1),(acousticness+.1)))  & Musicdata.objects.filter(danceability__range=((danceability-.1),(danceability+.1)))   & Musicdata.objects.filter(loudness__range=((loudness-3),(loudness+3)))  & Musicdata.objects.filter(liveness__range=((liveness-.1),(liveness+.1))) & Musicdata.objects.order_by('-popularity')
    tasteMatch = random.sample(list(matches),6)


    allSongs = artistMatch + genreList + tasteMatch
    return allSongs


# ERROR PAGES
def error_404(request, Exception=None):
    return render(
        request,
        'recommender/error.html',
        {
            'title': "Error",
            'errornum': 404,
            'errormsg':'Page Not Found',
            'year':datetime.now().year,
        }
    )

def error_500(request, Exception=None):
    return render(
        request,
        'recommender/error.html',
        {
            'title': "Error",
            'errornum': 500,
            'errormsg':'Server Error',
            'year':datetime.now().year,
        }
    )

def error_403(request, Exception=None):
    return render(
        request,
        'recommender/error.html',
        {
            'title': "Error",
            'errornum': 403,
            'errormsg':'Permission Denied',
            'year':datetime.now().year,
        }
    )

def error_400(request, Exception=None):
    return render(
        request,
        'recommender/error.html',
        {
            'title': "Error",
            'errornum': 400,
            'errormsg':'Bad Request',
            'year':datetime.now().year,
        }
    )
   






