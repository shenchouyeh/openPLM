import re

from django import template
from django.contrib.auth.models import User
from django.template import Node, resolve_variable
from openPLM.plmapp.controllers.user import UserController
from openPLM.plmapp import models


register = template.Library()

# from http://djangosnippets.org/snippets/1471/
@register.filter
def trunc(string, number, dots='...'):
    """ 
    Truncate the *string* to *number* characters
    and print *dots* on the end if truncated

    :usage: ``"isome text to be truncated"|trunc:6``
    :results: some te...
    """
    if not isinstance(string, basestring): 
        string = unicode(string)
    if len(string) <= number:
        return string
    return string[:number]+dots

@register.filter
def can_add(child, arg):
    parent, action = arg

    if isinstance(child, models.DocumentFile):
        child = child.document
    if action == "attach_doc":
        return parent.can_attach_document(child)
    elif action == "attach_part":
        return parent.can_attach_part(child)
    elif action == "add_child":
        return parent.can_add_child(child)
    elif action == "delegate":
        return isinstance(child, (User, UserController))
 
    return False

@register.filter
def button(css_class, options=""):
    classes = set([css_class, " ui-button", 
            "ui-button-text-only", "ui-widget", "ui-state-default",
            "ui-corner-all"])
    options = options.split(",")
    for opt in options:
        opt = opt.strip()
        if opt:
            if opt.startswith("icon"):
                classes.remove("ui-button-text-only")
            if opt.startswith("corner"):
                classes.remove("ui-corner-all")
            classes.add("ui-" + opt)
    return " ".join(classes)

def key(d, key_name):
    try:
        value = d[key_name]
    except KeyError:
        from django.conf import settings
        value = settings.TEMPLATE_STRING_IF_INVALID
    return value
key = register.filter('key', key)

def indice(l, index):
    return l[index]

indice = register.filter('indice', indice)

def attr(o, attr_name):
    from django.conf import settings
    return getattr(o, attr_name, settings.TEMPLATE_STRING_IF_INVALID)
attr = register.filter('attr', attr)

@register.filter
def is_plmobject(result):
    """
    Returns True if the object behind *result* is an instance of :class:`.PLMObject`
    """
    return issubclass(result.model, models.PLMObject)

@register.filter
def is_documentfile(result):
    """
    Returns True if the object behind *result* is an instance of :class:`.DocumentFile`
    """
    return issubclass(result.model, models.DocumentFile)

@models._cache_lifecycle_stuff
def get_state_class(plmobject):
    """
    Returns the state class ("cancelled", "draft", "proposed", "official",
    or "deprecated") of *plmobject*.
    """
    state, lifecycle = (plmobject.state_id, plmobject.lifecycle_id)
    if lifecycle == models.get_cancelled_lifecycle().name:
        return "cancelled"
    lc = models.Lifecycle.objects.get(name=lifecycle)
    if state == lc.official_state_id:
        return "official"
    if state == lc.first_state.name:
        return "draft"
    if state == lc.last_state.name:
        return "deprecated"
    return "proposed"

@register.filter
def result_class(result):
    """
    Returns a css class according to result.
    """
    if issubclass(result.model, (models.PLMObject, models.DocumentFile)):
        result.state_id = result.state
        result.lifecycle_id = result.lifecycle
        if result.state_id and result.lifecycle_id:
            return "state-" + get_state_class(result)
    return ""

# yes, this is a really bad way to detect an email
# but we may have to hide something like user@<em>domain</em>
# it is only use to hide an email
_email_rx = re.compile(r"\b[\w.>_<%+-]+@[\w_<>]+\.[\w_><]+\b")
@register.filter
def hide_emails(text):
    """
    Returns *text* with all emails removed.
    """
    from django.conf import settings
    if getattr(settings, "HIDE_EMAILS", False):
        text = _email_rx.sub("", text)
    return text

# from http://djangosnippets.org/snippets/2428/ by naktinis

"""
The tag generates a parameter string in form '?param1=val1&param2=val2'.
The parameter list is generated by taking all parameters from current
request.GET and optionally overriding them by providing parameters to the tag.

This is a cleaned up version of http://djangosnippets.org/snippets/2105/. It
solves a couple of issues, namely:
 * parameters are optional
 * parameters can have values from request, e.g. request.GET.foo
 * native parsing methods are used for better compatibility and readability
 * shorter tag name

Usage: place this code in your appdir/templatetags/add_get_parameter.py
In template:
{% load add_get_parameter %}
<a href="{% add_get param1='const' param2=variable_in_context %}">
Link with modified params
</a>

It's required that you have 'django.core.context_processors.request' in
TEMPLATE_CONTEXT_PROCESSORS

Original version's URL: http://django.mar.lt/2010/07/add-get-parameter-tag.html
"""

class AddGetParameter(Node):
    def __init__(self, values):
        self.values = values
        
    def render(self, context):
        req = resolve_variable('request', context)
        params = req.GET.copy()
        for key, value in self.values.items():
            params[key] = value.resolve(context)
        return '?%s' %  params.urlencode()


@register.tag
def add_get(parser, token):
    pairs = token.split_contents()[1:]
    values = {}
    for pair in pairs:
        s = pair.split('=', 1)
        values[s[0]] = parser.compile_filter(s[1])
    return AddGetParameter(values)
