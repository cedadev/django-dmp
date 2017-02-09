from dmp.models import *
from django.shortcuts import redirect, render_to_response, get_object_or_404, render
from django.http.response import HttpResponse
from dmp.forms import *
from django.core.exceptions import ValidationError

from django.contrib.auth.models import *
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from dateutil.relativedelta import relativedelta
import json
from django.template import Context, Template
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.utils.html import strip_tags


import requests
import datetime
import re
import string
import time
import os
import csv


# set http proxy for wget calls
# os.environ["http_proxy"] = "http://wwwcache.rl.ac.uk:8080"


def home(request):
    # Home page view
    return render_to_response('dmp/home.html', {'user': request.user})

def dmp_draft(request, project_id):
    # a summary of a single project
    project = get_object_or_404(Project, pk=project_id)
    return render_to_response('dmp/dmp_draft.html', {'project': project,})


def add_dataproduct(request, project_id):
    # add a data product to a project
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None

    project = get_object_or_404(Project, pk=project_id)
    dp = DataProduct(title="NEW DATA PRODUCT",
                     datavol=1000*1000*1000,
                     contact1=project.PI,
                     preservation_plan="KeepIndefinitely",
                     sciSupContact=user,
                     project=project,
                     status="WithProjectTeam")
    dp.save()
   
    return redirect('/admin/dmp/dataproduct/%s' % dp.pk)


def my_projects(request):
    # list projects for logged in user
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None

    # if set override login user
    scisupcontact = request.GET.get('scisupcontact', None) 
    if scisupcontact == 'None':
        scisupcontact = None
    if scisupcontact:
        user = User.objects.filter(username=scisupcontact)[0]

    projects = Project.objects.filter(sciSupContact=user)
    
    # if set override login user
    listall = request.GET.get('listall', None)
    if not listall:  
        projects = projects.exclude(status='Proposal').exclude(status='NotFunded')
        projects = projects.exclude(status='NoData').exclude(status='Defaulted').exclude(status='Complete')

    projects = projects.order_by('modified')

    return render_to_response('dmp/my_projects.html',
                              {'projects': projects, 'user': user, 'listall': listall,
                               'modchecktime': datetime.datetime.now()-datetime.timedelta(days=90)})


def datamad_update(request):
    projects = Project.objects.all()

    order = request.GET.get('order', '')
    if order:
        order = order.split(',')    
        projects = projects.order_by(*order)
        order = ','.join(order)
    
    return render_to_response('dmp/datamad_update.html',
                              {'projects': projects, 'order': order,
                               'modchecktime': datetime.datetime.now()-datetime.timedelta(days=90)})


def link_grant_to_project(request, grant_id):
    # list projects for logged in user
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None

    grant = get_object_or_404(Grant, pk=grant_id)

    searchstring = request.GET.get('search', '') 
    project_id = request.GET.get('project', None) 

    # if projectid set then set and redirest back to grant page
    if project_id: 
        project = get_object_or_404(Project, pk=project_id)
        grant.project = project
        grant.save()
        return redirect('/admin/dmp/grant?o=3')
 
    projectscores = {}
    searchstrings = searchstring.split()
    
    stopwords = "a,an,and,are,as,at,by,for,from,had,has,have,how,if,in,into,is,it,"
    stopwords += "its,no,not,of,off,on,or,so,some,than,that,the,then,there,these,they,"
    stopwords += "this,to,too,us,wants,was,were,what,when,where,which,while,who,why,"
    stopwords += "will,with,would,dr,prof,doctor,professor"
    stopwords = stopwords.split(',')
    
    for s in searchstrings:
        if s.lower() in stopwords:
            continue
           
        projects_bytitle = Project.objects.filter(title__icontains=s)
        projects_bypi = Project.objects.filter(PI__icontains=s)

        for p in projects_bytitle: 
            if p in projectscores:
                projectscores[p] += 1
            else:
                projectscores[p] = 1
        for p in projects_bypi: 
            if p in projectscores:
                projectscores[p] += 1
            else:
                projectscores[p] = 1

    topprojectscores = sorted(projectscores, key=projectscores.get) 
    topprojectscores = topprojectscores[-8:]
    topprojectscores.reverse()
    for i in range(len(topprojectscores)):
        project = topprojectscores[i]
        score = projectscores[project]
        topprojectscores[i] = (project, score)
    context = {'projectscores': topprojectscores, 'grant': grant, 'user': user,
               'search': searchstring}
    
    return render_to_response('dmp/link_grant_to_project.html', context)


def projects_by_person(request):

    projects = Project.objects.all()
    projects = projects.exclude(status='Proposal').exclude(status='NotFunded')
    projects = projects.exclude(status='NoData').exclude(status='Defaulted').exclude(status='Complete')

    summary = {}
    for p in projects:
        if p.sciSupContact:
            username = p.sciSupContact.username
        else:
            username = None

        if not username in summary:
            summary[username] = [1,[]]
            for pg in p.project_groups():
                if pg not in summary[username][1]:
                    summary[username][1].append(pg)
        else: 
            summary[username] = [summary[username][0]+1, summary[username][1]]
            for pg in p.project_groups(): 
                if pg not in summary[username][1]:
                    summary[username][1].append(pg)

    return render_to_response('dmp/projects_by_person.html', {'summary': summary})


def projects_vis(request):

    # list projects for logged in user
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None

    # if set override login user
    order = request.GET.get('order', None) 
    show = request.GET.get('show', None) 
    scisupcontact = request.GET.get('scisupcontact', None) 
    if scisupcontact == 'None':
        scisupcontact = None
    if scisupcontact:
        user = User.objects.filter(username=scisupcontact)[0]

    projects = Project.objects.filter(sciSupContact=user)
    
    # if set override login user
    listall = request.GET.get('listall', None)
    if not listall:  
        projects = projects.exclude(status='Proposal').exclude(status='NotFunded')
        projects = projects.exclude(status='NoData').exclude(status='Defaulted').exclude(status='Complete')

    if not order:
        projects = projects.order_by('modified')
    else:
        projects = projects.order_by(order)
    
    for p in projects:
        p.alert_type, p.alert_text = p.alerts()

    return render_to_response('dmp/projects_vis.html',
                              {'projects': projects, 'user': user,
                               'listall': listall, 'show': show,
                               'modchecktime': datetime.datetime.now()-datetime.timedelta(days=90)})


def showproject(request, project_id):
    # a summary of a single project
    project = get_object_or_404(Project, pk=project_id)
    return render_to_response('dmp/showproject.html', {'project': project})


def gotw_scrape(request, id):
    """Scrape grants on the web for grant info then make a project. """
    grant = get_object_or_404(Grant, pk=id)

    # find split grant info from grants on the web
    url = "http://gotw.nerc.ac.uk/list_split.asp?awardref=%s" % grant.number
    split_content = requests.get(url).text
    numbers = set()
    lead_number = grant.number
    start_date = datetime.datetime(3000, 1, 1)
    end_date = datetime.datetime(1900, 1, 1)

    for line in split_content.split('\n'):
        m = re.search('Lead Grant Reference:</b> (NE/\w{3,10}/\w{0,2})', line)
        if m:
            lead_number = m.groups()[0]
        m = re.search('(NE/\w{3,10}/\w{0,2})', line)
        if m:
            number = m.groups()[0]
            numbers.add(number)

        # start date
        m = re.search('<span class="detailsText">(\d{1,2} \w{3} \d{4})', line)
        if m:
            line_start_date = datetime.datetime.strptime(m.groups()[0], "%d %b %Y")
            start_date = min(line_start_date, start_date)

        # end date
        m = re.search('- (\d{1,2} \w{3} \d{4})</span>', line)
        if m:
            line_end_date = datetime.datetime.strptime(m.groups()[0], "%d %b %Y")
            end_date = max(line_end_date, end_date)

    # see if any of the grants are already connected to a project
    for g in Grant.objects.filter(number__in=numbers):
        if g.project is not None:
            grant.project = g.project
            grant.save()
            # redirect to existing project in admin view
            return redirect('/admin/dmp/project/%s' % grant.project.pk)

    # read grant info from lead grant
    if not grant.number: redirect('/admin/dmp/grant/%s' % id)
    url = 'http://gotw.nerc.ac.uk/list_full.asp?pcode=%s&cookieConsent=A' % lead_number
    content = requests.get(url).text
    pi = ''
    title = ''
    filtered_desc = ''

    # find title
    m = re.search('<p class="awardtitle"><b>(.*?)</b></p>', content)
    if m:
        title = str(m.group(1))
    else:
        # if not valid grant number
        return redirect('/admin/dmp/grant/%s' % grant.pk)


    # find abstract
    m = re.search('<p class="small"><b>Abstract:</b> (.*?)</p>', content, re.S)
    if m:
        desc = m.group(1)
        filtered_desc = ''.join(filter(lambda x: x in string.printable, desc))

    # find pi
    m = re.search('<b>Principal Investigator</b>: <a href="list_med_pi.asp\?pi=.*?">(.*?)</a>', content)
    if m:
        pi = str(m.group(1))

    # start date
    m = re.search('<span class="detailsText">(\d{1,2} \w{3} \d{4})', content)
    if m:
        line_start_date = datetime.datetime.strptime(m.groups()[0], "%d %b %Y")
        start_date = min(line_start_date, start_date)

    # end date
    m = re.search('- (\d{1,2} \w{3} \d{4})</span>', content)
    if m:
        line_end_date = datetime.datetime.strptime(m.groups()[0], "%d %b %Y")
        end_date = max(line_end_date, end_date)

    notes = "Imported from gotw %s.\n" % time.strftime("%Y-%m-%d %H:%M")
    scisupcontact = request.user

    # find programme
    m = re.search('<b>Programme</b>: <span class="detailsText"> <a href="list_them\.asp\?them=[\w\+]+">([\w\s]+)</a></span>', content)
    if m:
        programme = str(m.group(1))

    # make project and save
    p = Project(startdate=start_date, enddate=end_date, PI=pi,
                title=title, desc=filtered_desc,
                status="Active", sciSupContact=scisupcontact)
    p.save()

    # make note for project
    Note(
        creator=request.user,
        notes=notes,
        location=p
    ).save()

    # conect grant number to project
    grant.project = p
    grant.save()

    # make new programme if one found
    progs = ProjectGroup.objects.filter(name=programme)
    if len(progs) == 0:
        pg = ProjectGroup(name=programme)
        pg.save()
        pg.projects.add(p)
    else:
        progs[0].projects.add(p)

    # Add this project to any grant number
    for number in numbers:
        g = Grant.objects.filter(number=number, project=None)
        if len(g) > 0:
            g[0].project = p
            g[0].save()

    # redirect to new project in admin view
    return redirect('/admin/dmp/project/%s' % p.pk)

@login_required
def mail_template(request, project_id):

    project = Project.objects.get(pk=project_id)
    opts = project._meta
    data_products = DataProduct.objects.filter(project_id=project_id)

    if request.GET:
    #if request.method == 'GET':

        # load form objects
        type_select = EmailTemplateSelectorForm(request.GET)
        message = EmailMessageForm()

        # get template type to be rendered
        type = request.GET['template_type']

        # autofill email fields
        message.fields['receiver'].initial = project.PIemail
        message.fields['sender'].initial = request.user.email
        message.fields['subject'].initial = project.title

        cc = ''
        for i,grant in enumerate(Grant.objects.filter(project_id=project.id).exclude(data_email=project.PIemail)):
            if grant.data_email is not None:
                if i < 1:
                    cc += grant.data_email
                else:
                    cc += "," + grant.data_email

        message.fields['cc'].initial = cc
        template_obj = Template(EmailTemplate.objects.get(template_ref=type).content)
        message.fields['message'].initial = template_obj.render(Context({'project':project, 'user':request.user,
                                                                         'data_products':data_products}))
        message.fields['template_type'].initial = type

        return render(request, 'dmp/select_email_template.html',
                      {
                       'opts': opts,
                       'project': project,
                       'form_select': type_select,
                       'form_message': message,
                       'template_type': type,
                       })
    elif request.POST:
        form = EmailMessageForm(request.POST)
        type_select = EmailTemplateSelectorForm()
        type = request.POST['template_type']

        if form.is_valid():

            msg = EmailMultiAlternatives(
            subject = request.POST['subject'],
            body = strip_tags(request.POST['message']),
            from_email='noreply@ceda.ac.uk',
            to = [request.POST['receiver']],
            cc = [request.POST['cc']],
            bcc= [request.POST['sender']],
            reply_to= [request.POST['sender']]

            )
            msg.attach_alternative(request.POST['message'],"text/html")
            msg.send()
            messages.success(request, "Your email was sent successfully")

            email_note = '"' + str(EmailTemplate.objects.get(template_ref=type).template_name) + '" email was sent to ' + request.POST['receiver'] + " with " + \
                request.POST['cc'] + " ccd in."


            Note(
                creator=request.user,
                notes= email_note,
                location = project
            ).save()


            return redirect("/admin/dmp/project/%s/change" % project_id)

        return render(request, "dmp/select_email_template.html",
                      {
                      'opts': opts,
                        'project':project,
                          'form_select':type_select,
                          'form_message': form,
                          'template_type': type
        })

    else:



        type_select = EmailTemplateSelectorForm()
        message = EmailMessageForm()

        return render(request,'dmp/select_email_template.html',
                      {'project': project,
                       'opts': opts,
                       'form_select':type_select,
                       'form_message': message
                       })
@login_required
def grant_uploader(request):
    opts = Grant()._meta
    form = GrantUploadForm() #empty unbound form

    return render(request,"dmp/grant_uploader.html",{'form':form, 'opts':opts})

@login_required
def grant_upload_confirm(request):
    '''Processes the form and if the user has uploaded a file, presents the user with a list of the pending changes.'''

    opts = Grant()._meta

    # Counters and boolean switches to handle counting and saving of changes
    g_added = 0

    if request.POST:

        form = GrantUploadForm(request.POST,request.FILES)
        if form.is_valid():

            # Check if user has posted data in the text box
            if request.POST['grant_text'] != '':
                grants = set()
                search_text = request.POST['grant_text']

                # search text for strings matching format of grant reference and add to set for processing.
                for line in search_text.split('\n'):
                    grant_ref = re.search('(NE/\w{3,10}/\w{0,2})', line)
                    if grant_ref:
                        number = grant_ref.groups()[0]
                        grants.add(number)

                if grants:
                    # check to see if grants already exists. If not, add them.
                    for grant in grants:
                        if not Grant.objects.filter(number=grant):
                            instance = Grant(
                                number=grant
                            )
                            instance.save()
                            g_added+=1

                # add appropriate end message and send back to grant uploader.
                if grants and g_added > 0:
                    messages.success(request,"Successfully added " + str(g_added) + " grants.")
                if grants and g_added == 0:
                    messages.info(request,"No new grants found")
                else:
                    messages.error(request,"Text provided does not contain grant numbers")

                return render(request, 'dmp/grant_uploader.html', {"form":form, "opts":opts} )

            else:
                # User has uploaded a DataMad file
                # TODO: Allow script to pass any failed situations, eg. no matching regex.

                # build dictionary of dictionaries to give access to all grant numbers in the file plus their column attributes
                file = request.FILES['grantfile']
                data = csv.reader(file)
                header = next(data)
                grants = {}
                for row in data:
                    if row[0]:
                        row_dict = {}
                        for key, value in zip(header, row):
                            row_dict[key] = value
                        grants[row[0]] = row_dict

                # check arbitary grant ref to make sure that the necessary headers are in place
                if grants.keys()[0]:
                    errors = []
                    # Check necessary keys are in dictionary and flag errors
                    keys = (
                        'Data Contact Email',
                        'Grant Holder',
                        'Parent Grant',
                        'Assigned Data Centre',
                        "Other DC's Expecting Datasets",
                        'Actual End Date',
                        'Title',
                    )
                    for k in keys:
                        try:
                            grants[grants.keys()[0]][k]
                        except KeyError:
                            errors.append(k)

                    if errors:
                        for e in errors:
                            messages.error(request, 'Unexpected or missing column name in input file, was expecting "' + e +'". Correct header and retry.' )
                        return render(request,'dmp/grant_uploader.html',{'form':form, 'opts':opts})

                # Perform dry run to create a list of the changes which will be made for approval.
                # Task dictionaries
                new_grants = []
                new_projects = []
                link_projects = []
                field_updates = []

                # Loop grants
                for grant in grants:
                    # Check if the grant already exists in the database.
                    current_grant = Grant.objects.filter(number=grant)
                    if not current_grant:
                        new_grants.append({"Grant": grant, "Message": "Create new grant"})
                        current_grant = Grant(
                            number=grant,
                        )
                    else :
                        current_grant = current_grant[0]

                    create_project = False

                    # Check if the current grant has a lead grant
                    if grants[grant]["Parent Grant"]:

                        # retrieve parent grant object from database if it exists
                        parent_grant_object = Grant.objects.filter(number=grants[grant]["Parent Grant"]).first()

                        # if parent grant in database and it is not linked with a project
                        if parent_grant_object and not parent_grant_object.project:

                            # If there is a project already in the database with the same name as the grant, link it.
                            if Project.objects.filter(title=grants[grant]['Title']):
                                link_projects.append({"Grant": grant,"Message": "Link existing project called " + grants[grant]['Title']})


                            else:
                                # Otherwise create a new project
                                create_project=True
                    else:
                        # if the current grant does not have a parent listed, it is the parent.
                        if not current_grant.project:

                            # If the current grant does not have a project attached, look in database to see if one
                            # already exists which matches the name of the grant.
                            if Project.objects.filter(title=grants[grant]['Title']):

                                # link the project
                                link_projects.append({"Grant": grant,"Message": "Link existing project called " + grants[grant]['Title']})
                            else:
                                # create new project
                                create_project = True

                    if create_project:
                        # avoid message duplication where grants are subsidiary to a lead grant.
                        # If there is no parent grant listed, it is either the parent grant or on its own so continue.
                        # OR If there is a parent grant listed but the parent grants information is not contained in
                        # the dictionary, then it should be checked.
                        if not grants[grant]["Parent Grant"] or (grants[grant]["Parent Grant"] not in grants):
                            new_projects.append({"Grant": grant, "Message": "Create new project called '" + grants[grant]["Title"] + "'"})

                    # Check if updates required
                    # Only necessary if grant and project already exist
                    if current_grant and current_grant.project:
                        # If there is no parent grant listed, it is either the parent grant or on its own so continue.
                        # OR If there is a parent grant listed but the parent grants information is not contained in
                        # the dictionary then it should be checked.
                        if not grants[grant]["Parent Grant"] or (grants[grant]["Parent Grant"] not in grants):

                            # Check and update project fields.
                            proj = current_grant.project

                            # Check end date
                            if grants[grant]['Actual End Date'] \
                                    and proj.enddate < datetime.datetime.strptime(grants[grant]['Actual End Date'],
                                                                                  "%d/%m/%Y").date():
                                field_updates.append({"Grant": grant, "Message": "Extend End Date", "New_value": grants[grant]["Actual End Date"], "Old_value": proj.enddate.strftime('%d/%m/%Y')})

                            # Check Primary data centre field
                            if grants[grant]['Assigned Data Centre'] \
                                    and proj.primary_dataCentre != grants[grant]['Assigned Data Centre']:
                                field_updates.append({"Grant": grant, "Message": "Change Primary Data Centre", "New_value": grants[grant]['Assigned Data Centre'], "Old_value": proj.primary_dataCentre})

                            # Check "Other Datacentres" field
                            if grants[grant]["Other DC's Expecting Datasets"] \
                                    and proj.other_dataCentres != grants[grant]["Other DC's Expecting Datasets"]:
                                field_updates.append({"Grant":grant, "Message": "Change Other Data Centres", "New_value": grants[grant]["Other DC's Expecting Datasets"], "Old_value": proj.other_dataCentres})

                            # Have a guess at ODMP url if one is not already entered.
                            if not proj.ODMP_URL:
                                field_updates.append({"Grant":grant, "Message": "Add ODMP URL"})

                            # Check to see if grant has an email address, these are used for a CC field when sending email.
                            if grants[grant]['Data Contact Email'] \
                                    and not current_grant.data_email:
                                field_updates.append({"Grant":grant, "Message":"Add Data Email to grant"})

                # If there are no changes, escape the process.
                if not any([new_grants, new_projects, link_projects, field_updates]):
                    messages.success(request,"There are no changes to be made.")
                    return render(request, 'dmp/grant_uploader.html',{"form":form, "opts":opts})

                changes = {
                    "new_grants":new_grants,
                    "new_projects": new_projects,
                    "linked_projects" : link_projects,
                    "field_updates": field_updates
                }
                # Save file contents to database to use when changes are confirmed
                file_to_db = GrantFile.objects.create(
                    file_contents=grants
                )
                id = file_to_db.pk


                return render(request, 'dmp/grant_uploader_changes.html', {"temporary_id": id, "opts":opts, "changes":changes})

        # If form is not valid, return to grant uploader page and display errors.
        else:
            return render(request, 'dmp/grant_uploader.html', {"form":form, "opts":opts})

@login_required
def grant_upload_complete(request):
    # User has accepted or rejected the changes.
    # Check the action, perform necessary operations and remove the temporary file from database.

    form = GrantUploadForm()
    opts = Grant()._meta

    if request.POST:
        # see if user has pressed the cancel button.
        if "cancel" in request.POST:
            # remove temporary file object in database
            temp_file = GrantFile.objects.get(pk=request.POST['pk'])
            temp_file.delete()
            return redirect('grant_uploader')

        # get the file details from the session.
        grants = GrantFile.objects.get(pk=request.POST['pk']).file_contents

        # Counters and boolean switches to handle counting and saving of changes
        g_added = 0
        p_added = 0
        g_updated = 0
        p_updated = 0

        p_change = False
        g_change = False

        # loop through grants, check if they are in the database and add if not
        for grant in grants:
            if not Grant.objects.filter(number=grant):
                grant_instance = Grant(
                    number=grant,
                    data_email=grants[grant]['Data Contact Email']
                )
                grant_instance.save()
                g_added += 1

            # check if there is a project already created for grant. If not, create one.
            # Get current grant object.
            current_grant_obj = Grant.objects.filter(number=grant).order_by('-id').first()

            # Don't create a project unless certain conditions are met.
            create_project = False

            # Only need to check if the current grant does not have a project already
            if current_grant_obj and not current_grant_obj.project:

                # Check if the current grant has a lead grant
                if grants[grant]["Parent Grant"]:
                    # if there is a lead grant and data from the lead grant is in the database, use the lead grant to
                    # create the records.
                    if grants[grant]["Parent Grant"] in grants:
                        lead_grant = grants[grant]["Parent Grant"]
                    elif Grant.objects.filter(number=grants[grant]["Parent Grant"]):
                        lead_grant = grants[grant]["Parent Grant"]
                    else:
                        # Parent grant not in uploaded file.
                        lead_grant = None

                    # Retrieve parent grant object from database, if it exists
                    parent_grant_object = Grant.objects.filter(number=lead_grant).first()

                    # If parent grant in database and it is not linked with a project
                    if parent_grant_object and not parent_grant_object.project:
                        # If there is a project already in the database with the same name as the grant, link it.
                        if Project.objects.filter(title=grants[lead_grant]['Title']):
                            current_grant_obj.project = Project.objects.get(title=grants[lead_grant]['Title'])
                            current_grant_obj.save()
                        else:
                            # Otherwise create a new project
                            create_project = True
                    else:
                        if not parent_grant_object and lead_grant:
                            # Lead grant number is contained in uploaded file but not in database.
                            if Project.objects.filter(title=grants[lead_grant]['Title']):
                                current_grant_obj.project = Project.objects.get(title=grants[lead_grant]['Title'])
                                current_grant_obj.save()
                            else:
                                create_project = True
                        elif not parent_grant_object and not lead_grant:
                            # The parent grant is not in the database and the parent grant is not in the uploaded file.
                            # Don't create new project and move on to the checks. Essentially insufficient information.
                            pass
                        elif parent_grant_object.project:
                            current_grant_obj.project = parent_grant_object.project
                            current_grant_obj.save()

                        # exits with no link or new project created if there is a parent grant listed but the parent grant
                        # information is not contained in the uploaded file or in the database. Grant created but will have
                        # to be manually added to a project.
                else:
                    # If the current grant does not have a parent listed, it is the parent.
                    if not current_grant_obj.project:
                        # If there is a project already in the database with the same name as the grant, link it..
                        if Project.objects.filter(title=grants[grant]['Title']):
                            current_grant_obj.project = Project.objects.get(title=grants[grant]['Title'])
                            current_grant_obj.save()
                        else:
                            # Otherwise create new project
                            create_project = True


            # Create a new project
            if create_project:
                # use lead grant as the source of information to create the project

                lead_grant = grant
                pi_email = ''
                pi = grants[grant]['Grant Holder']
                filtered_desc = ''
                programme = None

                # If there is a parent grant, use this to scrape info from GOTW
                if grants[grant]['Parent Grant']:
                    lead_grant = grants[grant]['Parent Grant']

                    if lead_grant in grants.keys():
                        pi = grants[lead_grant]['Grant Holder']
                        pi_email = grants[lead_grant]['Data Contact Email']

                # scrape information from GOTW
                start_date = datetime.datetime(3000, 1, 1)
                end_date = datetime.datetime(1900, 1, 1)
                url = 'http://gotw.nerc.ac.uk/list_full.asp?pcode=%s&cookieConsent=A' % lead_grant
                content = requests.get(url).text

                # find abstract
                m = re.search('<p class="small"><b>Abstract:</b> (.*?)</p>', content, re.S)
                if m:
                    desc = m.group(1)
                    filtered_desc = ''.join(filter(lambda x: x in string.printable, desc))

                # start date
                m = re.search('<span class="detailsText">(\d{1,2} \w{3} \d{4})', content)
                if m:
                    line_start_date = datetime.datetime.strptime(m.groups()[0], "%d %b %Y")
                    start_date = min(line_start_date, start_date)

                # end date
                m = re.search('- (\d{1,2} \w{3} \d{4})</span>', content)
                if m:
                    line_end_date = datetime.datetime.strptime(m.groups()[0], "%d %b %Y")
                    end_date = max(line_end_date, end_date)

                # find programme
                m = re.search(
                    '<b>Programme</b>: <span class="detailsText"> <a href="list_them\.asp\?them=[\w\+]+">([\w\s]+)</a></span>',
                    content)
                if m:
                    programme = str(m.group(1))

                # If lead grant number is not in the file uploaded, revert back to the current grant.
                # Should not be needed as section above should never create the condition where create_project = True
                # when the parent grant details are not in the uploaded file.
                if lead_grant not in grants:
                    lead_grant = grant

                if pi == grants[lead_grant]['Grant Holder']:
                    pi_email = grants[lead_grant]['Data Contact Email']

                # create new project
                new_proj = Project(
                    title=grants[lead_grant]['Title'],
                    PI=pi,
                    PIemail=pi_email,
                    desc=filtered_desc,
                    startdate=start_date,
                    enddate=end_date,
                    status='Active',
                    sciSupContact=request.user,
                    primary_dataCentre=grants[lead_grant]['Assigned Data Centre'],
                    other_dataCentres=grants[lead_grant]["Other DC's Expecting Datasets"],
                )
                new_proj.save()
                p_added += 1

                # Link grant and new project
                current_grant_obj.project = new_proj
                current_grant_obj.save()

                # make new programme if one found
                progs = ProjectGroup.objects.filter(name=programme)
                if not progs and programme:
                    pg = ProjectGroup(name=programme)
                    pg.save()
                    pg.projects.add(new_proj)

                elif progs:
                    progs[0].projects.add(new_proj)

                # add note to the project
                note = Note(
                    creator=request.user,
                    notes='Project imported from GOTW and DataMad',
                    location=new_proj
                )
                note.save()

            # Check and update project fields.
            proj = current_grant_obj.project

            # If there is no parent grant listed, it is either the parent grant or on its own so continue with checks.
            # OR If there is a parent grant listed but the parent grants information is not contained in
            # the dictionary then it should be checked.

            # This will only check parent grant and child grants where the parent is not included in the uploaded file.
            # Should reduce runtime and duplication of database actions.
            if proj:
                if not grants[grant]["Parent Grant"] or (grants[grant]["Parent Grant"] not in grants):

                    # Check end date
                    # Coerce proj.enddate from datetime.datetime to datetime.date object.
                    if isinstance(proj.enddate,datetime.datetime):
                        proj.enddate = proj.enddate.date()

                    if grants[grant]['Actual End Date'] \
                            and proj.enddate < datetime.datetime.strptime(grants[grant]['Actual End Date'], "%d/%m/%Y").date():
                        proj.enddate = datetime.datetime.strptime(grants[grant]['Actual End Date'], "%d/%m/%Y").date()
                        p_change = True


                    # Check Primary data centre field
                    if grants[grant]['Assigned Data Centre'] \
                            and proj.primary_dataCentre != grants[grant]['Assigned Data Centre']:
                        proj.primary_dataCentre = grants[grant]['Assigned Data Centre']
                        p_change = True

                    # Check "Other Datacentres" field
                    if grants[grant]["Other DC's Expecting Datasets"] \
                            and proj.other_dataCentres != grants[grant]["Other DC's Expecting Datasets"]:
                        proj.other_dataCentres = grants[grant]["Other DC's Expecting Datasets"]
                        p_change = True

                    # Have a guess at ODMP url if one is not already entered.
                    if not proj.ODMP_URL:
                        proj.ODMP_URL = "https://systems.apps.nerc.ac.uk/grants/datamad/Outline%20DMPs/" + grant.replace(
                            "/", "_") + "%20DMP.pdf"
                        p_change = True

            # Check to see if grant has an email address, these are used for a CC field when sending email. Do this for
            # all grants.
            if current_grant_obj:
                if grants[grant]['Data Contact Email'] \
                        and not current_grant_obj.data_email:
                    current_grant_obj.data_email = grants[grant]['Data Contact Email']
                    g_change = True

            # Save changes and update count to track changes
            if p_change:
                proj.save()
                p_updated += 1
                p_change = False
            if g_change:
                current_grant_obj.save()
                g_updated += 1
                g_change = False

        # Display appropriate completion message
        if (g_added > 0 or p_added > 0) and grants:
            messages.success(request, "Successfully added " + str(g_added) + " grants and " + str(p_added) + " projects.")
        elif g_added < 1 and grants:
            messages.info(request, "No new grants were found")
        else:
            messages.error(request, "No grant numbers found")
        if p_updated > 0 or g_updated > 0:
            messages.success(request, "Successfully updated " + str(g_updated) + " grants and " + str(p_updated) + " projects.")

        # remove temporary file object in database
        temp_file = GrantFile.objects.get(pk=request.POST['pk'])
        temp_file.delete()

        return render(request, 'dmp/grant_uploader.html', {'form': form, 'opts': opts})


@login_required
def DOG_report(request):
    todays_date = datetime.datetime.date(datetime.datetime.now())

    # filter queries to collect data for new grant snapshot
    new_grant_query = [
        {'project__status': 'Active'},  # Grant active
        {'project__initial_contact__isnull': False},  # Contacted
        {'project__dmp_agreed__isnull': False},  # DMPs Accepted
        {'project__status': 'NoData'},  # No Data Grants
        {'project__status': 'Complete'},  # Complete Grants
        {'project__status': 'EndedWithDataToCome'},  # Ended with data to come grants
        {}]

    # filter queries to collect data for legacy grant snapshot
    legacy_grant_query = [
        {'project__status': 'Active'},  # Grant active
        {'project__status': 'NoData'},  # No Data Grants
        {'project__status': 'Complete'},  # Complete Grants
        {'project__status': 'EndedWithDataToCome'},  # Ended with data to come grants
        {}
    ]

    new_grant_dates = [datetime.date(2014,04,01),todays_date ]
    legacy_grant_dates = [datetime.date(2010,01,01),datetime.date(2014,03,31)]

    def grant_summary_counter(timerange, statistic):
        total = 0
        start = timerange[0]
        end = timerange[1]

        total += Grant.objects.filter(project__startdate__range=[start, end]).filter(**statistic).count()
        return total

    # loop stats and append info
    new_grant_snapshot = []
    for stat in new_grant_query:
        new_grant_snapshot.append(grant_summary_counter(new_grant_dates, stat))

    # loop stats and append info
    legacy_grant_snapshot = []
    for stat in legacy_grant_query:
        legacy_grant_snapshot.append(grant_summary_counter(legacy_grant_dates,stat))


    # get DOG report
    new_grant_report = DOGstats.objects.filter(stat_type='new_grants').order_by('-date')
    legacy_grant_report = DOGstats.objects.filter(stat_type='legacy_grants').order_by('-date')

    data = []
    for report in new_grant_report:
        data.append( [datetime.datetime.strftime(report.date,"%Y-%b-%d %H:%M"),report.active_grants,report.contacted_grants,report.dmps_accepted,
                      report.no_data,report.complete_grants,report.ended_with_outstanding_data,report.total_grants])
    new_grant_report = data

    data = []
    for report in legacy_grant_report:
        data.append([datetime.datetime.strftime(report.date,"%Y-%b"), report.active_grants, report.no_data,
                     report.complete_grants, report.ended_with_outstanding_data, report.total_grants])
    legacy_grant_report = data

    return render(request, "dmp/DOGreport.html", {'new_grant_snapshot':new_grant_snapshot,
                                                  'legacy_grant_snapshot':legacy_grant_snapshot,
                                                  'new_grant_report': new_grant_report,
                                                  'legacy_grant_report':legacy_grant_report
                                                  })

@login_required
def email_help(request):
    project_fields = Project._meta.get_fields()
    dataProduct_fields = DataProduct._meta.get_fields()
    user_fields = User._meta.get_fields()

    fields = []

    for project in project_fields:
        print (project.name)


    return render(request,"dmp/email_template_info.html")


