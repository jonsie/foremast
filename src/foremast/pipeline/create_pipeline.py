"""Create Pipelines for Spinnaker."""
import collections
import json
import logging
import os
from pprint import pformat

import requests

from ..consts import API_URL
from ..exceptions import SpinnakerPipelineCreationFailed
from ..utils import (ami_lookup, get_app_details, get_subnets,
                     get_template, get_properties)
from .clean_pipelines import clean_pipelines
from .construct_pipeline_block import construct_pipeline_block
from .renumerate_stages import renumerate_stages


class SpinnakerPipeline:
    """Manipulate Spinnaker Pipelines.

    Args:
        app_name: Str of application name.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))

        self.app_info = app_info
        self.generated = get_app_details.get_details(app=self.app_info['app'])
        self.app_name = self.generated.app_name()
        self.group_name = self.generated.project

        self.settings = get_properties(self.app_info['properties'])

        if self.app_info['env']:
            self.environments = [self.app_info['env']]
        else:
            self.environments = self.settings['pipeline']['env']

    def post_pipeline(self, pipeline):
        """Send Pipeline JSON to Spinnaker."""
        url = "{0}/pipelines".format(API_URL)

        if isinstance(pipeline, str):
            pipeline_json = pipeline
        else:
            pipeline_json = json.dumps(pipeline)

        self.log.debug('Pipeline JSON:\n%s', pipeline_json)

        pipeline_response = requests.post(url,
                                          data=pipeline_json,
                                          headers=self.header)

        self.log.debug('Pipeline creation response:\n%s',
                       pipeline_response.text)

        if not pipeline_response.ok:
            raise SpinnakerPipelineCreationFailed(
                'Failed to create pipeline for {0}: {1}'.format(
                    self.app_name, pipeline_response.json()))

        self.log.info('Successfully created "%s" pipeline',
                      json.loads(pipeline_json)['name'])

    def render_wrapper(self, region='us-east-1'):
        """Generate the base Pipeline wrapper.

        Args:
            region (str): AWS Region.

        Returns:
            dict: Rendered Pipeline wrapper.
        """
        base = self.settings['pipeline']['base']

        if self.app_info.get('base'):
            base = self.app_info['base']

        email = self.settings['pipeline']['notifications']['email']
        slack = self.settings['pipeline']['notifications']['slack']
        ami_id = ami_lookup(name=base,
                            region=region,
                            token_file=self.app_info['token_file'])

        data = {'app': {
            'ami_id': ami_id,
            'appname': self.app_name,
            'base': base,
            'environment': 'packaging',
            'region': region,
            'triggerjob': self.app_info['triggerjob'],
            'email': email,
            'slack': slack
        }}

        self.log.debug('Wrapper app data:\n%s', pformat(data))

        wrapper = get_template(
            template_file='pipeline-templates/pipeline_wrapper.json',
            data=data)

        return json.loads(wrapper)

    def create_pipeline(self):
        """Send a POST to spinnaker to create a new security group."""
        clean_pipelines(app=self.app_name, settings=self.settings)

        pipeline_envs = self.environments
        self.log.debug('Envs from pipeline.json: %s', pipeline_envs)

        regions_envs = collections.defaultdict(list)
        for env in pipeline_envs:
            for region in self.settings[env]['regions']:
                regions_envs[region].append(env)
        self.log.info('Environments and Regions for Pipelines:\n%s',
                      json.dumps(regions_envs, indent=4))

        subnets = get_subnets()

        pipelines = {}
        for region, envs in regions_envs.items():
            # TODO: Overrides for an environment no longer makes sense. Need to
            # provide override for entire Region possibly.
            pipelines[region] = self.render_wrapper(region=region)

            previous_env = None
            for env in envs:
                try:
                    region_subnets = {region: subnets[env][region]}
                except KeyError:
                    self.log.info('%s is not available for %s.', env, region)
                    continue

                block = construct_pipeline_block(env=env,
                                                 generated=self.generated,
                                                 previous_env=previous_env,
                                                 region=region,
                                                 region_subnets=region_subnets,
                                                 settings=self.settings[env],
                                                 pipeline_data=self.settings['pipeline'])

                pipelines[region]['stages'].extend(json.loads(block))

                previous_env = env

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for region, pipeline in pipelines.items():
            renumerate_stages(pipeline)

            self.post_pipeline(pipeline)

        return True
