from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import HttpResponse, Http404, HttpResponseForbidden
from rideshare.forms import RegistrationForm
from rideshare.models import User, AuthToken, Ride, Location, State
from django.db.models import Q
from django.forms.models import model_to_dict
from django.utils.timezone import utc
import json
import datetime

def home(request):
   return render(request,'index.html')

@login_required
def all_rides(request):
    rides = []
    for ride in Ride.objects.all():
        rides.append(model_to_dict(ride))
    return HttpResponse(json.dumps(rides), content_type='application/json')

@login_required
def my_rides(request):
    rides = []
    for ride in Ride.objects.filter(Q(driver=request.user) | Q(passengers__in=[request.user]) | Q(owner=request.user)):
        rides.append(model_to_dict(ride))
    return HttpResponse(json.dumps(rides), content_type='application/json')

@login_required
@require_POST
def remove_from_ride(request, rId):
    ride = Ride.objects.get(id=rId)
    if ride.driver == request.user:
        ride.driver = None
    else:
       try:
           passenger = ride.passengers.get(id=request.user.id)
           ride.passengers.remove(passenger)
       except: 
           pass
    ride.save()
    return HttpResponse(json.dumps(ride), content_type='application/json')

def cmp(city, to_wes, time):
   def compare_rides(r):
       i = 0
       if to_wes and r.start.city == city:   i += 10000
       if not to_wes and r.end.city == city: i += 10000 
       i -= abs(r.leave_time_start - time).seconds / 1800
       return -i
   return compare_rides
    

def search(request):
    driver = request.GET.get('driver',False)
    time = datetime.datetime.strptime(request.GET.get('time'), '%Y-%m-%d %H:%M').replace(tzinfo=utc)
    state = request.GET.get('state')
    city = request.GET.get('city')
    to_wes = request.GET.get('to_wes')
    
    if driver: query = Ride.objects.filter(driver__isnull=True)
    else: query = Ride.objects.filter(driver__isnull=False)
    
    if to_wes: query = query.filter(start__state__name=state)
    else: query = query.filter(end__state__name=state)
    
    query = sorted(query,key=cmp(city,to_wes,time))
    rides = []
    for ride in query:
        rideDict = model_to_dict(ride)
        rideDict['leave_time_start'] = rideDict['leave_time_start'].strftime('%m/%d at %H:%M')
        rideDict['leave_time_end'] = rideDict['leave_time_end'].strftime('%m/%d at %H:%M')
        rides.append(rideDict)
    return HttpResponse(json.dumps(rides), content_type='application/json')

@login_required
@require_POST
def add_to_ride(request, rId):
    if not request.user.verified: return HttpResponse("{ 'response': 'You must verify your account to join a ride.' }", content_type='application/json')
    ride = Ride.objects.get(id=rId)
    if request.POST.get('driver',False) and not ride.driver:
        ride.driver = request.user
        ride.max_passengers = request.POST.get('max_passengers',1)
    elif not request.POST.get('driver',False) and ride.passengers.count() < ride.max_passengers:
        ride.passengers.add(request.user)
    ride.save()
    rd = model_to_dict(ride)
    rd['leave_time_start'] = str(rd['leave_time_start'])
    rd['leave_time_end'] = str(rd['leave_time_end'])
    return HttpResponse(json.dumps(rd),content_type='application/json')

@login_required
@require_POST
def create_ride(request):
    if not request.user.verified: return HttpResponse("{ 'response': 'You must verify your account to create a ride.' }", content_type='application/json')
    start = Location.objects.create(state=State.objects.get(name=request.POST['start_state']),city=request.POST['start_city'],address=request.POST['start_address'])
    end = Location.objects.create(state=State.objects.get(name=request.POST['end_state']),city=request.POST['end_city'],address=request.POST['end_address'])
    ride = Ride.objects.create(owner=request.user,start=start,end=end,leave_time_start=request.POST['leave_time_start'],leave_time_end=request.POST['leave_time_end'])
    ride.save()
    if request.POST.get('driver',False):
       ride.driver = request.user
       ride.max_passengers = request.POST.get('max_passengers',1)
    else:
       ride.passengers.add(request.user)
    ride.save()
    rd = model_to_dict(ride)
    rd['leave_time_start'] = str(rd['leave_time_start'])
    rd['leave_time_end'] = str(rd['leave_time_end'])
    return HttpResponse(json.dumps(rd),content_type='application/json')

def authenticate(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    # Get user with given username/password combination
    user = auth.authenticate(username=username, password=password)
    if user is not None:
        # Log in user if active
        if user.is_active:
            auth.login(request, user)
            return HttpResponse("{ 'response': 'ok' }",content_type='application/json')
    return HttpResponse("{'response':'Username/password incorrect'}",content_type='application/json')

@login_required
def logout(request):
    auth.logout(request)
    return HttpResponse("{'response':'ok'}",content_type='application/json')

def user_info(request):
    if request.user.is_authenticated():
        return HttpResponse(json.dumps(request.user.to_dict()), content_type='application/json')
    return HttpResponse("{'response': 'Not logged in.'}",content_type='application/json')

@login_required
def get_info_user(request, uId):
    return HttpResponse(json.dumps(model_to_dict(User.objects.get(id=uId))),content_type='application/json')

def get_location(request, lId):
    l = model_to_dict(Location.objects.get(id=lId))
    l['state'] = State.objects.get(id=l['state']).name
    return HttpResponse(json.dumps(l),content_type='application/json')

@require_POST
def forgot_password(request):
    try:
        user = User.objects.get(email=request.POST.get('email'))
    except ObjectDoesNotExist:
        return HttpResponse("{ 'response': 'Email address is not associated with an account.' }",content_type='application/json')
    new_token = user.generate_token()
    subject="Account Recovery"
    html_content = ("<div>\r\n"
                    "  <div style='color: #0096C9; background: #FFFFFF; font-size: 3em; padding: 10px;'>Ride@Wes</div>\r\n"
                    "    <div style='background: #0096C9; color: #FFFFFF; font-size: 2em; padding: 10px;'>Account Recovery"
                    "    </div>                               "
                    "</div>\r\n"
                    "<div style='background: #FFFFFF; margin: 30px 60px; padding: 10px;'>\r\n"
                    "  <div style='color: #A5A5A5; font-size: 1.5em;'>To recover your account please follow the link below. If you did not request account recovery you can safely ignore this message.</div>\r\n"
                    "</div>\r\n"
                    "<div style='background: #888888; width: 200px; margin-left: auto; margin-right: auto; color: #FFFFFF; text-align: center; font-size: 3em;          padding: 3px; margin-top: 20px;'>\r\n"
                    "  <a href='http://rideatwes.weshack.com/recover/"+ new_token.auth_code+"' style='text-decoration: none; color: inherit;'>Recover</a>\r\n"
                    "</div>\r\n")
    html_message = ("<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>\r\n"
             "<html xmlns='http://www.w3.org/1999/xhtml'>\r\n"
             "<head>\r\n"
             "<meta http-equiv='Content-Type' content='text/html; charset=UTF-8' />\r\n"
             "<link href='http://fonts.googleapis.com/css?family=Raleway' rel='stylesheet' type='text/css'>\r\n"
             "</head>\r\n"
             "<body style='background: #ECF0F1; font-size: 12px;'>\r\n"
             "<div style='width: 60%; min-width: 400px; max-width: 800px; margin-left: auto; margin-right: auto; color: gray; margin-top: 40px;'>\r\n")
    html_message += html_content + "</div>\r\n</body>\r\n</html>\r\n"
    message="To recover your account please follow the link to http://rideatwes.weshack.com/recover/" + new_token.auth_code
    message+="\nIf you did not request account recovery you can safely ignore this message."
    message+="\nThanks,"+"\n"+"The Ride@Wes Team."
    from_email, to = 'no-reply@joomah.com', request.POST.get('email')
    msg = EmailMultiAlternatives(subject, message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    msg.send()
    return HttpResponse("{ 'response': 'ok' }",content_type='application/json')

@require_POST
def recover(request, key):
    try:
        ja = AuthToken.objects.get(auth_code=key)
    except ObjectDoesNotExist:
        raise Http404
    pwd = request.POST.get('password')
    pwd1 = request.POST.get('password1')
    if not pwd or len(pwd) < 8: return HttpResponse("{'response': 'Password must be at least 8 characters.' }",content_type='application/json')
    if not pwd1 or pwd != pwd1: return HttpResponse("{'response': 'Passwords do not match.' }",content_type='application/json')
    ja.verified = True # if they got this email we know their email address is correct
    ja.user.set_password(pwd)
    ja.user.backend = 'django.contrib.auth.backends.ModelBackend'
    ja.user.save()
    auth.login(request, ja.user)
    ja.delete()
    return HttpResponse("{ 'response': 'ok' }", content_type='application/json')

def verify(request, key):
    try:
        ja = AuthToken.objects.get(auth_code=key)
    except ObjectDoesNotExist:
        raise Http404
    ja.user.verified = True
    ja.user.backend = 'django.contrib.auth.backends.ModelBackend'
    ja.user.save()
    auth.login(request, ja.user)
    ja.delete()
    return HttpResponse("{ 'response': 'ok' }",content_type='application/json')

def get_comments(request,rId):
    return HttpResponse(json.dumps(Comment.objects.filter(ride__id=rId)),content_type='application/json')

@login_required
@require_POST
def add_comment(request,rId):
    ride = Ride.objects.get(rId)
    if len(ride.passengers.filter(id=request.user.id)) == 0 and ride.driver != request.user: return HttpResponse("{ 'response': 'You must belong to a ride to post comments.' }", content_type='application/json')
    Comment(ride=Ride.objects.get(rId),author=request.user,body=request.POST['body']).save()
    return HttpResponse("{'response': 'ok'}",content_type='application/json')

@require_POST
def create_user(request):
    form = RegistrationForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponse("{'response':'ok'}",content_type='application/json')
    vars = {}
    vars['response'] = form.errors
    return HttpResponse(json.dumps(vars),content_type='application/json')

@require_POST
@login_required
def modify_user(request):
    if request.POST.get('phone_number',False):
        request.user.phone_number = request.POST['phone_number']
    if request.POST.get('class_year',False):
        request.user.class_year = request.POST['class_year']
    if request.POST.get('name',False):
        request.user.name = request.POST['name']
    request.user.save()
    return HttpResponse(json.dumps(request.user),content_type='application/json')
