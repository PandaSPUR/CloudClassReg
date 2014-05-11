from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from registration.models import *
from django.contrib.auth.models import User

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

def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/reg/')