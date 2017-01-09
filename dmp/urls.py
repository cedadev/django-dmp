from django.conf.urls import include, url
from django.contrib import admin


from views import *



urlpatterns = [
     url(r'^project/(?P<project_id>\d+)$', dmp_draft, name="dmp_draft"),
     url(r'^project/(?P<project_id>\d+)/adddataproduct$', add_dataproduct),
     url(r'^project/(?P<project_id>\d+)/show$', showproject),
     url(r'^myprojects$', my_projects),
     url(r'^datamad_update$', datamad_update),
     url(r'^projectsvis$', projects_vis),
     url(r'^projectsbyperson$', projects_by_person, name="projects_by_person"),
     url(r'^grant/(?P<id>\d+)/scrape$', gotw_scrape),
     url(r'^grant/(?P<grant_id>\d+)/link$', link_grant_to_project),
     url(r'^email_templates/(?P<project_id>\d+)/$', mail_template, name="email_templates"),
     url(r'^grant/grant_upload/$',grant_uploader, name="grant_uploader"),
     url(r'^DOG_report/$', DOG_report, name="DOG_report"),
     url(r'^$', home, name='index'),
     url(r'^home/$', home, name='home'),
     url(r'^emailhelp/$',email_help,name="email_help"),
]
