from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
	#We'll use Django's automatically created primary key as the Student ID here.
	username = models.ForeignKey(User)
	major = models.CharField(max_length=256)

class Transcript(models.Model):
	student = models.ForeignKey(Student)
	course = models.ForeignKey(Course)
	grade = models.IntegerField(default=0)

class Course(models.Model):
	name = models.CharField(max_length=256)
	major = models.CharField(max_length=256)
	semester = models.CharField(max_length=256)
	description = models.CharField(max_length=1024)
	professor = models.CharField(max_length=256)
	isOpen = models.BooleanField(default=False)
	capacity = models.IntegerField(default=0)
	credits = models.IntegerField(default=3)