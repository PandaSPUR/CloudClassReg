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
		return self.username.first_name + " " + self.username.last_name

class Semester(models.Model):
	season = models.CharField(max_length=256)
	year = models.CharField(max_length=4)
	start = models.CharField(max_length=10) #YYYY-MM-DD as per RFC 3339, always a Monday. Reason: figuring out which dates are mon/tues/etc for Google Calendar
	end = models.CharField(max_length=10) #YYYY-MM-DD as per RFC 3339, could be any day.
	def __unicode__(self):
		return self.season + " " + self.year

class Course(models.Model):
	code = models.CharField(max_length=10) #Ex: "CS-GY 1234""
	name = models.CharField(max_length=256)
	major = models.ForeignKey(Major)
	semester = models.ForeignKey(Semester)
	description = models.CharField(max_length=1024)
	professor = models.CharField(max_length=256)
	room = models.CharField(max_length=256)
	isOpen = models.BooleanField(default=False)
	capacity = models.IntegerField(default=0)
	credits = models.IntegerField(default=3)
	#Really crude way of picking a class's time slots...
	#If the class doesnt meet at that day, just write "0000-0000" for sake of uniformity
	monday = models.CharField(max_length=9, default="0000-0000") #Format: HHMM-HHMM
	tuesday = models.CharField(max_length=9, default="0000-0000") #Format: HHMM-HHMM
	wednesday = models.CharField(max_length=9, default="0000-0000") #Format: HHMM-HHMM
	thursday = models.CharField(max_length=9, default="0000-0000") #Format: HHMM-HHMM
	friday = models.CharField(max_length=9, default="0000-0000") #Format: HHMM-HHMM
	def __unicode__(self):
		return self.code
	def hasSpace(self):
		if not self.isOpen: #add this here so checking hasSpace is sufficient for enrollment and catalog display purposes
			return False
		if self.transcript_set.count() < self.capacity:
			return True
		else:
			return False
	#check if a student of s_id meets this course's requirements
	def meetsPrereqs(self, s_id):
		prereqs = CoursePrereq.objects.filter(course=self)
		studentPastCourses = Transcript.objects.filter(student__id=s_id)
		prereqsMet = True #default to true if there are no prereqs.
		for course in prereqs:
			prereqsMet = False
			for pastCourse in studentPastCourses:
				if pastCourse.course.code == course.prereq.code:
					if pastCourse.grade > 0: #can also change this to "if >=2" if a C minimum is required from prereqs
						prereqsMet = True
						continue #Found a matching completed prerequisite, skip on to the next required "course"
		return prereqsMet
	#check if a student of s_id is enrolled in a conflicting course.
	def hasConflict(self, s_id):
		otherCourses = Transcript.objects.filter(student__id=s_id).filter(course__semester=self.semester)
		for course in otherCourses:
			if self.monday != "0000-0000" and course.course.monday != "0000-0000":
				#if starting time is between start and end of other course:
				if int(course.course.monday[0:4]) <= int(self.monday[0:4]) < int(course.course.monday[5:]):
					return True;
				#if this class ends after other starts.
				if int(course.course.monday[0:4]) < int(self.monday[5:]):
					return True;
			if self.tuesday != "0000-0000" and course.course.tuesday != "0000-0000":
				#if starting time is between start and end of other course:
				if int(course.course.tuesday[0:4]) <= int(self.tuesday[0:4]) < int(course.course.tuesday[5:]):
					return True;
				#if this class ends after other starts.
				if int(course.course.tuesday[0:4]) < int(self.tuesday[5:]):
					return True;
			if self.wednesday != "0000-0000" and course.course.wednesday != "0000-0000":
				#if starting time is between start and end of other course:
				if int(course.course.wednesday[0:4]) <= int(self.wednesday[0:4]) < int(course.course.wednesday[5:]):
					return True;
				#if this class ends after other starts.
				if int(course.course.wednesday[0:4]) < int(self.wednesday[5:]):
					return True;
			if self.thursday != "0000-0000" and course.course.thursday != "0000-0000":
				#if starting time is between start and end of other course:
				if int(course.course.thursday[0:4]) <= int(self.thursday[0:4]) < int(course.course.thursday[5:]):
					return True;
				#if this class ends after other starts.
				if int(course.course.thursday[0:4]) < int(self.thursday[5:]):
					return True;
			if self.friday != "0000-0000" and course.course.friday != "0000-0000":
				#if starting time is between start and end of other course:
				if int(course.course.friday[0:4]) <= int(self.friday[0:4]) < int(course.course.friday[5:]):
					return True;
				#if this class ends after other starts.
				if int(course.course.friday[0:4]) < int(self.friday[5:]):
					return True;
		return False #default to false if there are no other courses student is currently enrolled in

class Transcript(models.Model):
	student = models.ForeignKey(Student)
	course = models.ForeignKey(Course)
	grade = models.IntegerField(default=0)
	def __unicode__(self):
		return self.student.username.first_name + " " + self.student.username.last_name

class CoursePrereq(models.Model):
	course = models.ForeignKey(Course)
	prereq = models.ForeignKey(Course, related_name="prereq")
	def __unicode__(self):
		return self.course.code + ": " + self.course.name

class Cart(models.Model):
	student = models.ForeignKey(Student)
	course = models.ForeignKey(Course)


'''Stuff for Google App Engine'''
class CredentialsModel(models.Model):
	id = models.ForeignKey(User, primary_key=True)
	credential = CredentialsField()
	def __unicode__(self):
		return self.id.first_name + " " + self.id.last_name + "'s GAE Credentials"

class FlowModel(models.Model):
	id = models.ForeignKey(User, primary_key=True)
	flow = FlowField()

class Calendar(models.Model):
	student = models.ForeignKey(Student)
	calendarID = models.CharField(max_length=256)
	def __unicode__(self):
		return self.student.username.first_name + " " + self.student.username.last_name + "'s Calendar"