# Copyright 2009 GORBET + BANERJEE (http://www.gorbetbanerjee.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import os
import os.path
import Image
import urllib
import datetime, calendar
import random
import time
import re
import feedparser
import unicodedata
import traceback
import logging
import pprint

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.files import File
from django.db import models
from django.db.models import signals
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.dispatch import dispatcher
from django.core.mail import send_mail
from django.utils.encoding import force_unicode
from django.db.models import Q
from django.db.models.fields.files import ImageFieldFile
from django.core.urlresolvers import reverse

from front.models import EventModel
from iboot_control import IBootControl

class IBootDevice(models.Model):
	name = models.CharField(max_length=1024, null=False, blank=False)
	mac_address = models.CharField(max_length=1024, null=False, blank=False, help_text="e.g. 00-0D-AD-01-94-6F")
	ip = models.IPAddressField(blank=False, null=True)
	@models.permalink
	def get_absolute_url(self): return ('iboot.views.iboot', (), { 'id':self.id })
	def __unicode__(self): return '%s' % self.name
	class Meta:
		ordering = ['name']
		verbose_name = 'iBoot Device'
		verbose_name_plural = 'iBoot Devices'
	class HydrationMeta:
		attributes = ['id', 'name', 'mac_address']

class IBootEvent(EventModel):
	COMMAND_CHOICES = (('cycle', 'Cycle'), ('on', 'Turn On'), ('off', 'Turn Off'), ('toggle', 'Toggle') )
	command = models.CharField(max_length=12, blank=False, null=False, choices=COMMAND_CHOICES, default='cycle')
	device = models.ForeignKey(IBootDevice, blank=False, null=False)

	def execute(self):
		try:
			control = IBootControl(settings.IBOOT_POWER_PASSWORD, self.device.ip)
			print 'running ', self
			if self.command == 'cycle':
				control.cycle_power()
			elif self.command == 'on':
				control.turn_on()
			elif self.command == 'off':
				control.turn_off()
			elif self.command == 'toggle':
				control.toggle()
			else:
				self.tries = self.tries + 1
				self.save()
				return False
			print 'ran command', self.command
		except:
			traceback.print_exc()
			self.tries = self.tries + 1
			self.save()
			return False
			
		self.last_run = datetime.datetime.now()
		self.tries = 1
		self.save()
		return True

	def __unicode__(self): return 'iBoot Event: [%s],[%s],[%s]' % (self.days, self.hours, self.minutes)

	class Meta:
		verbose_name = 'iBoot Event'
		verbose_name_plural = 'iBoot Events'
