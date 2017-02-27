from django.conf.urls import include, url
from django.contrib import admin


from views import *



urlpatterns = [
     url(r'^project/(?P<project_id>\d+)$', dmp_draft),
     url(r'^project/(?P<project_id>\d+)/adddataproduct$', add_dataproduct),
     url(r'^project/(?P<project_id>\d+)/show$', showproject),
     url(r'^myprojects$', my_projects),
     url(r'^datamad_update$', datamad_update),
     url(r'^projectsvis$', projects_vis),
     url(r'^projectsbyperson$', projects_by_person, name="projects_by_person"),
     url(r'^grant/(?P<id>\d+)/scrape$', gotw_scrape),
     url(r'^grant/(?P<grant_id>\d+)/link$', link_grant_to_project),
     url(r'^email_templates/(?P<project_id>\d+)/$', mail_template, name="email_templates"),
     url(r'^DOG_report/$', DOG_report, name="DOG_report"),
     url(r'^$', home, name='index'),
     url(r'^home/$', home, name='home'),
     url(r'^emailhelp/$',email_help,name="email_help"),
     url(r'^grant/grant_upload/$',grant_uploader, name="grant_uploader"),
     url(r'^grant/grant_upload/confirm$',grant_upload_confirm, name="grant_upload_confirm"),
     url(r'^grant/grant_upload_complete/$', grant_upload_complete, name="grant_upload_complete"),
     url(r'^todo_list/$', todo_list, name= "todo_list"),
     url(r'^todo_list/(?P<scisupcontact>[\w]+)$', todo_list, name="todo_list_filter"),

     # todo list Requests
     url(r'^todo_list/modal/(?P<object_type>[\w]+)/(?P<object_id>\d+)', return_reminder, name="reminder_ajax"),
     url(r'^todo_list/save_reminder/(?P<object_type>[\w]+)/(?P<object_id>\d+)', modify_reminder, name="modify_reminder"),
     url(r'^todo_list/update_duedate/(?P<object_type>[\w]+)/(?P<object_id>\d+)/(?P<time_interval>[\w-]+)', calculate_due_date, name="calculate_due_date"),
     url(r'todo_list/mark_complete/(?P<reminder_id>\d+)$', reminder_complete, name="reminder_complete"),
]
