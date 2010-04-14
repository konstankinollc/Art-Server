# Copyright 2009 GORBET + BANERJEE (http://www.gorbetbanerjee.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import datetime
import sys
import calendar
import pprint
import traceback

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

from bacnet_control import BacnetControl

from models import *
from forms import *

@staff_member_required
def index(request):
	return render_to_response('lighting/index.html', { 'bacnet_lights':BACNetLight.objects.all(), 'projectors':Projector.objects.all() }, context_instance=RequestContext(request))

@staff_member_required
def bacnet_light(request, id):
	light = get_object_or_404(BACNetLight, pk=id)
	control = BacnetControl(settings.BACNET_BIN_DIR)
	if request.method == 'POST':
		light_control_form = LightControlForm(request.POST)
		if light_control_form.is_valid():
			new_value = light_control_form.cleaned_data['light_value']
			try:
				control.write_analog_output_int(light.device_id, light.property_id, int(new_value))
			except:
				logging.exception('Could not write the posted value (%s) for bacnet device %s property %s' % (new_value, light.device_id, light.property_id))
				return HttpResponseServerError('Could not write the posted value (%s) for bacnet device %s property %s\n\n%s' % (new_value, light.device_id, light.property_id, sys.exc_info()[1]))
	try:
		read_result = control.read_analog_output(light.device_id, light.property_id)
		light_value = float(clean_rp_result(read_result))
		light_control_form = LightControlForm(data={'light_value':light_value})
	except:
		logging.exception('Could not read the analog output for bacnet device %s property %s' % (light.device_id, light.property_id))
		light_value = None
		light_control_form = LightControlForm()
	return render_to_response('lighting/bacnet_light.html', {'light_value':light_value, 'light_control_form':light_control_form, 'light':light }, context_instance=RequestContext(request))

@staff_member_required
def projector(request, id):
	projector = get_object_or_404(Projector, pk=id)
	return render_to_response('lighting/projector.html', { 'projector':projector }, context_instance=RequestContext(request))
