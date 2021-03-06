# Copyright 2011 GORBET + BANERJEE (http://www.gorbetbanerjee.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import datetime
import calendar
import pprint
import traceback
import logging
import urllib
import sys

from django.conf import settings
from django.db.models import Q
from django.template import Context, loader
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
import django.contrib.contenttypes.models as content_type_models
from django.template import RequestContext
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.utils import feedgenerator

from models import *
from art_server.hydration import dehydrate_to_list_xml, dehydrate_to_xml
from incus.soundman_control import SoundManControl
from front.management.commands.send_alert import Command as SendAlertCommand

def emergency(request):
	try:
		if request.method == 'POST' and request.POST.get('code', None):
			try:
				code = int(request.POST.get('code'))
			except:
				return HttpResponse('Bad code', content_type="text/plain")

			if settings.AUDIO_EMERGENCY_CODE == code:
				control_error = False
				for group in ABChannelGroup.objects.all():
					for channel in group.channels.all():
						try:
							control = SoundManControl(channel.audioBoxDevice.ip, channel.audioBoxDevice.port)
							result = control.mute(channel.short_name)
							print 'muted', channel, result
						except:
							traceback.print_exc()
							control_error = True
				emergency_message = "Someone activated the emergency audio system."
				if control_error: emergency_message += " Also, there was an error communicating with the audio server."
				alert_command = SendAlertCommand()
				alert_command.handle("AUDIO EMERGENCY SYSTEM ACTIVATED", emergency_message)
				return HttpResponse('Activated', content_type="text/plain")
			else:
				return HttpResponse('Bad code', content_type="text/plain")
		return HttpResponse('This is the audio emergency API. Nothing happened.', content_type="text/plain")
	except:
		traceback.print_exc()

def ab_devices(request):
	return HttpResponse(dehydrate_to_list_xml([device.wrap() for device in ABDevice.objects.all()]), content_type="text/xml")

def ab_device(request, id):
	device = get_object_or_404(ABDevice, pk=id)
	return HttpResponse(dehydrate_to_xml(device.wrap()), content_type="text/xml")

def ab_group(request, id):
	group = get_object_or_404(ABChannelGroup, pk=id)
	return HttpResponse(dehydrate_to_xml(group.wrap()), content_type="text/xml")

def ab_group_gain(request, id):
	group = get_object_or_404(ABChannelGroup, pk=id)
	if request.method == 'POST' and request.POST.get('gain', None):
		print 'This is where we should communicate with the AB64 to set the master gain'
		group.master_gain = float(request.POST.get('gain'))
		group.save()
	return HttpResponse(group.master_gain, content_type="text/plain")

def ab_channel_mute(request, id):
	channel = get_object_or_404(ABChannel, pk=id)
	control = SoundManControl(channel.audioBoxDevice.ip, channel.audioBoxDevice.port)
	if request.method == 'POST' and request.POST.get('mute', None) == 'toggle':
		control.toggle_mute(channel.short_name)
	elif request.method == 'POST' and request.POST.get('mute', None) == 'on':
		control.mute(channel.short_name)
	elif request.method == 'POST' and request.POST.get('mute', None) == 'off':
		control.unmute(channel.short_name)
	return HttpResponse(control.get_mute(channel.short_name), content_type="text/plain")

def ab_channel_gain(request, id):
	channel = get_object_or_404(ABChannel, pk=id)
	if request.method == 'POST' and request.POST.get('gain', None):
		gain = float(request.POST.get('gain'))
		control = SoundManControl(channel.audioBoxDevice.ip, channel.audioBoxDevice.port)
		control.set_gain(channel.short_name, gain)
		channel.gain = gain
		channel.save()
	return HttpResponse(channel.gain, content_type="text/plain")
