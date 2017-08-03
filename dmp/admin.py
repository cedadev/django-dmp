from dmp.models import *
from dmp.forms import ProjectAdminForm, NotesForm, ReminderForm
from django.forms import BaseInlineFormSet
from django.contrib.auth.models import *
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.exceptions import ObjectDoesNotExist

# this is the customisation of the admin interface

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

class ReminderInline(admin.TabularInline):
    model = Reminder
    extra = 0
    classes = ['collapse']
    form = ReminderForm


class DataProductAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('title', 'status','sciSupContact',)
    search_fields = ('title',)
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
    list_select_related = ('project','sciSupContact',)

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
            'fields': (
            ('startdate', 'enddate'), ('initial_contact','dmp_agreed'),
            ('sciSupContact', 'status'),
            ('primary_dataCentre','other_dataCentres'),
            'dmp_URL','ODMP_URL','moles_URL', 'reassigned')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('Contact1', 'Contact2', 'projectcost',
                      'services', 'third_party_data',
                      'project_URL', 'project_usergroup')
        }),
    )

    inlines = [NotesInline,MetadataFormInline, ReminderInline]

    list_select_related = ('sciSupContact',)

    def save_formset(self, request, form, formset, change):

        if formset.model == Note:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk:
                    instance.creator = request.user
                instance.save()
            formset.save()

        elif formset.model == Reminder:
            create_note = False
            instances = formset.save(commit=False)

            if formset.deleted_objects:
                note_message = "The following reminders were deleted:\n"
                for reminder in formset.deleted_objects:
                    note_message += '"%s" \n' % reminder.description
                reminder = formset.deleted_objects[0]
                Note(
                    creator= request.user,
                    notes = note_message,
                    location = reminder.project

                ).save()

            if instances:
                note_message = 'Reminders have been modified.\n'
                project = instances[0].project

            for instance in instances:
                try:
                    db_instance = Reminder.objects.get(id=instance.pk)
                except ObjectDoesNotExist:
                    # User has added a new reminder and it is not yet in the database.
                    instance.save()
                else:
                    if instance.description != db_instance.description:
                        note_message += 'Description has changed from: "%s" to: "%s"\n' % (db_instance.description, instance.description)
                        create_note = True

                    a = instance.date_due()

                    if instance.date_due() != db_instance.due_date:
                        note_message += 'Reminder: "%s". Due date has changed from: "%s" to: "%s"\n' % (instance.description, db_instance.due_date, instance.due_date)
                        create_note = True
                    instance.save()

            if create_note:
                Note(
                    creator = request.user,
                    notes = note_message,
                    location = project
                ).save()

            formset.save()
        else:
            return super(ProjectAdmin, self).save_formset(request, form, formset, change)


admin.site.register(Project, ProjectAdmin)


class GrantAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('number', 'project', 'gotw', 'scrape_project', 'lead_grant')
    search_fields = ('number', 'project__title')
    fields = ('number', 'project', 'lead_grant')
    #readonly_fields=('title', 'pi', 'desc')
    list_select_related = ('project',)
admin.site.register(Grant, GrantAdmin)


class ProjectGroupAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'desc')
    search_fields = ('name', 'desc')
    filter_horizontal = ('projects', )
admin.site.register(ProjectGroup, ProjectGroupAdmin)


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_name','template_ref', 'last_edited', 'edited_by')
    list_select_related = ('edited_by',)


    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('template_ref',)
        return self.readonly_fields

admin.site.register(EmailTemplate, EmailTemplateAdmin)


class draftDmpAdmin(admin.ModelAdmin):
    list_display = ('draft_dmp_name',)

    # def has_add_permission(self, request):
    #     if self.model.objects.count() > 0:
    #         return False
    #     else:
    #         return True
admin.site.register(draftDmp,draftDmpAdmin)

########################################################################################################################
#                                                                                                                      #
#                               Section for debugging and development admin views                                      #
#                                                                                                                      #
########################################################################################################################

# class OAuth_tokenAdmin(admin.ModelAdmin):
#     list_display = ('user',)
#
# admin.site.register(OAuthToken, OAuth_tokenAdmin)

# class NotesAdmin(admin.ModelAdmin):
#
#     list_display = ('content_type','location','creator','added')
#     list_filter = ('content_type','creator')
#
#
# admin.site.register(Note, NotesAdmin)

# class MetadataAdmin(admin.ModelAdmin):
#     pass
#
# admin.site.register(MetadataForm,MetadataAdmin)

# class ReminderAdmin(admin.ModelAdmin):
#     list_display = ['id','description','reminder','state']
# admin.site.register(Reminder, ReminderAdmin)
