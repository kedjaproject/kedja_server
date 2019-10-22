import optparse
import sys
import textwrap

from kedja.utils import get_role
from pyramid.paster import bootstrap
from pyramid.security import ALL_PERMISSIONS

from kedja.interfaces import INamedACL


def print_acl():
    description = """\
    Print the specified acl or list available.
    """
    usage = "usage: %prog config_uri"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description)
        )

    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 1:
        print('You must provide at least one argument')
        return 2
    config_uri = args[0]
    with bootstrap(config_uri) as env:
        registry = env['registry']
        for acl in registry.getAllUtilitiesRegisteredFor(INamedACL):
            print("="*80)
            print('%-20s     %-20s' % ("id/name:", acl.name))
            print('%-20s     %-20s' % ("title:", acl.title))
            print("description:\n%s" % acl.description)
            print("-"*80)
            for ace in acl:
                role = get_role(ace[1])
                role_title = "%s (%s)" % (role.title, role)
                permissions = ace[2]
                if permissions == ALL_PERMISSIONS:
                    permissions = "ALL PERMISSIONS"
                print('%-10s    %-20s   %-20s' % (ace[0], role_title, permissions))
