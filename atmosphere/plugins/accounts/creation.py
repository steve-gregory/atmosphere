from threepio import logger
from jetstream.allocation import TASAPIDriver


class AccountCreationPlugin(object):
    """
    Validation plugins must implement a create_accounts function that
    takes two  arguments:
    - `provider (core.models.Provider)`
    - `user (core.models.AtmosphereUser)`
    Plugins are responsible for implementing `get_credentials_list`.
    The list of credentials are fed into the AccountDriver
    The accounts are created based on those credentials
    and a list of new `core.models.Identity` are returned
    """

    def get_credentials_list(self, provider, username):
        raise NotImplementedError("See docs")

    def create_accounts(self, provider, username):
        from service.driver import get_account_driver
        account_driver = get_account_driver(provider)
        if not account_driver:
            raise ValueError(
                "Provider %s produced an invalid account driver -- Use plugin after you create a provider."
                % provider)
        credentials_list = self.get_credentials_list(provider, username)
        identities = []
        for credentials in credentials_list:
            try:
                logger.debug(
                    "Creating new account for %s with credentials - %s"
                    % (username, credentials))
                new_identity = account_driver.create_account(**credentials)
                identities.append(new_identity)
            except:
                logger.exception(
                    "Could *NOT* Create NEW account for %s"
                    % username)
        return identities


class UserGroup(AccountCreationPlugin):

    def get_credentials_list(self, provider, username):
        """
        For each provider:
        - 'username' and 'project_name' == username
        """
        credentials_list = []
        credentials_list.append({
            'username': username,
            'project_name': username,
            'account_user': username,
            'group_name': username,
            'is_leader': True,
        })
        return credentials_list


class XsedeGroup(AccountCreationPlugin):
    """
    For Jetstream, AccountCreation respects the "Directory"
    between User and Project.

    NOTE: This requires some communication with the TAS API Driver
    and can take some time to generate a list...
    Due to memoization, it is best to "Batch" these requests.

    For Each project listed for tacc_username(user.username):
    - 'username' == tacc_username(user.username)
    - 'project_name' == tacc_project_name
    """

    def __init__(self):
        self.tas_driver = TASAPIDriver()

    def get_credentials_list(self, provider, username):
        credentials_list = []
        print "Collecting credentials for %s" % username
        tacc_username = self.tas_driver._xsede_to_tacc_username(username)
        if not tacc_username:
            logger.warn(
                "TAS Driver found no TACC Username for XUP User %s"
                % user.username)
            tacc_username = username
        tacc_projects = self.tas_driver.find_projects_for(tacc_username)
        for tacc_project in tacc_projects:
            tacc_projectname = tacc_project['chargeCode']
            tacc_leader_username = tacc_project.get('pi', {})\
                .get('username', '')
            is_leader = tacc_leader_username == tacc_username
            credentials_list.append({
                'account_user': username,
                'username': tacc_username,
                'project_name': tacc_projectname,
                'group_name': tacc_projectname,
                'is_leader': is_leader,
            })
        print "%s - %s" % (username, credentials_list)
        return credentials_list