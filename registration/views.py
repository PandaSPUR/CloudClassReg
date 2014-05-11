from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from CloudClassReg import settings
from registration.models import *
from django.contrib.auth.models import User

'''for Google App Engine'''
import os
import logging
import httplib2
from apiclient.discovery import build
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri='http://localhost:8000/reg/oauth2callback')
'''end for Google App Engine'''

# Create your views here.
@login_required
def index(request):
	return render(request, 'registration/index.html')

@login_required
def catalog(request):
	majors_list = Major.objects.all()
	if request.method == 'POST':
		courses_list = Course.objects.filter(major=request.POST['chosenMajor'])
		return render(request, "registration/catalog.html", {'majors_list': majors_list, 'courses_list': courses_list})
	else:
		return render(request, "registration/catalog.html", {'majors_list': majors_list, 'firstload': True})

@login_required
def cart(request):
	currentStudent = Student.objects.get(username__username=request.user.username)

	if request.GET: #request.GET is a dictionary, check if it exists (i.e. if anythings being passed)
		chosenCourseObj = Course.objects.get(id=request.GET['chosenCourse'])
		#Need to check if student is already enrolled
		Cart.objects.get_or_create(student=currentStudent, course=chosenCourseObj)

	cart_list = Cart.objects.filter(student=currentStudent)
	return render(request, "registration/cart.html", {'cart_list': cart_list})

@login_required
def enroll(request):
	currentStudent = Student.objects.get(username__username=request.user.username)
	cart_list = Cart.objects.filter(student=currentStudent)
	enrollResults = {}

	for item in cart_list:
		currentCourse = Course.objects.get(id=item.course.id)
		created = False
		if currentCourse.hasSpace:
			obj, created = Transcript.objects.get_or_create(student=currentStudent, course=currentCourse)
		if created:
			enrollResults[currentCourse.code] = "Enrollment Successful"
		else:
			enrollResults[currentCourse.code] = "Enrollment Unsuccessful"
	return render(request, "registration/enroll.html", {'results': enrollResults})

@login_required
def schedexample(request):
	storage = Storage(CredentialsModel, 'id', request.user, 'credential')
	credential = storage.get()
	if credential is None or credential.invalid == True:
		FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user)
		authorize_url = FLOW.step1_get_authorize_url()
		return HttpResponseRedirect(authorize_url)
	else:
		http = httplib2.Http()
		http = credential.authorize(http)
		service = build("calendar", "v3", http=http)
		calendar_list = service.calendarList().list().execute()

		return render(request, "registration/sched.html", {'calendar_list': calendar_list})

def sched(request):
	storage = Storage(CredentialsModel, 'id', request.user, 'credential')
	credential = storage.get()
	if credential is None or credential.invalid == True:
		FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user)
		authorize_url = FLOW.step1_get_authorize_url()
		return HttpResponseRedirect(authorize_url)
	else:
		http = httplib2.Http()
		http = credential.authorize(http)
		service = build("calendar", "v3", http=http)

		currentStudent = Student.objects.get(username__username=request.user.username)

		try: 
			calendar_id = Calendar.objects.get(student=currentStudent).calendarID
		except:
			new_calendar = service.calendars().insert(body={'summary': 'CCProject', 'timeZone': 'America/New_York'}).execute()
			calendar_id = new_calendar['id']
			Calendar.objects.create(student=currentStudent, calendarID=calendar_id)
		return render(request, "registration/sched.html", {'calendar_id': calendar_id})

@login_required
def auth_return(request):
	if not xsrfutil.validate_token(settings.SECRET_KEY, request.REQUEST['state'], request.user):
		return  HttpResponseBadRequest()
	credential = FLOW.step2_exchange(request.REQUEST)
	storage = Storage(CredentialsModel, 'id', request.user, 'credential')
	storage.put(credential)
	return HttpResponseRedirect("/reg/sched")

def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/reg/')