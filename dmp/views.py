from dmp.models import *
from django.shortcuts import redirect, render_to_response, get_object_or_404, render
from django.http.response import HttpResponse
from dmp.forms import *
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

# upload draft dmp to google
import cStringIO as StringIO
from httplib2 import Http
from apiclient.discovery import build
from oauth2client import file, client
from oauth2client import GOOGLE_TOKEN_URI, GOOGLE_REVOKE_URI, GOOGLE_AUTH_URI
from oauth2client.client import HttpAccessTokenRefreshError
import tempfile
from contextlib import contextmanager



from django.contrib.auth.models import *

from django.template import Context, Template
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.html import strip_tags

import requests
import datetime
import re
import string
import time
import os
import csv
import json


# set http proxy for wget calls
# os.environ["http_proxy"] = "http://wwwcache.rl.ac.uk:8080"


def home(request):
    # Home page view
    return render_to_response('dmp/home.html', {'user': request.user})


def google_drive_upload(request, project_id):
    # TODO  handle token revoke
    # Put project id in the session when coming from form submit
    if request.POST:
        request.session['project_id'] = project_id

    try:
        token = request.user.oauth_token
    except ObjectDoesNotExist:
        return redirect('google_authorise')
    else:
        # Upload file to google drive if there is a current token

        # Load the project for the upload
        project = get_object_or_404(Project, pk= project_id)

        # Render DMP template and create string
        filename = project.title + '_DraftDMP.html'
        template = Template(draftDmp.objects.all()[0].draft_dmp_content)
        context = Context({'project': project})
        html = template.render(context)
        result = StringIO.StringIO()
        result.write(html.encode("ISO-8859-1"))

        # Create google credentials object
        creds = client.GoogleCredentials(
            access_token=token.access_token,
            client_secret=settings.DMP_AUTH['OAUTH']['CLIENT_ID'],
            client_id=settings.DMP_AUTH['OAUTH']['CLIENT_ID'],
            refresh_token=token.refresh_token,
            token_expiry=token.token_expiry,
            token_uri=GOOGLE_TOKEN_URI,
            user_agent=None
        )

        # Create temporary file for google to upload
        @contextmanager
        def tempinput(data):
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            temp.write(data)
            temp.close()
            yield temp.name
            os.remove(temp.name)

        desired_name = re.sub('.html','',filename) # name which will be displayed in the Google Drive
        with tempinput(result.getvalue()) as tempfilename:

            # Build drive object
            DRIVE = build('drive', 'v3', http=creds.authorize(Http()))
            FILES = (
                (tempfilename, 'application/vnd.google-apps.document'),
            )
            # Upload file
            for filename, mimeType in FILES:
                metadata = {'name': desired_name}
                if mimeType:
                    metadata['mimeType'] = mimeType
                try:
                    res = DRIVE.files().create(body=metadata, media_body=filename).execute()
                except HttpAccessTokenRefreshError:
                    return redirect('google_authorise')
                if res:
                    messages.success(
                        request,
                        "Uploaded " +
                        desired_name +
                        " to Google Drive"
                    )
            # Add document link to project
            if res:
                google_doc_url = DRIVE.files().get(fileId=res['id'], fields="webViewLink").execute()['webViewLink']
                project.dmp_URL = google_doc_url
                project.save()

        return redirect("/admin/dmp/project/%s/change" % project_id)


def google_drive_authorise(request):

    SCOPES = ('https://www.googleapis.com/auth/drive.file',
              'https://www.googleapis.com/auth/userinfo.profile',
              'https://www.googleapis.com/auth/userinfo.email',)

    flow = client.OAuth2WebServerFlow(
        client_id=settings.DMP_AUTH['OAUTH']['CLIENT_ID'],
        redirect_uri='https://localhost:8000/dmp/google_drive_token_exchange/',
        scope=SCOPES,
        approval_prompt='force',
        access_type='offline',
    )

    # Get authorisation URL
    auth_url = flow.step1_get_authorize_url()

    return redirect(auth_url)


def google_drive_token_exchange(request):
    # TODO handle any error messages
    # Exchange code for token
    SCOPES = ('https://www.googleapis.com/auth/drive.file',
              'https://www.googleapis.com/auth/userinfo.profile',
              'https://www.googleapis.com/auth/userinfo.email',)

    flow = client.OAuth2WebServerFlow(
        client_id=settings.DMP_AUTH['OAUTH']['CLIENT_ID'],
        client_secret=settings.DMP_AUTH['OAUTH']['CLIENT_SECRET'],
        scope=SCOPES,
        approval_prompt='force',
        access_type='offline',
        redirect_uri='https://localhost:8000/dmp/google_drive_token_exchange/'
    )

    token = flow.step2_exchange(request.GET['code'])

    # save token against the current logged in user.
    token = {'token_expiry': token.token_expiry,'access_token': token.access_token,'refresh_token':token.refresh_token}

    OAuthToken.objects.update_or_create(user=request.user, defaults=token)

    #  Retrieve the project id and return to google_drive_upload.
    project_id = request.session.pop('project_id', None)

    return redirect('dmp_upload',project_id)


def dmp_draft(request, project_id):
    # a summary of a single project
    project = get_object_or_404(Project, pk=project_id)
    opts = Project()._meta
    form = DraftDmpForm()

    template_obj = Template(draftDmp.objects.all()[0].draft_dmp_content)
    form.fields['draft_dmp'].initial = template_obj.render(Context({'project': project}))

    # If there us a google token for the current logged in user, collect user information
    try:
        token = request.user.oauth_token
    except ObjectDoesNotExist:
        google_user= None
    else:



        response = json.loads(requests.get('https://www.googleapis.com/oauth2/v3/userinfo?access_token=%s' % token.access_token).text)



        r = requests.get("https://www.googleapis.com/oauth2/v4/token", params={"refresh_token":token.refresh_token,
                                                                               "client_id":settings.DMP_AUTH['OAUTH']['CLIENT_ID'],
                                                                               "client_secret":settings.DMP_AUTH['OAUTH']['CLIENT_SECRET'],
                                                                               "grant_type":"refresh_token"})

        if r.status_code != 200:
            google_user= None
        else:
            google_user = json.loads(r.text)
            google_user['initial'] = google_user['name'][0]


    return render(request,
                  'dmp/dmp_draft.html',
                  {
                      'project': project,
                      'opts': opts,
                      'form': form,
                      'google_user': google_user
                  }
                  )


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
    #TODO add ODMP URL guess when new project created as in the grant uploader.
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

            if request.POST['cc']:
                email_note = '"' + str(EmailTemplate.objects.get(template_ref=type).template_name) + '" email was sent to ' + request.POST['receiver'] + " with " + \
                    request.POST['cc'] + " ccd in."
            else:
                email_note = '"' + str(
                    EmailTemplate.objects.get(template_ref=type).template_name) + '" email was sent to ' + request.POST[
                                 'receiver'] +"."

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

    # Counters and boolean switches to handle counting and saving of changes
    g_added = 0
    p_added = 0
    g_updated = 0
    p_updated = 0

    p_change = False
    g_change = False

    if request.method == 'POST':

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
                updated = False

            else:
                # User has uploaded a DataMad file
                # TODO: Allow script to pass any failed situations, eg. no matching regex.
                # TODO: If script fails, give an informative error message to help the user correct the input.

                # build dictionary of dictionaries to give access to all grant numbers in the file plus their column attributes
                file = request.FILES['grantfile']
                data = csv.reader(file)
                header = next(data)
                grants = {}
                for row in data:
                    row_dict = {}
                    for key, value in zip(header, row):
                        row_dict[key] = value
                    grants[row[0]] = row_dict

                # check arbitary grant ref
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
                        'Title'
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

                # loop through grants, check if they are in the database and add if not
                for grant in grants:
                    if not Grant.objects.filter(number=grant):
                        grant_instance = Grant(
                            number=grant,
                            data_email=grants[grant]['Data Contact Email']
                        )
                        grant_instance.save()
                        g_added += 1

                    # check if there is a project already created with title for grant. If not, create one.
                    if not Project.objects.filter(title=grants[grant]['Title']):
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

                        if pi == grants[grant]['Grant Holder']:
                            pi_email = grants[grant]['Data Contact Email']

                        # create new project
                        new_proj = Project(
                            title = grants[grant]['Title'],
                            PI=pi,
                            PIemail=pi_email,
                            desc=filtered_desc,
                            startdate=start_date,
                            enddate=end_date,
                            status='Active',
                            sciSupContact=request.user,
                            primary_dataCentre = grants[grant]['Assigned Data Centre'],
                            other_dataCentres = grants[grant]["Other DC's Expecting Datasets"],
                        )
                        new_proj.save()
                        p_added += 1

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
                            location = new_proj
                        )
                        note.save()


                    # Link grants and projects, works if new grant and project created or if just linking existing
                    # grants and projects
                    current_grant_obj = Grant.objects.get(number=grant)

                    # Link grant if not currently linked to project
                    if not current_grant_obj.project:
                        current_grant_obj.project = Project.objects.get(title=grants[grant]['Title'])
                        current_grant_obj.save()

                    # Check and update project fields.
                    proj = current_grant_obj.project

                    # Check end date
                    if grants[grant]['Actual End Date'] \
                        and proj.enddate < datetime.datetime.strptime(grants[grant]['Actual End Date'],"%d/%m/%Y").date():
                        proj.enddate = datetime.datetime.strptime(grants[grant]['Actual End Date'],"%d/%m/%Y").date()
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

                    # Check to see if grant has an email address, these are used for a CC field when sending email.
                    if grants[grant]['Data Contact Email'] \
                        and not current_grant_obj.data_email:
                        current_grant_obj.data_email = grants[grant]['Data Contact Email']
                        g_change = True

                    # Save changes and update count to track changes
                    if p_change:
                        proj.save()
                        p_updated += 1
                    if g_change:
                        current_grant_obj.save()
                        g_updated += 1

            # display appropriate completion message
            if (g_added > 0 or p_added > 0) and  grants:
                messages.success(request,"Successfully added "+ str(g_added) + " grants and "+ str(p_added) + " projects.")
            elif g_added < 1 and grants:
                messages.info(request,"No new grants were found")
            else:
                messages.error(request,"No grant numbers found")
            if p_change or g_change:
                messages.success(request,"Successfully updated " + str(g_updated) + " grants and " + str(p_updated) + " projects.")

            return render(request,'dmp/grant_uploader.html',{'form':form, 'opts':opts})
    else:
        form = GrantUploadForm() #empty unbound form

    return render(request,"dmp/grant_uploader.html",{'form':form, 'opts':opts})

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


