from django.conf.urls import include, url
from django.contrib import admin


from .views import *

urlpatterns = [

     url(r'^$', home, name="home"),

     url(r'^project/(?P<project_id>\d+)/adddataproduct$', add_dataproduct),
     url(r'^project/(?P<project_id>\d+)/show$', showproject),
     url(r'^myprojects$', my_projects),
     url(r'^datamad_update$', datamad_update),
     url(r'^projectsvis$', projects_vis),
     url(r'^projectsbyperson$', projects_by_person, name="projects_by_person"),
     url(r'^grant/(?P<id>\d+)/scrape$', gotw_scrape),
     url(r'^grant/(?P<grant_id>\d+)/link$', link_grant_to_project),
     url(r'^$', home, name='index'),
     url(r'^home/$', home, name='home'),
     url(r'^project/DOG_report/$', DOG_report, name="DOG_report"),
     url(r'project/DOG_report/grant_value_report$', grant_value_report,name="grant_value_report"),

     # Send emails to PI
     url(r'^project/email_templates/(?P<project_id>\d+)/$', mail_template, name="email_templates"),
     url(r'^emailhelp/$',email_help,name="email_help"),

     # Google drive draft DMP upload and authorisation process
     url(r'^project/(?P<project_id>\d+)$', dmp_draft, name="dmp_draft"),
     url(r'^google_drive_authorise/$', google_drive_authorise, name='google_authorise'),
     url(r'^google_drive_token_exchange/$', google_drive_token_exchange, name='google_token_exchange'),
     url(r'^google_drive_upload/(?P<project_id>\d+)/$', google_drive_upload, name='dmp_upload'),
     url(r'^google_drive_revoke/(?P<project_id>\d+)/$', google_drive_token_revoke, name="google_token_revoke"),
     url(r'^render_template/(?P<project_id>\d+)/(?P<template_id>\d+)$', render_template, name="render_template"),


     # Grant uploader process
     url(r'^grant/grant_upload/$',grant_uploader, name="grant_uploader"),
     url(r'^grant/grant_upload/confirm$',grant_upload_confirm, name="grant_upload_confirm"),
     url(r'^grant/grant_upload_complete/$', grant_upload_complete, name="grant_upload_complete"),


     # todo list Requests
     url(r'^todo_list/$', todo_list, name="todo_list"),
     url(r'^todo_list/(?P<scisupcontact>[\w]+)$', todo_list, name="todo_list_filter"),
          # todolist AJAX requests
          url(r'^todo_list/modal/(?P<object_type>[\w]+)/(?P<object_id>\d+)', return_reminder, name="reminder_ajax"), #populates modal with data and sets the target url for the form.
          url(r'^todo_list/update_duedate/(?P<object_type>[\w]+)/(?P<object_id>\d+)/(?P<time_interval>[\w-]+)', calculate_due_date, name="calculate_due_date"),

     url(r'^todo_list/save_reminder/(?P<object_type>[\w]+)/(?P<object_id>\d+)', modify_reminder, name="modify_reminder"),
     url(r'^todo_list/summary/$', todolist_summary, name="todolist_summary"),

]
