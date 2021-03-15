# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '09 Mar 2021'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from django.core.management.base import BaseCommand
from dmp.models import Project, Reminder, DataProduct
import random
import json

COMPLETED_TRANSITION = [
    'Initial contact',
    'Grant Completed'
]

STATUS_JIRA_MAPPING = {
    'Proposal': {
        'transitions': COMPLETED_TRANSITION,
    },
    'NotFunded': {
        'transitions': COMPLETED_TRANSITION
    },
    'NoData': {
        'transitions': COMPLETED_TRANSITION,
        'component': 'CEDA No data'
    },
    'EndedWithDataToCome': {
        'transitions': COMPLETED_TRANSITION,
        'component': 'CEDA Ended with data to come'
    },
    'Defaulted': {
        'transitions': COMPLETED_TRANSITION,
        'component': 'CEDA No data'
    },
    'NoDataForUs': {
        'transitions': COMPLETED_TRANSITION
    },
    'Complete': {
        'transitions': COMPLETED_TRANSITION
    },
    'Unresponsive': {
        'transitions': COMPLETED_TRANSITION,
        'component': 'CEDA Unresponsive'
    },
    'MergedProject/HandledElsewhere': {
        'transitions': COMPLETED_TRANSITION,
        'component': 'CEDA Merge/handled else where'
    }
}


PROJECT_STATUS_JIRA_MAPPING = {
    'InitialContact': {
        'transitions': [
            'Initial contact'
        ]
    },
    'DMPComms': {
        'transitions': [
            'Initial contact',
            'DMP Comms'
        ]
    },
    'Progress': {
        'transitions': [
            'Initial contact',
            'DMP Comms',
            'Agreed DMP'
        ]
    },
    'DataDelivery': {
        'transitions': [
            'Initial contact',
            'DMP Comms',
            'Agreed DMP',
            'Data Delivery'
        ]
    }
}


def indent_notes(note):
    return note.replace('\n', '\n\t')


def get_user(user):
    if user:
        return user.email


def map_dataproduct(data_product: DataProduct, headline_grant) -> dict:
    """
    Converts a dataproduct from dmp tool to something which can be input into
    datamad2 dataproduct

    :param data_product: Dataproduct to map
    :param headline_grant: Grant reference to attach the data product to

    :returns: dict
    """

    return {
        'grant_ref': headline_grant.number,
        'added': str(data_product.added),
        'modified': str(data_product.modified),
        'data_product_type': 'digital',
        'name': data_product.title,
        'contact': data_product.contact1,
        'preservation_plan': data_product.preservation_plan,
        'description': data_product.desc,
        'data_volume': data_product.datavol,
        'delivery_date': str(data_product.deliverydate),
        'responsibility': get_user(data_product.sciSupContact),
        'additional_comments': "\n".join(
            [f'[{note.creator} {note.added}]: \n\t{indent_notes(note.notes)}' for note in data_product.notes.all()]
        )
    }


def create_subtask(reminder: Reminder, grant_ref: str) -> dict:
    """
    Create subtask from DMP reminder object and link to parent issue.

    :param reminder: DMP Reminder Object
    :param parent_issue: The issue to link the subtask to
    :param grant_ref: Grant reference string
    :param reporter: The person responsible for the subtask
    """

    subtask_dict = {
        'project': 'CEDA',
        'summary': f"{grant_ref}:{reminder.description}",
        'description': '',
        'issuetype': {'name': 'Sub-Task'},
        'duedate': str(reminder.due_date)
    }

    return subtask_dict


class Command(BaseCommand):
    help = 'Migration from the DMP tool to JIRA/Datamad2'

    def handle(self, *args, **options):

        # Return all projects with linked grants
        projects = Project.objects.exclude(grant=None)

        output = []

        for project in projects:

            project_dict = {
                'jira': {},
                'datamad': {}
            }

            # Select the main grant ref
            grants = project.grant_set.all()

            # If there is >1 grant attached there are several scenarios to resolve
            if grants.count() > 1:
                lead_grants = [grant for grant in grants if grant.lead_grant]
                lead_grant_count = len(lead_grants)

                if lead_grant_count > 1:
                    # If > 1 lead. Pick one at random
                    headline_grant = random.choice(lead_grants)

                elif lead_grant_count == 1:
                    # If one, this is the main grant
                    headline_grant = lead_grants[0]

                else:
                    # In some cases there are no lead grants but multiple grants
                    # In this case, choose one at random
                    headline_grant = random.choice(grants)
            else:
                # There is only one grant, pick this one
                headline_grant = grants[0]

            jira_issue_content = {
                'project': 'CEDA',
                'issuetype': {'id': '10602'},
                'summary': f'{headline_grant}: {project.title}',
                'description': project.desc,
            }

            # Add NERC references
            grants = ",".join([
                grant.number for grant in grants
            ])
            jira_issue_content['customfield_11658'] = grants

            # Add the initial contact date
            if project.initial_contact:
                jira_issue_content['customfield_11662'] = str(project.initial_contact)
                project_dict['datamad']['date_contacted_pi'] = str(project.initial_contact)

            # Add components
            dmp_status = STATUS_JIRA_MAPPING.get(project.status)

            if dmp_status:
                dmp_status_components = dmp_status.get('component')
                if dmp_status_components:
                    components = jira_issue_content.get('components', [])
                    components.append({'name': dmp_status_components})
                    jira_issue_content['components'] = components

            # Add the dmp agreed flag
            if project.dmp_agreed:
                components = jira_issue_content.get('components', [])
                components.append({'name': 'CEDA DMP Agreed'})
                jira_issue_content['components'] = components

                # Add to datamad
                project_dict['datamad']['dmp_agreed_date'] = str(project.dmp_agreed)


            # Add the issue content to the dict
            project_dict['jira']['issue'] = jira_issue_content

            ############################################
            # Things which need an active issue to add #
            ############################################

            # Add the JIRA workflow status
            if project.status == 'Active' or project.status == 'NotStarted':
                project_status = PROJECT_STATUS_JIRA_MAPPING.get(project.project_status)

                if project_status:
                    project_dict['jira']['status_transitions'] = project_status['transitions']
            else:
                dmp_status = STATUS_JIRA_MAPPING.get(project.status)

                if dmp_status:
                    project_dict['jira']['status_transitions'] = dmp_status['transitions']

            # Add the project assignee
            project_dict['jira']['assignee'] = project.sciSupContact.email

            # turn notes into a comment
            comments = []
            for note in project.notes.all():
                comment = f'[{note.creator} {note.added}]: \n\t{indent_notes(note.notes)}'
                comments.append(comment)

            project_dict['jira']['comments'] = comments

            # add dmp_URL as an issue link
            links = []
            if project.dmp_URL:
                links.append({
                    'url': project.dmp_URL,
                    'title': 'DMP URL'
                })

            # Add the MOLES URL as an issue link
            if project.moles_URL:
                links.append({
                    'url': project.moles_URL,
                    'title': 'MOLES URL'
                })

            project_dict['jira']['links'] = links

            # turn reminders into subtasks
            reminders = project.reminder_set.all()
            subtasks = []
            for reminder in reminders:
                subtasks.append(create_subtask(reminder, headline_grant))

            project_dict['jira']['subtasks'] = subtasks

            #######################
            # Datamad ONLY Fields #
            #######################

            # Export Data Products

            data_products = []
            for dp in project.data_outputs():
                data_product = map_dataproduct(dp, headline_grant)

                data_products.append(data_product)

            for tp_dp in project.third_party_data.all():
                data_product = map_dataproduct(tp_dp, headline_grant)
                data_product['data_product_type'] = 'third_party'

                data_products.append(data_product)

            project_dict['datamad']['data_products'] = data_products

            output.append(project_dict)

            project.migrated = True
            project.save()

        # Output to json file
        with open('dmp_jira_migration.json', 'w') as writer:
            json.dump(output, writer, indent=4)
