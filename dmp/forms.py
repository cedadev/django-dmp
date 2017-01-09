from django.forms.widgets import Widget
from django.forms.utils import flatatt
from django.utils.html import format_html
from django import forms
from dmp.models import EmailTemplate
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.validators import validate_email


class ReadOnlyInput(Widget):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type='hidden',
                                       name=name, value=value)
        return format_html('<input{} />{}', flatatt(final_attrs), value)

class NotesForm(forms.ModelForm):
    class Meta:
        widgets = {'notes': forms.Textarea(attrs={'rows':4 ,'style':'width: 90%'})}
    # def __init__(self, *args, **kwargs):
    #     super(NotesForm, self).__init__(*args, **kwargs)
    #     if self.instance.pk:
    #         self.fields['notes'].widget = ReadOnlyInput()


class ProjectAdminForm(forms.ModelForm):
    def clean(self):
        return self.cleaned_data


def validate_file_extension(value):
    if not value.name.endswith('.csv'):
        raise ValidationError(u'Please upload a csv')


class GrantUploadForm(forms.Form):

    grant_text = forms.CharField(label='Enter text containing grant numbers below:', widget=forms.Textarea(attrs={'style':'height: 200px; width: 50%;'}),required=False)
    grantfile = forms.FileField(label='Select DataMad csv file',required=False, validators= [validate_file_extension])

    def clean(self):
        cleaned_data = super(GrantUploadForm, self).clean()
        form_empty = True
        for field_value in cleaned_data.itervalues():
            # Check for None or '', so IntegerFields with 0 or similar things don't seem empty.
            if field_value:
                form_empty = False
                break
        if form_empty:
            raise ValidationError("You must fill at least one field!")
        return cleaned_data  # Important that clean should return cleaned_data!


class EmailTemplateSelectorForm(forms.Form):
    available_templates = EmailTemplate.objects.all().order_by("template_name")
    CHOICES = []
    for template in available_templates:
        CHOICES.append((template.template_ref,template.template_name))
    template_type = forms.ChoiceField(label='Select email template to use ', choices=CHOICES)


class EmailMessageForm(forms.Form):
    # validation rules
    def multiple_emails_split_with_comma(value):
        ''' if there are multiple @ symbols, check that they are seperated by a comma as the result has to be a python list'''
        if value.count('@') > 1:
                emails = value.split(',')
                if len(emails) < 2:
                    raise ValidationError(_('Please separate email addresses with comma ( , )'))

    def email_validate(value):
        '''Check that the addresses supplied are in the correct format. Will also flag if addresses are not split by a comma'''
        emails = value.split(',')
        for mail in emails:
            try:
                validate_email(mail.strip())
            except ValidationError:
                raise ValidationError(_('%(invalid_email)s is an invalid email '),params={'invalid_email':mail} )

    # fields
    receiver = forms.CharField(label="To", max_length=200, widget=forms.TextInput(attrs={'style':'width:98%'}), validators=[multiple_emails_split_with_comma,email_validate])
    sender = forms.EmailField(label="From", max_length=200, widget=forms.TextInput(attrs={'style':'width:98%'}))
    cc = forms.CharField(label="CC", required=False, widget=forms.TextInput(attrs={'style':'width:98%'}))
    subject = forms.CharField(label="Subject", widget=forms.TextInput(attrs={'style': 'width:98%'}))
    attachments = forms.FileField(label="Attachments", required=False)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 20}))
    template_type = forms.CharField(max_length=200)

class DraftDmpForm(forms.Form):
    draft_dmp = forms.CharField(widget=forms.Textarea(attrs={'style': 'height:700px'}))
