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
'''for local testing
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets-local.json')

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri='http://localhost:8000/reg/oauth2callback')
'''
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets-aws.json')

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri='http://CloudClassReg-env-4xhwra3wte.elasticbeanstalk.com/reg/oauth2callback')
'''end for Google App Engine'''

# Create your views here.
@login_required
def index(request):
	storage = Storage(CredentialsModel, 'id', request.user, 'credential')
	credential = storage.get()
	if credential is None or credential.invalid == True:
		FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user)
		authorize_url = FLOW.step1_get_authorize_url()
		return HttpResponseRedirect(authorize_url)
	return render(request, 'registration/index.html')

@login_required
def catalog(request):
	majors_list = Major.objects.all()
	semesters_list = Semester.objects.all()
	if request.method == 'POST':
		courses_list = Course.objects.filter(major=request.POST['chosenMajor']).filter(semester=request.POST['chosenSemester'])
		return render(request, "registration/catalog.html", {'majors_list': majors_list, 'semesters_list': semesters_list, 'courses_list': courses_list})
	else:
		return render(request, "registration/catalog.html", {'majors_list': majors_list, 'semesters_list': semesters_list, 'firstload': True})

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
def empty_cart(request):
	currentStudent = Student.objects.get(username__username=request.user.username)
	cart_list = Cart.objects.filter(student=currentStudent)
	for item in cart_list:
		item.delete()
	return HttpResponseRedirect("/reg/cart/")

@login_required
def remove_cart_item(request):
	if request.GET:
		currentStudent = Student.objects.get(username__username=request.user.username)
		item = Cart.objects.filter(student=currentStudent).get(course__code=request.GET['code'])
		item.delete()
	return HttpResponseRedirect("/reg/cart/")

@login_required
def enroll(request):
	currentStudent = Student.objects.get(username__username=request.user.username)
	cart_list = Cart.objects.filter(student=currentStudent)
	enrollResults = {}

	'''Initialize some credentials for Google App Engine, for adding new classes to calendar'''
	storage = Storage(CredentialsModel, 'id', request.user, 'credential')
	credential = storage.get()
	http = httplib2.Http()
	http = credential.authorize(http)
	service = build("calendar", "v3", http=http)
	calendar_id = Calendar.objects.get(student=currentStudent).calendarID

	for item in cart_list:
		currentCourse = Course.objects.get(id=item.course.id)
		created = False

		#check a few conditions before completing enrollment.
		if not currentCourse.hasSpace:
			enrollResults[currentCourse.code] = "Class is closed."
			continue
		if not currentCourse.meetsPrereqs(currentStudent.id):
			enrollResults[currentCourse.code] = "Prerequisite courses not completed."
			continue
		if Transcript.objects.filter(student__id=currentStudent.id).filter(course__id=currentCourse.id).count() != 0:
			enrollResults[currentCourse.code] = "Already enrolled."
			continue
		if currentCourse.hasConflict(currentStudent.id):
			enrollResults[currentCourse.code] = "Conflicts with another enrolled class."
			continue

		#try to add the course to student's transcript.
		obj, created = Transcript.objects.get_or_create(student=currentStudent, course=currentCourse)
		if created:
			enrollResults[currentCourse.code] = "Enrollment Successful"
			item.delete() #Successfully enrolled, so remove from cart.

			'''BUILDING EVENT ENTRY FOR GOOGLE CALENDAR'''
			event = {}
			event["summary"] = currentCourse.code
			event["location"] = currentCourse.room
			event["recurrence"] = []
			event["recurrence"].append("RRULE:FREQ=WEEKLY;UNTIL=" + currentCourse.semester.end[0:4] + currentCourse.semester.end[5:7] + currentCourse.semester.end[8:10] + "T000000Z")

			event["start"] = {}
			event["end"] = {}
			if currentCourse.monday != "0000-0000":
				event["start"]["dateTime"] = (currentCourse.semester.start + "T" + 
					currentCourse.monday[0:2] + ":" + currentCourse.monday[2:4] + ":00.000")
				event["start"]["timeZone"] = "America/New_York"
				event["end"]["dateTime"] = (currentCourse.semester.start + "T" + 
					currentCourse.monday[5:7] + ":" + currentCourse.monday[7:9] + ":00.000")
				event["end"]["timeZone"] = "America/New_York"
				service.events().insert(calendarId=calendar_id, body=event).execute()
			if currentCourse.tuesday != "0000-0000":
				startDate = currentCourse.semester.start[0:8] + str(int(currentCourse.semester.start[8:]) + 1)
				event["start"]["dateTime"] = (startDate + "T" + 
					currentCourse.tuesday[0:2] + ":" + currentCourse.tuesday[2:4] + ":00.000")
				event["start"]["timeZone"] = "America/New_York"
				event["end"]["dateTime"] = (startDate + "T" + 
					currentCourse.tuesday[5:7] + ":" + currentCourse.tuesday[7:9] + ":00.000")
				event["end"]["timeZone"] = "America/New_York"
				service.events().insert(calendarId=calendar_id, body=event).execute()
			if currentCourse.wednesday != "0000-0000":
				startDate = currentCourse.semester.start[0:8] + str(int(currentCourse.semester.start[8:]) + 2)
				event["start"]["dateTime"] = (startDate + "T" + 
					currentCourse.wednesday[0:2] + ":" + currentCourse.wednesday[2:4] + ":00.000")
				event["start"]["timeZone"] = "America/New_York"
				event["end"]["dateTime"] = (startDate + "T" + 
					currentCourse.wednesday[5:7] + ":" + currentCourse.wednesday[7:9] + ":00.000")
				event["end"]["timeZone"] = "America/New_York"
				service.events().insert(calendarId=calendar_id, body=event).execute()
			if currentCourse.thursday != "0000-0000":
				startDate = currentCourse.semester.start[0:8] + str(int(currentCourse.semester.start[8:]) + 3)
				event["start"]["dateTime"] = (startDate + "T" + 
					currentCourse.thursday[0:2] + ":" + currentCourse.thursday[2:4] + ":00.000")
				event["start"]["timeZone"] = "America/New_York"
				event["end"]["dateTime"] = (startDate + "T" + 
					currentCourse.thursday[5:7] + ":" + currentCourse.thursday[7:9] + ":00.000")
				event["end"]["timeZone"] = "America/New_York"
				service.events().insert(calendarId=calendar_id, body=event).execute()
			if currentCourse.friday != "0000-0000":
				startDate = currentCourse.semester.start[0:8] + str(int(currentCourse.semester.start[8:]) + 4)
				event["start"]["dateTime"] = (startDate + "T" + 
					currentCourse.friday[0:2] + ":" + currentCourse.friday[2:4] + ":00.000")
				event["start"]["timeZone"] = "America/New_York"
				event["end"]["dateTime"] = (startDate + "T" + 
					currentCourse.friday[5:7] + ":" + currentCourse.friday[7:9] + ":00.000")
				event["end"]["timeZone"] = "America/New_York"
				service.events().insert(calendarId=calendar_id, body=event).execute()
		else:
			enrollResults[currentCourse.code] = "Enrollment Unsuccessful"

	return render(request, "registration/enroll.html", {'results': enrollResults})

@login_required
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
	return HttpResponseRedirect("/reg")

@login_required
def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/reg/')