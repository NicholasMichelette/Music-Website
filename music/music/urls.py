"""music URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from recommender import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('recommender/', include('recommender.urls')),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('recommender/best/', views.searchform_get, name='best'),
    path('recommender/bestp/', views.searchform_post, name='bestp'),
    path('song_artist/<str:songid>/', views.song_artist, name='song_artist'),
    path('users/<str:name>/', views.userpage, name='users'),
    path('users/<str:name>/profilesettings/', views.edit_profile, name='profilesettings'),
    path('users/<str:name>/profilesettings/changepassword', views.change_password, name='changepassword'),
    path('users/<str:name>/<str:followtype>/', views.follow, name='follow'),
    path('register/', views.registerpage, name='registerpage'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('playlist/', views.playlist, name ='playlist'),
    path('surveyquestion/', views.surveyquestion, name= 'surveyquestion'),
    path('surveysongs/', views.surveysongs, name= 'surveysongs'),
    path('test/', views.test, name='test'),
    path('follow_unfollow/', views.follow_unfollow_profile, name="follow_unfollow"),
    path('extendedplaylist/<int:playlistID>/', views.extendedplaylist, name ='extendedplaylist'),
    path('searchpage/', views.searchpage, name= 'searchpage'),
    path('playlistbutton/<str:song>', views.playlistbutton, name='playlistbutton'),
    path('playlistbutton2/', views.playlistbutton2, name='playlistbutton2'),
    path('createPlaylist/', views.createPlaylist, name='createPlaylist'),
    path('likebutton/', views.likebutton, name = 'likebutton'),
    path('dislikebutton/', views.dislikebutton, name = 'dislikebutton'),
    path('removebutton/', views.removebutton, name = 'removebutton'),
    path('recentlylistened/', views.recentlylistened, name = 'recentlylistened')

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler404 = 'recommender.views.error_404'
handler500 = 'recommender.views.error_500'
handler403 = 'recommender.views.error_403'
handler400 = 'recommender.views.error_400'