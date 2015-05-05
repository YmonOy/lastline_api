from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address, MinLengthValidator, MaxLengthValidator

from ll_logger import LogExceptions
from ll_debug import __debugvar__ 

import string
import unicodedata
import json

# Translation support 
import gettext
_ = gettext.gettext

# Validators
validate_max1k = MaxLengthValidator(1024)

def validate_impact(value):
  try:
    value = int(value)
  except (ValueError, TypeError) as e:
    raise ValidationError(
      _('Impact value is not a number: %(value)s'), params={'value': value} )
  except:
    raise ValidationError(
      _('Impact value is invalid: %(value)s'), params={'value': value} )

  if value < 1 or value % 10 != 0 or value > 100:
    raise ValidationError(
      _('Impact value not divisible by 10 and between 10-100: %(value)s'), params={'value': value} )
  else:
    return True

# Latin-1'ish, extended ascii
def charset_extended():
  return(chr(x) for x in range(128,184))

# Accepts data to filter, ascii to excempt from filtration
# Otherwise only allows 'printable' ascii set
def filter_ascii(data, exempted):
  # Normalize unicode to ascii
  try:
    data = unicodedata.normalize('NKFD', data).encode('latin-1', 'replace')
  except TypeError:
    pass
  allchars = string.maketrans('','') # returns chars 0-256
  printable = allchars.translate(allchars, string.printable.join(exempted)) # all allowed
  return data.translate(allchars, printable) # return filtered

# Proper domain, comment, source validation, short names, utf domains, etc?
# Any UTF-8 input to these makes it basically impossible to define safe character sets.
# Best we can do is block out any non-valid UTF-8.
def validate_unicode(data, max_length=None):
  if(max_length is not None):
    if(len(data) > max_length): 
      raise ValidationError(
        _('Input is longer than %(max_length)s characters'), params={'max_length': max_length} )

  try:
    unicode.decode(data, "utf-8", errors='strict')
  except UnicodeError, UnicodeDecodeError:
    raise ValidationError(_('Input is not in valid utf-8'))

# Forms
class Undefined_Form(forms.Form):
  def clean_entries(self):
    return None

class Add_ipForm(forms.Form):
  key = forms.CharField(label='entries', max_length=100, required=False) 
  key_id = forms.CharField(label='entries', max_length=100, required=False)
  subkey_id = forms.CharField(label='entries', max_length=100, required=False)
  entries = forms.CharField(label='entries', max_length=1024)

  def clean_entries(self):
    validate_unicode(self.cleaned_data['key'], max_length=100)
    validate_unicode(self.cleaned_data['key_id'], max_length=100)
    validate_unicode(self.cleaned_data['subkey_id'], max_length=100)

    data = json.loads(self.cleaned_data['entries'])[0] # [{json=a..}]
    if validate_impact((data['impact'])):
      data['impact'] = int(data['impact']) # Unicode str number, decimals, etc
    validate_ipv46_address(data['ip'])
    validate_unicode(data['comment'], max_length=255)
    validate_unicode(data['source'], max_length=45)
    return data

class Delete_ipForm(forms.Form):
  key = forms.CharField(label='entries', max_length=100, required=False) 
  key_id = forms.CharField(label='entries', max_length=100, required=False)
  subkey_id = forms.CharField(label='entries', max_length=100, required=False)
  entries = forms.CharField(label='entries', max_length=524288) # 512kb
 
  def clean_entries(self):
    validate_unicode(self.cleaned_data['key'], max_length=100)
    validate_unicode(self.cleaned_data['key_id'], max_length=100)
    validate_unicode(self.cleaned_data['subkey_id'], max_length=100)

    data = json.loads(self.cleaned_data['entries']) # [{a,b,c}]
    for ip in data:
      validate_ipv46_address(ip)
    return data

class Add_domainForm(forms.Form):
  key = forms.CharField(label='entries', max_length=100, required=False) 
  key_id = forms.CharField(label='entries', max_length=100, required=False)
  subkey_id = forms.CharField(label='entries', max_length=100, required=False)
  entries = forms.CharField(label='entries', max_length=2000)

  def clean_entries(self): 
    validate_unicode(self.cleaned_data['key'], max_length=100)
    validate_unicode(self.cleaned_data['key_id'], max_length=100)
    validate_unicode(self.cleaned_data['subkey_id'], max_length=100)

    data = json.loads(self.cleaned_data['entries'])[0] # [{json=a..}]
    if validate_impact((data['impact'])):
      data['impact'] = int(data['impact']) # Unicode str number, decimals, etc
    validate_unicode(data['domain'], max_length=1024)
    validate_unicode(data['comment'], max_length=255)
    validate_unicode(data['source'], max_length=45)
    return data

class Delete_domainForm(forms.Form):
  key = forms.CharField(label='entries', max_length=100, required=False) 
  key_id = forms.CharField(label='entries', max_length=100, required=False)
  subkey_id = forms.CharField(label='entries', max_length=100, required=False)
  entries = forms.CharField(label='entries', max_length=524288) # 512kb
 
  def clean_entries(self):
    validate_unicode(self.cleaned_data['key'], max_length=100)
    validate_unicode(self.cleaned_data['key_id'], max_length=100)
    validate_unicode(self.cleaned_data['subkey_id'], max_length=100)

    data = json.loads(self.cleaned_data['entries']) # [{a,b,c}]
    for domain in data:
      validate_unicode(domain, max_length=1024)
    return data
