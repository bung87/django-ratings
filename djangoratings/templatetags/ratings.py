"""
Template tags for Django
"""
# TODO: add in Jinja tags if Coffin is available

from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import ObjectDoesNotExist
import django
from djangoratings.models import Vote

register = template.Library()
# template.resolve_variable Deprecated in Django 1.8, will be removed in Django 1.10.
def resolve_variable(path,context):
    if django.VERSION[:2] < (1, 10):
        return template.resolve_variable(path,context)
    else:
        return template.Variable(path).resolve(context)

class RatingByRequestNode(template.Node):
    def __init__(self, request, obj, context_var):
        self.request = request
        self.obj, self.field_name = obj.split('.')
        self.context_var = context_var
    
    def render(self, context):
        try:
            request = resolve_variable(self.request, context)
            obj = resolve_variable(self.obj, context)
            field = getattr(obj, self.field_name)
        except (template.VariableDoesNotExist, AttributeError):
            return ''
        try:
            ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META['REMOTE_ADDR']
            if len(ip.split(",")) > 1:
                ip = ip.split(",")[0]
            vote = field.get_rating_for_user(request.user, ip, request.COOKIES)
            context[self.context_var] = vote
        except ObjectDoesNotExist:
            context[self.context_var] = 0
        return ''

def do_rating_by_request(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    stores it in a context variable. If the user has not voted, the
    context variable will be 0.
    
    Example usage::
    
        {% rating_by_request request on instance as vote %}
    """
    
    bits = token.contents.split()
    if len(bits) != 6:
        raise template.TemplateSyntaxError("'%s' tag takes exactly five arguments" % bits[0])
    if bits[2] != 'on':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'on'" % bits[0])
    if bits[4] != 'as':
        raise template.TemplateSyntaxError("fourth argument to '%s' tag must be 'as'" % bits[0])
    return RatingByRequestNode(bits[1], bits[3], bits[5])
register.tag('rating_by_request', do_rating_by_request)

class RatingByUserNode(RatingByRequestNode):
    def render(self, context):
        try:
            user = resolve_variable(self.request, context)
            obj = resolve_variable(self.obj, context)
            field = getattr(obj, self.field_name)
        except template.VariableDoesNotExist:
            return ''
        try:
            vote = field.get_rating_for_user(user)
            context[self.context_var] = vote
        except ObjectDoesNotExist:
            context[self.context_var] = 0
        return ''

def do_rating_by_user(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    stores it in a context variable. If the user has not voted, the
    context variable will be 0.
    
    Example usage::
    
        {% rating_by_user user on instance as vote %}
    """
    
    bits = token.contents.split()
    if len(bits) != 6:
        raise template.TemplateSyntaxError("'%s' tag takes exactly five arguments" % bits[0])
    if bits[2] != 'on':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'on'" % bits[0])
    if bits[4] != 'as':
        raise template.TemplateSyntaxError("fourth argument to '%s' tag must be 'as'" % bits[0])
    return RatingByUserNode(bits[1], bits[3], bits[5])
register.tag('rating_by_user', do_rating_by_user)
