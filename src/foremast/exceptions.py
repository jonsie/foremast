#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Foremast and Spinnaker related custom exceptions."""


class ForemastError(Exception):
    """Foremast related error."""


class ForemastTemplateNotFound(Exception):
    """Foremast Template was not found."""


class ForemastConfigurationFileError(ForemastError):
    """Foremast configuration file misconfigured."""


class GitLabApiError(ForemastError):
    """GitLab API did not return a good status."""


class SpinnakerError(ForemastError):
    """Spinnaker related error."""


class SpinnakerAppNotFound(SpinnakerError):
    """Spinnaker app not found error."""


class SpinnakerApplicationListError(SpinnakerError):
    """Spinnaker application list error."""


class SpinnakerDnsCreationFailed(SpinnakerError):
    """Spinnaker DNS creation error."""


class SpinnakerElbNotFound(SpinnakerError):
    """Spinnaker Elb not found."""


class SpinnakerTimeout(SpinnakerError):
    """Spinnaker Timeout error."""


class SpinnakerVPCNotFound(SpinnakerError):
    """Spinnaker did not find a VPC."""


class SpinnakerVPCIDNotFound(SpinnakerError):
    """Spinnaker did not find the VPC ID."""


class SpinnakerTaskError(SpinnakerError):
    """Spinnaker Task did not finish properly."""

    def __init__(self, task_state):
        errors = []
        for stage in task_state['execution']['stages']:
            context = stage['context']

            try:
                errors.extend(context['exception']['details']['errors'])
            except KeyError:
                for task in context['kato.tasks']:
                    errors.append(task['exception']['message'])

        super().__init__(*errors)


class SpinnakerTaskInconclusiveError(SpinnakerTaskError):
    """Spinnaker Task state failed to reach terminal state in allowed time."""

    def __init__(self, message):
        mock_failure_stage = {
            'context': {
                'exception': {
                    'details': {
                        'errors': [message],
                    },
                },
            },
        }
        spinnaker_task_state = {
            'execution': {
                'stages': [mock_failure_stage],
            },
        }

        super().__init__(spinnaker_task_state)


class SpinnakerPipelineCreationFailed(SpinnakerError):
    """Could not create Spinnaker Pipeline."""


class SpinnakerPipelineDeletionFailed(SpinnakerError):
    """Could not delete Spinnaker Pipeline."""


class SpinnakerSecurityGroupCreationFailed(SpinnakerError):
    """Could not create Security Group."""


class SpinnakerSecurityGroupError(SpinnakerError):
    """Could not create Security Group."""


class SpinnakerSubnetError(SpinnakerError):
    """Unavailable environment or region."""

    def __init__(self, env='', region=''):
        error = '{0} is not available for {1}'.format(region, env)
        super().__init__(error)


class InvalidEventConfiguration(ForemastError):
    """Invalid AWS Lambda event configuration."""


class SNSTopicNotFound(ForemastError):
    """SNS Topic was not found."""


class SNSSubscriptionDoesNotExist(ForemastError):
    """SNS Subscriptions does not exist."""


class LambdaFunctionDoesNotExist(ForemastError):
    """Lambda function was not found."""


class LambdaAliasDoesNotExist(ForemastError):
    """Lambda function was not found."""


class RequiredKeyNotFound(ForemastError):
    """Required key in json config not found."""


class PrimaryDNSRecordNotFound(ForemastError):
    """Required Primary DNS record does not exist."""


class S3ArtifactNotFound(ForemastError):
    """Could not find Artifact to upload to S3."""


class S3SharedBucketNotFound(ForemastError):
    """Shared S3 Bucket does not exist."""


class DataPipelineDefinitionError(ForemastError):
    """Error Creating Data Pipeline."""
