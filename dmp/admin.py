from dmp.models import *
from dmp.forms import ProjectAdminForm, NotesForm
from django.forms import BaseInlineFormSet
from django.contrib.auth.models import *
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline



# this is the customisation of the admin interface

#-----
# This is the interface for the data products


class NotesInline(GenericTabularInline):
    model = Note
    form = NotesForm
    extra = 0
    readonly_fields = ('added','creator',)
    classes = ['collapse']

class MetadataFormInline(GenericTabularInline):
    model = MetadataForm
    extra = 0
    readonly_fields = ('modified',)
    classes = ['collapse']

class SchedulerInline(admin.TabularInline):
    model = Reminder
    extra = 0
    readonly_fields = ('due_date',)
    classes = ['collapse']


class DataProductAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('title', 'status','sciSupContact',)
    search_fields = ('title', 'contact')
    list_filter = ('sciSupContact','status',)

    fieldsets = (
        (None, {
            'fields': ('title', 'desc',),
        }),
        ('', {
            #'classes': ('collapse',),
            'fields': ('datavol','project','sciSupContact',
                       'contact1','contact2','deliverydate',
                       'preservation_plan','status','data_URL')
        })
    )

    inlines = [NotesInline]

    def save_formset(self, request, form, formset, change):
        if formset.model != Note:
            return super(DataProductAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.creator = request.user
            instance.save()
        formset.save()


admin.site.register(DataProduct, DataProductAdmin)


#-----
# This is the interface for the projects

class ProjectAdmin(admin.ModelAdmin):
    save_on_top = True


    list_display = ('title', 'project_groups_links', 'startdate', 'enddate', 'initial_contact', 'dmp_agreed', 'status', 'ndata','sciSupContact','grant_links')
    search_fields = ('title', 'desc', 'PI', 'Contact1', 'Contact2')
    list_filter = ('status', 'sciSupContact', 'date_added')
    filter_horizontal = ('third_party_data',)
    form = ProjectAdminForm
    fieldsets = (
        (None, {
            'fields': (('title', 'PI', 'PIemail'), 'desc',),
        }),
        ('', {
            #'classes': ('collapse',),
            'fields': (
            ('startdate', 'enddate'), ('initial_contact','dmp_agreed'),
            ('sciSupContact', 'status'),
            ('primary_dataCentre','other_dataCentres'),
            'dmp_URL','ODMP_URL','moles_URL')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('Contact1', 'Contact2', 'projectcost',
                      'services', 'third_party_data',
                      'project_URL', 'project_usergroup')
        }),
    )

    inlines = [NotesInline,MetadataFormInline, SchedulerInline]

    def save_formset(self, request, form, formset, change):
        if formset.model != Note:
            return super(ProjectAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.creator = request.user
            instance.save()
        formset.save()


admin.site.register(Project, ProjectAdmin)


class GrantAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('number', 'project', 'gotw', 'scrape_project')
    search_fields = ('number', 'project__title')
    fields = ('number', 'project')
    #readonly_fields=('title', 'pi', 'desc')
admin.site.register(Grant, GrantAdmin)

class ProjectGroupAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'desc')
    search_fields = ('name', 'desc')
    filter_horizontal = ('projects', )
admin.site.register(ProjectGroup, ProjectGroupAdmin)


class NotesAdmin(admin.ModelAdmin):

    list_display = ('content_type','location','creator','added')
    list_filter = ('content_type','creator')


admin.site.register(Note, NotesAdmin)

class MetadataAdmin(admin.ModelAdmin):
    pass

admin.site.register(MetadataForm,MetadataAdmin)

class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_name','template_ref', 'last_edited', 'edited_by')


    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('template_ref',)
        return self.readonly_fields

admin.site.register(EmailTemplate, EmailTemplateAdmin)

class ReminderAdmin(admin.ModelAdmin):
    list_display = ['id','description']
admin.site.register(Reminder, ReminderAdmin)