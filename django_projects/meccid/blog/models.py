from django.contrib.auth.models import User, UserManager
from django.db import models
import datetime
from django.contrib import admin
from threadedcomments import ThreadedComment
from django.contrib.auth.models import UserManager
from django.forms import Form
from django import forms
from django.db.models.signals import post_save

class UserProfile(models.Model):
    user = models.OneToOneField(User,primary_key=True)
    karma = models.IntegerField(default = 0)
    objects = UserManager()
    def __unicode__(self):
        return self.user.username

class BlogPost(models.Model):
#    id = models.IntegerField(primary_key=True)
    author = models.ForeignKey(User)
    title = models.CharField(max_length=128)
    body = models.TextField()
    published = models.BooleanField(default=True)
    date_posted = models.DateTimeField(default=datetime.datetime.now)
    baseThreadID = models.OneToOneField(ThreadedComment)
    postKarma = models.IntegerField(default=0)
    postNumComments = models.IntegerField(default=0)
    category = models.CharField(max_length=10, default='other')
    
    def __unicode__(self):
        return self.title

class UserForm(forms.Form):
    username = forms.CharField(max_length=10,required=True, help_text='The username you want.')
    email = forms.EmailField(required=True, help_text='Please enter your e-mail.')
    password = forms.CharField(label=(u'Password'),widget=forms.PasswordInput(render_value=False))

    def clean_email(self):
        field_data = self.cleaned_data['email']

        if not field_data:
            return ''

        u = User.objects.filter(email=field_data)
        if len(u) > 0:
            raise forms.ValidationError('This e-mail is already registered.')

        return field_data
    def clean_username(self):
        field_data = self.cleaned_data['username']

        if not field_data:
            return ''

        u = User.objects.filter(username=field_data)
        if len(u) > 0:
            raise forms.ValidationError('This username is already registered.')

        return field_data


class Tag(models.Model):
    mid = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=50)
    notableForID = models.CharField(max_length=50)
    notableForName = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name
    
class TagUserPost(models.Model):
    title = models.CharField(max_length=150)
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    post = models.ForeignKey(BlogPost)

    def __unicode__(self):
        return self.title

class TagToTag(models.Model):
    title = models.CharField(max_length=100)
    tag1 = models.ForeignKey(Tag, related_name='tagtotag_tag1')
    tag2 = models.ForeignKey(Tag, related_name='tagtotag_tag2')
    bound = models.IntegerField(default=1)
    isSibling = models.BooleanField(default=False)
    isInstance = models.IntegerField(default=0)

    def __unicode__(self):
        return self.title

class UserToUser(models.Model):
    title = models.CharField(max_length=100)
    user1 = models.ForeignKey(User, related_name='usertouser_user1')
    user2 = models.ForeignKey(User, related_name='usertouser_user2')
    boundTag = models.IntegerField(default=0)  
    boundPost1to2 = models.IntegerField(default=0)
    boundPost2to1 = models.IntegerField(default=0)
    boundVote1to2 = models.IntegerField(default=0)
    boundVote2to1 = models.IntegerField(default=0)
    def __unicode__(self):
        return self.title
    


admin.site.register(BlogPost)
admin.site.register(UserProfile)
admin.site.register(Tag)
admin.site.register(TagToTag)
admin.site.register(UserToUser)
admin.site.register(TagUserPost)