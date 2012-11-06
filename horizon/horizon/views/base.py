# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django import shortcuts
from django.views import generic
from django.views.decorators import vary
from django.http import HttpResponse
from django.utils import simplejson
from ThRedisClient import *
import string, time, datetime


from openstack_auth.views import Login

import horizon
from horizon import exceptions


def user_home(request):
    """ Reversible named view to direct a user to the appropriate homepage. """
    return shortcuts.redirect(horizon.get_user_home(request.user))


def get_user_home(user):
    if user.is_superuser:
        return horizon.get_dashboard('syspanel').get_absolute_url()
    return horizon.get_dashboard('nova').get_absolute_url()


@vary.vary_on_cookie
def splash(request):
    if request.user.is_authenticated():
        return shortcuts.redirect(get_user_home(request.user))
    form = Login(request)
    request.session.clear()
    request.session.set_test_cookie()
    return shortcuts.render(request, 'splash.html', {'form': form})

def get_md(request):
    result = {}
    rediscli = ThRedisClient('localhost')
    qin = request.GET['query'].split(',')
    tstart = request.GET['stime']
    
    if tstart == 'latest':
	for id in qin:
		temp = {}
		iinfo = rediscli.get1byinstance(id, -1).split('$')
		temp['cpu'] = iinfo[0]+"%"
		temp['mem'] = round((string.atof(iinfo[2])-string.atof(iinfo[1]))/string.atof(iinfo[2])*100, 2)
		temp['netin'] = string.atoi(iinfo[3].split(':')[1])/1024/1024
		temp['netout'] = string.atoi(iinfo[4].split(':')[1])/1024/1024
		temp['timestamp'] = time.localtime(string.atoi(iinfo[-1]))[0]
		result[id] = temp
    else:
	for id in qin:
		result[id] = []
		iinfos = rediscli.getrangebyinstance(id, -100, -1)
		#iinfos = rediscli.getallbyinstance(id)
		amcharts_item = {}
		for s in iinfos:
			schips = s.split('$')
			date_obj =str( datetime.datetime.fromtimestamp(string.atoi(schips[-1])))
			cpu = schips[0]
			amcharts_item = {'date':date_obj, 'value':string.atof(cpu)}
			result[id].append(amcharts_item)

    return HttpResponse(simplejson.dumps(result))


class APIView(generic.TemplateView):
    """ A quick class-based view for putting API data into a template.

    Subclasses must define one method, ``get_data``, and a template name
    via the ``template_name`` attribute on the class.

    Errors within the ``get_data`` function are automatically caught by
    the :func:`horizon.exceptions.handle` error handler if not otherwise
    caught.
    """
    def get_data(self, request, context, *args, **kwargs):
        """
        This method should handle any necessary API calls, update the
        context object, and return the context object at the end.
        """
        raise NotImplementedError("You must define a get_data method "
                                   "on %s" % self.__class__.__name__)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            context = self.get_data(request, context, *args, **kwargs)
        except:
            exceptions.handle(request)
        return self.render_to_response(context)
