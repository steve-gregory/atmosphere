#!/usr/bin/env python
import argparse
import os
import sys
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)
os.environ["DJANGO_SETTINGS_MODULE"] = "atmosphere.settings"

import django; django.setup()

import libcloud.security

from core.models import AtmosphereUser as User
from core.models import Provider, ProviderMachine, Size
from core.query import only_current

from service.instance import launch_instance


libcloud.security.VERIFY_SSL_CERT = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="The OpenStack compute node to launch"
                        " instances on.")
    parser.add_argument("--name", default="Agent Smith",
                        help="The OpenStack compute node to launch"
                        " instances on.")
    parser.add_argument("--provider-list", action="store_true",
                        help="List of provider names and IDs")
    parser.add_argument("--provider-id", type=int, help="Atmosphere provider"
                        " to use when launching instances.")
    parser.add_argument("--machine-alias", help="Atmosphere machine alias,"
                        " or list of machine_alias separated by comma,"
                        " to use when launching instances.")
    parser.add_argument("--size-id", help="Atmosphere size to use when"
                        " launching instances.")
    parser.add_argument("--size-list", action="store_true",
                        help="List of size names and IDs")
    parser.add_argument("--skip-deploy", action="store_true",
                        help="Don't run Atmosphere's deploy.")
    parser.add_argument("--count", default=1, type=int,
                        help="Number of instances to launch.")
    parser.add_argument("--user", help="Atmosphere username to use.")
    args = parser.parse_args()
    if args.provider_list:
        handle_provider_list()
        if not args.provider_id:
            sys.exit(0)
    handle_provider(args)
    provider = Provider.objects.get(id=args.provider_id)
    handle_size(args, provider)
    size = Size.objects.get(id=args.size_id)
    machines = handle_machine(args, provider)
    user = User.objects.get(username=args.user)
    handle_count(args)
    print "Using Provider %s." % provider
    print "Using Size %s." % size.name
    if args.host:
        host = "nova:%s" % args.host
    else:
        host = None
    launch(user, args.name, provider, machines, size,
           host, args.skip_deploy, args.count)
    if args.count == 1:
        print "Launched %d instance." % args.count
    else:
        print "Launched %d instances." % args.count


def handle_provider_list():
    print "ID\tName"
    for p in Provider.objects.all().order_by('id'):
        print "%d\t%s" % (p.id, p.location)


def handle_provider(args):
    if not args.provider_id:
        print "Error: provider-id is required. To get a list of providers"\
            " use --provider-list."
        sys.exit(1)


def handle_machine(args, provider):
    if not args.machine_alias:
        print "Error: A machine-alias is required."
        sys.exit(1)
    if ',' not in args.machine_alias:
        return [ProviderMachine.objects.get(
            instance_source__identifier=args.machine_alias,
            instance_source__provider_id=provider.id)]
    machines = args.machine_alias.split(",")
    print "Batch launch of images detected: %s" % machines
    return [
        ProviderMachine.objects.get(
            instance_source__identifier=machine_alias,
            instance_source__provider_id=provider.id)
        for machine_alias in machines]


def handle_size(args, provider):
    if args.size_list:
        print "ID\tName\tCPU\tMemory"
        for s in Size.objects.filter(only_current(),
                                     provider=provider).order_by('id'):
            print "%s\t%s\t%d\t%d" % (s.id, s.name, s.cpu, s.mem)
        sys.exit(0)
    if not args.size_id:
        print "Error: size-id is required. To get a list of sizes"\
            " use --size-list."
        sys.exit(1)


def handle_count(args):
    if args.count < 1 or args.count > 10:
        print "Error: Count must be between 1 and 10."
        sys.exit(1)


def launch(user, name, provider, machines, size,
           host, skip_deploy, count):
    ident = user.identity_set.get(provider_id=provider.id)
    instances = []
    kwargs = {}
    if host:
        kwargs['ex_availability_zone'] = host
    for c in range(0, count):
        for machine in machines:
            try:
                instance_id = launch_instance(
                    user, ident.uuid, size.alias,
                    machine.instance_source.identifier,
                    name=name,
                    deploy=(not skip_deploy),
                    **kwargs)
                print "Successfully launched Machine %s : %s" \
                    % (machine.instance_source.identifier, instance_id)
                instances.append(instance_id)
            except Exception as exc:
                print "Error on launch of Machine %s : %s" \
                    % (machine.instance_source.identifier, exc)
    return instances


if __name__ == "__main__":
    main()
