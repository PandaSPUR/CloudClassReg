from django.db import models
from django.contrib.auth.models import User

from oauth2client.django_orm import FlowField, CredentialsField

class Major(models.Model):
	major = models.CharField(max_length=256)
	def __unicode__(self):
		return self.major

class Student(models.Model):
	#We'll use Django's automatically created primary key as the Student ID here.
	username = models.ForeignKey(User)
	major = models.ForeignKey(Major)
	def __unicode__(self):
		name = self.username.first_name + " " + self.username.last_name
		return name

class Semester(models.Model):
	season = models.CharField(max_length=256)
	year = models.CharField(max_length=4)
	start = models.CharField(max_length=10) #YYYY-MM-DD as per RFC 3339, always a Monday. Reason: figuring out which dates are mon/tues/etc for Google Calendar
	end = models.CharField(max_length=10) #YYYY-MM-DD as per RFC 3339, could be any day.

class Course(models.Model):
	code = models.CharField(max_length=10) #Ex: "CS-GY 1234""
	name = models.CharField(max_length=256)
	major = models.ForeignKey(Major)
	#semester = models.CharField(max_length=256)
	semester = models.ForeignKey(Semester)
	description = models.CharField(max_length=1024)
	professor = models.CharField(max_length=256)
	isOpen = models.BooleanField(default=False)
	capacity = models.IntegerField(default=0)
	credits = models.IntegerField(default=3)
	#Really crude way of picking a class's time slots...
	#If the class doesnt meet at that day, just write "0000-0000" for sake of uniformity
	monday = models.CharField(max_length=9) #Format: HHMM-HHMM
	tuesday = models.CharField(max_length=9) #Format: HHMM-HHMM
	wednesday = models.CharField(max_length=9) #Format: HHMM-HHMM
	thursday = models.CharField(max_length=9) #Format: HHMM-HHMM
	friday = models.CharField(max_length=9) #Format: HHMM-HHMM
	def __unicode__(self):
		return self.code
	def hasSpace(self):
		if self.transcript_set.count() < self.capacity:
			return True
		else:
			return False

class Transcript(models.Model):
	student = models.ForeignKey(Student)
	course = models.ForeignKey(Course)
	grade = models.IntegerField(default=0)

class CoursePrereq(models.Model):
	course = models.ForeignKey(Course)
	prereq = models.CharField(max_length=10)

class Cart(models.Model):
	student = models.ForeignKey(Student)
	course = models.ForeignKey(Course)
	def __unicode__(self):
		return self.course.name


'''Stuff for Google App Engine'''
class CredentialsModel(models.Model):
	id = models.ForeignKey(User, primary_key=True)
	credential = CredentialsField()

class FlowModel(models.Model):
	id = models.ForeignKey(User, primary_key=True)
	flow = FlowField()

class Calendar(models.Model):
	student = models.ForeignKey(Student)
	calendarID = models.CharField(max_length=256)