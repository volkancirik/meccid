from django.contrib.auth import logout
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from freebase.api.session import HTTPMetawebSession
from meccid.blog.models import UserToUser, TagUserPost
from meccid.blog.models import UserProfile
from models import BlogPost
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse
from threadedcomments import ThreadedComment
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from voting.models import Vote
from meccid.blog.models import UserForm
from meccid.blog.models import Tag
from meccid.blog.models import TagToTag
from django.contrib.auth.decorators \
import login_required
from django.contrib.auth import authenticate, login
#from SPARQLWrapper import SPARQLWrapper, JSON
from freebase import HTTPMetawebSession
from django.db import transaction
from django.db.models import Q
import datetime
import freebase
from django.utils import simplejson
from collections import OrderedDict

def replyItem(request,page_id,tIndex):
    try:
        reply = ThreadedComment.objects.get( pk = tIndex)
    except ThreadedComment.DoesNotExist:
        raise Http404
    try:
        post = BlogPost.objects.get(pk = page_id)
    except BlogPost.DoesNotExist:
        raise Http404
    try:
        baseSet = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(post.baseThreadID.pk)))
    except ThreadedComment.DoesNotExist:
        raise Http404

    postSet = BlogPost.objects.filter(pk = page_id)
    tags = list()
    
    return render_to_response('view_page.html', {'post' : post, 'postSet' : postSet,'base' : baseSet,'reply':reply ,'tags': tags },context_instance = RequestContext(request)
    )
#    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

def updateUserToUser(request,page_id,author):
    try:
        post = BlogPost.objects.get(pk = page_id)
    except BlogPost.DoesNotExist:
        raise Http404

    try:
        authorUser = User.objects.get( username = author)
    except User.DoesNotExist:
        raise Http404

    if not authorUser.id == request.user.id:
        baseT = ThreadedComment.objects.get(pk = post.baseThreadID)
        set = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(baseT.id)), user = request.user)

        if set.count() < 2:  # If the only instance is the one just created.
            try:
                utu = UserToUser.objects.get(user1 = request.user, user2 = authorUser)
                utu.boundPost1to2 += 1
                utu.save()
            except UserToUser.DoesNotExist:
                try:
                    utu = UserToUser.objects.get(user2 = request.user, user1 = authorUser)
                    utu.boundPost2to1 += 1
                    utu.save()
                except UserToUser.DoesNotExist:
                    utu = UserToUser.objects.create(user1 = request.user, user2 = authorUser, title = request.user.username + " " + authorUser.username)
                    utu.boundPost1to2 += 1
                    utu.save()
    return HttpResponseRedirect("/blog/page/"+str(page_id)+"/")

votes = {"up" : +1, "down": -1 ,"clear" : 0}

def voteObject(request,page_id,tIndex,direction):
    
    if not request.user.is_authenticated():
           raise Http404
    try:
        reply = ThreadedComment.objects.get( pk = tIndex)
    except ThreadedComment.DoesNotExist:
        raise Http404

    if reply.user.id == request.user.id:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

    user = request.user
    if Vote.objects.get_for_user(reply, user) is None:
        voteBefore = 0
    else:
        voteBefore = Vote.objects.get_for_user(reply, user).vote

    vote = votes[direction]
    custom = UserProfile.objects.get( pk = reply.user.id)
    custom.karma = custom.karma + vote - voteBefore
    custom.save()
    Vote.objects.record_vote(reply,user,vote)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
def voteObjectScr(request,tIndex,direction):

    if not request.user.is_authenticated():
           raise Http404
    try:
        reply = ThreadedComment.objects.get( pk = tIndex)
    except ThreadedComment.DoesNotExist:
        raise Http404

    if reply.user.id == request.user.id:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

    user = request.user
    if Vote.objects.get_for_user(reply, user) is None:
        voteBefore = 0
    else:
        voteBefore = Vote.objects.get_for_user(reply, user).vote

    vote = votes[direction]
    custom = UserProfile.objects.get( pk = reply.user.id)
    custom.karma = custom.karma + vote - voteBefore
    custom.save()
    Vote.objects.record_vote(reply,user,vote)
    score = Vote.objects.get_score(reply)['score']
    return HttpResponse(simplejson.dumps({'message': str(score),'votebefore':voteBefore }),
                        mimetype='application/json')
#    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

def jscript(request):

    return render_to_response(
        'bla.html', context_instance = RequestContext(request))

@login_required
def view_page(request, page_id):
    try:
        post = BlogPost.objects.get(pk = page_id)
    except BlogPost.DoesNotExist:
        raise Http404
    baseT = ThreadedComment.objects.get(pk = post.baseThreadID)

    baseSet = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(baseT.comment_ptr_id)))

    newSet = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(baseT.comment_ptr_id)))
    newSet = newSet.order_by('-submit_date')
    latestTC = newSet[0]


    post.postNumComments = baseSet.count() -1
    post.save()
    postSet = BlogPost.objects.filter(pk = page_id)

    tagSet = list()
    try:
        tups = TagUserPost.objects.filter(post =  post)
        for tup in tups:
            tag = Tag.objects.get(pk = tup.tag.mid)
            tagSet.append(tag)
        imageID = "NULL"
        if len(tagSet)>0:
            headTag = tagSet[0]
            query=[{"mid":headTag.mid,"/common/topic/image" : [{"id" : None,"optional": True}]}]
            result = freebase.mqlread(query,extended=True)
            if(len(result[0]["/common/topic/image"]))>0:
                imageID = result[0]["/common/topic/image"][0]["id"]
    except TagUserPost.DoesNotExist:
        pass
    
    return render_to_response( "view_page.html", {"post":post, "postSet": postSet ,'base' : baseSet,'user' : request.user, 'tags' : tagSet,'latestTC' : latestTC.comment_ptr_id,'imageID': imageID},context_instance = RequestContext(request))

@login_required
def new_post(request):
   return render_to_response("new_post.html",{"user": request.user})

@login_required
def new_post_save(request):
    page_name =  request.POST["page_name"]
    content =  request.POST["content"]
    postCategory = request.POST["cat"]

    baseT = ThreadedComment.objects.create(name = "base"+page_name, title = "base" ,content_type_id ='9',site_id='1', submit_date = datetime.datetime.now())
    page = BlogPost.objects.create(title = page_name,body = content, author = request.user, category = postCategory,baseThreadID_id  =baseT.comment_ptr_id, date_posted = datetime.datetime.now())

    baseT.tree_path = page.id
    baseT.save()

    tagList = list()
    if request.method == "POST":
         for tokenItem in request.POST.getlist('token'):
             query=[{"id": tokenItem, "mid":None, "/common/topic/notable_for": [],"name":[]}]

             result = freebase.mqlread(query,extended=True)
             try:
                tagInstance = Tag.objects.get(pk = result[0]['mid'])
             except Tag.DoesNotExist:
                notableName = "NULL"
                notableID = "NULL"
                if len(result[0]["/common/topic/notable_for"])>0:
                    res2 = freebase.mqlread([{"id": result[0]["/common/topic/notable_for"][0],"name":[]}],extended=True)
                    notableName = res2[0]['name'][0]
                    notableID = result[0]["/common/topic/notable_for"][0]
                tagInstance = Tag.objects.create(mid = result[0]['mid'], name = result[0]['name'][0],notableForID = notableID,notableForName = notableName)
             tagList.append(tagInstance)

    for tagInstance in tagList:
        try:
            TagUserPost.objects.get(tag = tagInstance, user = request.user, post = page)
        except TagUserPost.DoesNotExist:
            TagUserPost.objects.create(tag = tagInstance, user = request.user, post = page, title = tagInstance.name + " " +request.user.username + " " + page.title)

            tupList = TagUserPost.objects.filter(tag = tagInstance)
            for tupInstance in tupList:
                if not tupInstance.user.id == request.user.id:
                    try:
                        utu = UserToUser.objects.get(user1 = request.user, user2 = tupInstance.user)
                        utu.boundTag += 1
                        utu.save()
                    except UserToUser.DoesNotExist:
                        try:
                            utu = UserToUser.objects.get(user2 = request.user, user1 = tupInstance.user)
                            utu.boundTag += 1
                            utu.save()
                        except UserToUser.DoesNotExist:
                            utu = UserToUser.objects.create(user1 = request.user, user2 = tupInstance.user, title = request.user.username + " " + tupInstance.user.username)
                            utu.boundTag += 1
                            utu.save()
    for i in range(len(tagList)):
        tagInstanceI = tagList[i]
        for j in range(i+1,len(tagList)):
            tagInstanceII =  tagList[j]
            try:
                T2Tinstance = TagToTag.objects.get(tag1 = tagInstanceI, tag2 = tagInstanceII)
                T2Tinstance.bound = T2Tinstance.bound+1
                T2Tinstance.save()
            except TagToTag.DoesNotExist:
                try :
                    T2Tinstance = TagToTag.objects.get(tag1 = tagInstanceII, tag2 = tagInstanceI)
                    T2Tinstance.bound = T2Tinstance.bound+1
                    T2Tinstance.save()
                except TagToTag.DoesNotExist:
                    isSib = False
                    isInst = 0
                    if tagInstanceI.notableForID == tagInstanceII.notableForID and tagInstanceII.notableForID != "NULL":
                        isSib = True
                    if tagInstanceI.notableForName == tagInstanceII.name:
                        isInst = 1
                    elif tagInstanceII.notableForName == tagInstanceI.name:
                        isInst = 2
                    TagToTag.objects.create(tag1_id = tagInstanceI.mid, tag2_id = tagInstanceII.mid, title = tagInstanceI.name+tagInstanceII.name, isSibling = isSib, isInstance =isInst)

    return HttpResponseRedirect("/blog/page/"+str(page.id)+"/")


def logout_page(request):
    logout(request)
    return HttpResponseRedirect("/main/") # return HttpResponseRedirect('/')

def main_view(request):
    return HttpResponseRedirect("/main/date/all/")

def listAll(request,sort,filter):
    posts = list()
    result_count = -1
    searched = 0
    if request.method == 'POST':
        searched = 1
        category =  request.POST["category"]
        keyword =  request.POST["keyword"]

        if category == "k":
            all_posts = BlogPost.objects.all()
            posts_dict = all_posts.filter(Q(body__contains=keyword) | Q(title__contains=keyword) )
            posts = list()
            for post in posts_dict:
                posts.append(post)
            
            comments = ThreadedComment.objects.filter(comment__contains=keyword)
            for comment in comments:
                for post in all_posts:
                    baseT = ThreadedComment.objects.get(pk = post.baseThreadID)
                    if comment.tree_path.__contains__('%010i' % int(baseT.comment_ptr_id)) and not posts.__contains__(post):
                        posts.append(post)

        elif category=="u":
            try:
                user= User.objects.get(username = keyword)
                return HttpResponseRedirect("/profile/"+keyword)
            except User.DoesNotExist:
                pass
        else:
            try:
                result = TagUserPost.objects.filter(tag__name__contains = keyword)
                posts = list()
                for tup in result:
                    posts.append(tup.post)
            except TagUserPost.DoesNotExist:
                pass
        result_count = posts.__len__()
    else:
        if filter == "all":
            try:
                posts = BlogPost.objects.all()
            except BlogPost.DoesNotExist:
                pass
        else:
            try:
                posts = BlogPost.objects.filter(category = filter)
            except BlogPost.DoesNotExist:
                pass
        if sort == "date":
            posts = posts.order_by('-date_posted')

        elif sort == "vote":
            for post in posts:
                post.postKarma =  Vote.objects.get_score(post)['score']
                post.save()
            posts = posts.order_by('-postKarma')

        elif sort == "pop":
            posts = posts.order_by('-postNumComments')

        elif sort == "recent":
            postDate = dict()
            for aPost in posts:
                    baseT = ThreadedComment.objects.get(pk = aPost.baseThreadID)
    #                baseSet = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(baseT.comment_ptr_id))).order_by('-submit_date')
                    baseSet = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(baseT.comment_ptr_id)))
                    baseSet = baseSet.order_by('-submit_date')

                    dictItem = {baseSet[0].submit_date : aPost   }
                    postDate.update(dictItem)


            ordered = OrderedDict(sorted(postDate.items(), key=lambda t: t[0]))
            posts = list()
            for key in ordered:
                posts.append(ordered[key])
    posts.reverse()
    post_pages = posts
    paginator = Paginator(post_pages, 15)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        post_pages = paginator.page(page)
    except (EmptyPage, InvalidPage):
        post_pages = paginator.page(paginator.num_pages)

    return render_to_response('listAll.html', {'post' : posts, 'filter' : filter, 'sort' : sort, 'post_pages' : post_pages, 'result_count' : result_count},context_instance = RequestContext(request) )

def sort(request,criteria):

    if criteria == "date":
            post = BlogPost.objects.order_by('-date_posted')
            return render_to_response('listAll.html', {'post' : post},context_instance = RequestContext(request) )
    if criteria == "vote":
            postList = BlogPost.objects.all()
            for post in postList:
                post.postKarma =  Vote.objects.get_score(post)['score']
                post.save()
            postList = BlogPost.objects.filter().order_by('-postKarma')
            return render_to_response('listAll.html', {'post' : postList},context_instance = RequestContext(request) )
    if criteria == "pop":
            postList = BlogPost.objects.filter().order_by('-postNumComments')
            return render_to_response('listAll.html', {'post' : postList},context_instance = RequestContext(request) )

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def votePost(request,pIndex,direction):

    if not request.user.is_authenticated():
           raise Http404
    try:
        post = BlogPost.objects.get( pk = pIndex)
    except BlogPost.DoesNotExist:
        raise Http404

    if post.author.id == request.user.id:
       return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

    user = request.user
    if Vote.objects.get_for_user(post, user) is None:
        voteBefore = 0
    else:
        voteBefore = Vote.objects.get_for_user(post, user).vote

    vote = votes[direction]
    custom = UserProfile.objects.get( pk = post.author_id)
    custom.karma = custom.karma + vote - voteBefore
    custom.save()
    Vote.objects.record_vote(post,user,vote)

    if not post.author.id == request.user.id:
        try:
            utu = UserToUser.objects.get(user1 = request.user, user2 = post.author)
            utu.boundVote1to2 += vote - voteBefore
            utu.save()
        except UserToUser.DoesNotExist:
            try:
                utu = UserToUser.objects.get(user2 = request.user, user1 = post.author)
                utu.boundVote2to1 += vote - voteBefore
                utu.save()
            except UserToUser.DoesNotExist:
                utu = UserToUser.objects.create(user1 = request.user, user2 = post.author, title = request.user.username + " " + post.author.username)
                utu.boundVote1to2 += vote - voteBefore
                utu.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

@login_required
def votePostScr(request,pIndex,direction):

    if not request.user.is_authenticated():
           raise Http404
    try:
        post = BlogPost.objects.get( pk = pIndex)
    except BlogPost.DoesNotExist:
        raise Http404

    if post.author.id == request.user.id:
       return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

    user = request.user
    if Vote.objects.get_for_user(post, user) is None:
        voteBefore = 0
    else:
        voteBefore = Vote.objects.get_for_user(post, user).vote

    vote = votes[direction]
    custom = UserProfile.objects.get( pk = post.author_id)
    custom.karma = custom.karma + vote - voteBefore
    custom.save()
    Vote.objects.record_vote(post,user,vote)

    if not post.author.id == request.user.id:
        try:
            utu = UserToUser.objects.get(user1 = request.user, user2 = post.author)
            utu.boundVote1to2 += vote - voteBefore
            utu.save()
        except UserToUser.DoesNotExist:
            try:
                utu = UserToUser.objects.get(user2 = request.user, user1 = post.author)
                utu.boundVote2to1 += vote - voteBefore
                utu.save()
            except UserToUser.DoesNotExist:
                utu = UserToUser.objects.create(user1 = request.user, user2 = post.author, title = request.user.username + " " + post.author.username)
                utu.boundVote1to2 += vote - voteBefore
                utu.save()

    score = Vote.objects.get_score(post)['score']
    return HttpResponse(simplejson.dumps({'message': str(score),'votebefore':voteBefore }),
                        mimetype='application/json')
    #return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))


def votePostView(request,page_id,pIndex,direction):

    if not request.user.is_authenticated():
           raise Http404
    try:
        post = BlogPost.objects.get( pk = pIndex)
    except BlogPost.DoesNotExist:
        raise Http404

    if post.author.id == request.user.id:
       return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

    user = request.user
    if Vote.objects.get_for_user(post, user) is None:
        voteBefore = 0
    else:
        voteBefore = Vote.objects.get_for_user(post, user).vote

    vote = votes[direction]
    custom = UserProfile.objects.get( pk = post.author_id)
    custom.karma = custom.karma + vote - voteBefore
    custom.save()
    Vote.objects.record_vote(post,user,vote)

    if not post.author.id == request.user.id:
        try:
            utu = UserToUser.objects.get(user1 = request.user, user2 = post.author)
            utu.boundVote1to2 += vote - voteBefore
            utu.save()
        except UserToUser.DoesNotExist:
            try:
                utu = UserToUser.objects.get(user2 = request.user, user1 = post.author)
                utu.boundVote2to1 += vote - voteBefore
                utu.save()
            except UserToUser.DoesNotExist:
                utu = UserToUser.objects.create(user1 = request.user, user2 = post.author, title = request.user.username + " " + post.author.username)
                utu.boundVote1to2 += vote - voteBefore
                utu.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

# direct_to_template, {'template':'news/test.txt', 'mimetype':'text/plain'})
def registerUser(request):
    if request.method == 'POST':
        formset = UserForm(request.POST, request.FILES)
        if formset.is_valid():
            newUser =  User.objects.create_user(formset.data['username'], formset.data['email'], formset.data['password'])
            custom = UserProfile(user = newUser)
            custom.user_id = newUser.id
            custom.save()
            newUser = authenticate(username=request.POST['username'],password=request.POST['password'])
            login(request, newUser)

            return render_to_response("registration/registerSuccess.html",{"userKarma": custom.karma})
        else:
            return render_to_response("registration/register.html", {"formset": formset})
    else:
        userForm = UserForm()
        return render_to_response("registration/register.html", {"formset": userForm})

def profileView(request):

    if request.method == "POST":
        author = request.POST["authorname"]
        author = author[0:len(author)-1]
        givenuser =User.objects.get( username = author)
        try:
            givenUserProfile = UserProfile.objects.get(  pk  = givenuser.id)
        except UserProfile.DoesNotExist:
            givenUserProfile = UserProfile(user = request.user)
            givenUserProfile.user_id = request.user.id
            givenUserProfile.save()
    else:
            try:
                givenUserProfile = UserProfile.objects.get( pk = request.user.id)
            except UserProfile.DoesNotExist:
                givenUserProfile = UserProfile(user = request.user)
                givenUserProfile.user_id = request.user.id
                givenUserProfile.save()

    posts = BlogPost.objects.filter(author = givenUserProfile )
    posts = list(posts)
    comments = ThreadedComment.objects.filter(user_name = request.user.username)
    all_posts = BlogPost.objects.all()

    for comment in comments:
        for post in all_posts:
            baseT = ThreadedComment.objects.get(pk = post.baseThreadID)
            if comment.tree_path.__contains__('%010i' % int(baseT.comment_ptr_id)) and not posts.__contains__(post):
                    posts.append(post)
    post_pages = posts
    paginator = Paginator(post_pages, 15) # Show 25 contacts per page

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        post_pages = paginator.page(page)
    except (EmptyPage, InvalidPage):
        post_pages = paginator.page(paginator.num_pages)
    return render_to_response("profile.html",{"userInfo": givenUserProfile,"user": request.user,"post_pages":post_pages})

def profileViewName(request,uname):

    post_pages = list()
    try:
        givenuser = User.objects.get( username = uname)
        try:
                givenUserProfile = UserProfile.objects.get( pk = givenuser.id)
        except UserProfile.DoesNotExist:
            givenUserProfile = UserProfile(user = givenuser)
            givenUserProfile.user_id = givenuser.id
            givenUserProfile.save()

        posts = BlogPost.objects.filter(author = givenUserProfile )
        posts = list(posts)
        comments = ThreadedComment.objects.filter(user_name = uname)
        all_posts = BlogPost.objects.all()

        for comment in comments:
            for post in all_posts:
                baseT = ThreadedComment.objects.get(pk = post.baseThreadID)
                if comment.tree_path.__contains__('%010i' % int(baseT.comment_ptr_id)) and not posts.__contains__(post):
                        posts.append(post)
        post_pages = posts
        paginator = Paginator(post_pages, 15) # Show 25 contacts per page
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        try:
            post_pages = paginator.page(page)
        except (EmptyPage, InvalidPage):
            post_pages = paginator.page(paginator.num_pages)
    except User.DoesNotExist:
        error = "User Not Found!"
        return render_to_response("profile.html",{"error": error},context_instance = RequestContext(request) )
            
    return render_to_response("profile.html",{"post" : posts, "userInfo" : givenUserProfile,"post_pages" : post_pages },context_instance = RequestContext(request) )

def filterPost(request,criteria):

    post = BlogPost.objects.filter( category = criteria)
    return render_to_response('listAll.html', {'post' : post},context_instance = RequestContext(request) )

def sample(request):

    return render_to_response("bla.html",{})

def addTag(request,page_id,owner,contributor):

    page = BlogPost.objects.get(pk = page_id)

    tagSet = set()
    prevList = list()
    whoAdds = User.objects.get( id = contributor)
    try:
        tups = TagUserPost.objects.filter(post =  page)
        for tup in tups:
            tag = Tag.objects.get(pk = tup.tag.mid)
            tagSet.add(tag.mid)
            prevList.append(tag)
    except TagUserPost.DoesNotExist:
        pass
    
    tagList = list()
    if request.method == "POST":
         for tokenItem in request.POST.getlist('token'):
             query=[{"id": tokenItem, "mid":None, "/common/topic/notable_for": [],"name":[]}]
             result = freebase.mqlread(query,extended=True)
             try:
                tagInstance = Tag.objects.get(pk = result[0]['mid'])
                tagList.append(tagInstance)
             except Tag.DoesNotExist:
                notableName = "NULL"
                notableID = "NULL"
                if len(result[0]["/common/topic/notable_for"])>0:
                    res2 = freebase.mqlread([{"id": result[0]["/common/topic/notable_for"][0],"name":[]}],extended=True)
                    notableName = res2[0]['name'][0]
                    notableID = result[0]["/common/topic/notable_for"][0]
                tagInstance = Tag.objects.create(mid = result[0]['mid'], name = result[0]['name'][0],notableForID = notableID,notableForName = notableName)
                tagList.append(tagInstance)
            
    newList = list()
    for tagInstance in tagList:
        if tagInstance.mid not in tagSet:
            try:
                TagUserPost.objects.get(tag = tagInstance, user = request.user, post = page)
            except TagUserPost.DoesNotExist:
                newList.append(tagInstance)
                TagUserPost.objects.create(tag = tagInstance, user = whoAdds, post = page, title = tagInstance.name + " " +whoAdds.username + " " + page.title)
                tupList = TagUserPost.objects.filter(tag = tagInstance)
                for tupInstance in tupList:
                    if not tupInstance.user.id == request.user.id:
                        try:
                            utu = UserToUser.objects.get(user1 = request.user, user2 = tupInstance.user)
                            utu.boundTag += 1
                            utu.save()
                        except UserToUser.DoesNotExist:
                            try:
                                utu = UserToUser.objects.get(user2 = request.user, user1 = tupInstance.user)
                                utu.boundTag += 1
                                utu.save()
                            except UserToUser.DoesNotExist:
                                utu = UserToUser.objects.create(user1 = request.user, user2 = tupInstance.user, title = request.user.username + " " + tupInstance.user.username)
                                utu.boundTag += 1
                                utu.save()

    for i in range(len(newList)):
        tagInstanceI = newList[i]
        for j in range(i+1,len(newList)):
            tagInstanceII =  newList[j]
            try:
                T2Tinstance = TagToTag.objects.get(tag1 = tagInstanceI, tag2 = tagInstanceII)
                T2Tinstance.bound = T2Tinstance.bound+1
                T2Tinstance.save()
            except TagToTag.DoesNotExist:
                try :
                    T2Tinstance = TagToTag.objects.get(tag1 = tagInstanceII, tag2 = tagInstanceI)
                    T2Tinstance.bound = T2Tinstance.bound+1
                    T2Tinstance.save()
                except TagToTag.DoesNotExist:
                    isSib = False
                    isInst = 0
                    if tagInstanceI.notableForID == tagInstanceII.notableForID and tagInstanceII.notableForID != "NULL":
                        isSib = True
                    if tagInstanceI.notableForName == tagInstanceII.name:
                        isInst = 1
                    elif tagInstanceII.notableForName == tagInstanceI.name:
                        isInst = 2
                    T2Tinstance = TagToTag.objects.create(tag1_id = tagInstanceI.mid, tag2_id = tagInstanceII.mid, title = tagInstanceI.name+tagInstanceII.name, isSibling = isSib, isInstance =isInst)

    for i in range(len(prevList)):
        tagInstanceI = prevList[i]
        for j in range(len(newList)):
            tagInstanceII =  newList[j]
            try:
                T2Tinstance = TagToTag.objects.get(tag1 = tagInstanceI, tag2 = tagInstanceII)
                T2Tinstance.bound = T2Tinstance.bound+1
                T2Tinstance.save()
            except TagToTag.DoesNotExist:
                try :
                    T2Tinstance = TagToTag.objects.get(tag1 = tagInstanceII, tag2 = tagInstanceI)
                    T2Tinstance.bound = T2Tinstance.bound+1
                    T2Tinstance.save()
                except TagToTag.DoesNotExist:
                    isSib = False
                    isInst = 0
                    if tagInstanceI.notableForID == tagInstanceII.notableForID and tagInstanceII.notableForID != "NULL":
                        isSib = True
                    if tagInstanceI.notableForName == tagInstanceII.name:
                        isInst = 1
                    elif tagInstanceII.notableForName == tagInstanceI.name:
                        isInst = 2
                    T2Tinstance = TagToTag.objects.create(tag1_id = tagInstanceI.mid, tag2_id = tagInstanceII.mid, title = tagInstanceI.name+" - "+tagInstanceII.name, isSibling = isSib, isInstance =isInst)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

def sparql(request):

    token = list()
    if request.method == "POST":
#        fSession = HTTPMetawebSession("api.freebase.com")
        
        r = list()
        for tokenItem in request.POST.getlist('token'):
         query=[{"id": tokenItem, "mid":None, "/common/topic/notable_for": [{}],"name":[]   }]
         result = freebase.mqlread(query,extended=True)
        return render_to_response("sparql.html",{"list":r})

    return render_to_response("sparql.html",{})

def freeBase(request):

    albumList = list()                                # Use the metaweb module
    albums_by_bob = [{'id':'/en/pearl_jam','type': []}]
    fSession = HTTPMetawebSession("api.freebase.com")
    q = [{"id" : "/en/the_beatles", "/common/topic/article" : {"id" : None, "optional" : True, "limit" : 1}}]
    r = fSession.mqlread(albums_by_bob)
#    article_id = r["/common/topic/article"]["id"]
#    result = fSession.raw('/m/0b1zz')
#    result = fSession.mqlread(albums_by_bob)
#    for album in result:  # Loop through query results
#        albumList.append(album)                        # Print album names
#    albumList.append(result)
#    return render_to_response("freebase.html",{"list":albumList})
    return render_to_response("freebase.html",{"text":r})

def treePath(request, page_id):
    try:
        post = BlogPost.objects.get(pk = page_id)
    except BlogPost.DoesNotExist:
        raise Http404
    baseT = ThreadedComment.objects.get(pk = post.baseThreadID)
    baseSet = ThreadedComment.objects.filter(tree_path__contains = ('%010i' % int(baseT.comment_ptr_id)))

    return render_to_response(
        'thread.html', {'post' : baseSet},
        context_instance = RequestContext(request))

def exportToFile(request):
    if request.user.is_superuser is True:
#        User.email_user(request.user,'meccid - network info','test',from_email='boomslang143@gmail.com')
        users = UserProfile.objects.all()
        f = open('./nets/userToUser_tags.net', 'w')
        f.write("*Vertices  " + str(users.count()) +"\n")
        for user in users:
            f.write(str(user.user.id-1)+" \""+ str(user.user.username) +"\"" + " x_fact " + str(user.karma+1) + " y_fact " + str(user.karma+1) +"\n")
        utus = UserToUser.objects.all()
        f.write("*Edges  " + str(utus.count()) +"\n")
        for utu in utus:
    #        if utu.boundTag > 0:
                f.write(str(utu.user1.id-1)+" "+ str(utu.user2.id-1) +" " + str(utu.boundTag) +  "\n")
        f.close()

        f = open('./nets/userToUser_comments.net', 'w')
        f.write("*Vertices  " + str(users.count()) +"\n")
        for user in users:
            f.write(str(user.user.id-1)+" \""+ str(user.user.username) +"\"" + " x_fact " + str(user.karma+1) + " y_fact " + str(user.karma+1) +"\n")
        utus = UserToUser.objects.all()
        f.write("*Arcs  " + str(utus.count() * 2) +"\n")
        for utu in utus:
    #        if utu.boundPost1to2 > 0:
                f.write(str(utu.user1.id-1)+" "+ str(utu.user2.id-1) +" " + str(utu.boundPost1to2) +  "\n")
    #        if utu.boundPost2to1 > 0:
                f.write(str(utu.user2.id-1)+" "+ str(utu.user1.id-1) +" " + str(utu.boundPost2to1) +  "\n")
        f.close()

        f = open('./nets/userToUser_votes.net', 'w')
        f.write("*Vertices  " + str(users.count()) +"\n")
        for user in users:
            f.write(str(user.user.id-1)+" \""+ str(user.user.username) +"\"" + " x_fact " + str(user.karma+1) + " y_fact " + str(user.karma+1) +"\n")
        utus = UserToUser.objects.all()
        f.write("*Arcs  " + str(utus.count() * 2) +"\n")
        for utu in utus:
    #        if utu.boundVote1to2 > 0:
                f.write(str(utu.user1.id-1)+" "+ str(utu.user2.id-1) +" " + str(utu.boundVote1to2) +  "\n")
    #        if utu.boundVote2to1 > 0:
                f.write(str(utu.user2.id-1)+" "+ str(utu.user1.id-1) +" " + str(utu.boundVote2to1) +  "\n")
        f.close()

        tags = Tag.objects.all()
        f = open('./nets/tagToTag_bounds.net', 'w')
        f.write("*Vertices  " + str(tags.count()) +"\n")
        i = 1
        for tag in tags:
            f.write(str(i)+" \""+ str(tag.name) +"\"" + " x_fact " + str(1) + " y_fact " + str(1) +"\n")
            i+=1
        ttts = TagToTag.objects.all()
        f.write("*Edges  " + str(ttts.count()) +"\n")
        for ttt in ttts:
            ind1 = -1
            ind2 = -1
            for index, tag in enumerate(tags):
                if tag.mid == ttt.tag1.mid:
                    ind1 = index + 1
                elif tag.mid == ttt.tag2.mid:
                    ind2 = index + 1
            f.write(str(ind1)+" "+ str(ind2) +" " + str(ttt.bound) +  "\n")
        f.close()

        f = open('./nets/tagToTag_isSibling.net', 'w')
        f.write("*Vertices  " + str(tags.count()) +"\n")
        i = 1
        for tag in tags:
            f.write(str(i)+" \""+ str(tag.name) +"\"" + " x_fact " + str(1) + " y_fact " + str(1) +"\n")
            i+=1
        ttts = TagToTag.objects.all()
        f.write("*Edges  " + str(ttts.count()) +"\n")
        for ttt in ttts:
            ind1 = -1
            ind2 = -1
            for index, tag in enumerate(tags):
                if tag.mid == ttt.tag1.mid:
                    ind1 = index + 1
                elif tag.mid == ttt.tag2.mid:
                    ind2 = index + 1
            if ttt.isSibling is True:
                f.write(str(ind1)+" "+ str(ind2) +" " + str(1) +  "\n")
            else:
                f.write(str(ind1)+" "+ str(ind2) +" " + str(0) +  "\n")
        f.close()

        f = open('./nets/tagToTag_isInstance.net', 'w')
        f.write("*Vertices  " + str(tags.count()) +"\n")
        i = 1
        for tag in tags:
            f.write(str(i)+" \""+ str(tag.name) +"\"" + " x_fact " + str(1) + " y_fact " + str(1) +"\n")
            i+=1
        ttts = TagToTag.objects.all()
        f.write("*Edges  " + str(ttts.count()) +"\n")
        for ttt in ttts:
            ind1 = -1
            ind2 = -1
            for index, tag in enumerate(tags):
                if tag.mid == ttt.tag1.mid:
                    ind1 = index + 1
                elif tag.mid == ttt.tag2.mid:
                    ind2 = index + 1
            if ttt.isInstance == 1:
                f.write(str(ind1)+" "+ str(ind2) +" " + str(1) +  "\n")
            elif ttt.isInstance == 2:
                f.write(str(ind2)+" "+ str(ind1) +" " + str(1) +  "\n")
            else:
                f.write(str(ind1)+" "+ str(ind2) +" " + str(0) +  "\n")
        f.close()

    return HttpResponseRedirect("/main/date/all/")

def updateTagToTags(request):
    if request.user.is_superuser is True:
        tagList = Tag.objects.all()
        for i in range(len(tagList)):
            tag1i = tagList[i]
            for j in range(i+1,len(tagList)):
                tag2i =  tagList[j]

                ttt, created = TagToTag.objects.get_or_create(tag1 = tag1i, tag2 = tag2i)
                if ttt.tag1.notableForID == ttt.tag2.notableForID and ttt.tag1.notableForID != "NULL" and ttt.isSibling == False:
                    ttt.isSibling = True
                if tag1i.notableForName == tag2i.name:
                    ttt.isInstance = 1
                elif tag1i.name == tag2i.notableForName:
                    ttt.isInstance = 2
                ttt.title = tag1i.name+" - "+tag2i.name
                ttt.save()
    return HttpResponseRedirect("/main/date/all/")