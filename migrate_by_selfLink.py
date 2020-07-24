from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor

import warnings

import argparse
from vm_network_migration.handler_helper import selfLink_executor

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--selfLink',
                        help='The selfLink of the target resource.')

    parser.add_argument('--network', help='The name of the target network.')
    parser.add_argument(
        '--subnetwork',
        default=None,
        help='The name of target subnetwork. For auto mode networks,'
             ' this field is optional')
    parser.add_argument(
        '--preserve_instance_external_ip',
        default=False,
        help='Preserve the external IP addresses of the instances serving this forwarding rule')

    args = parser.parse_args()

    if args.preserve_instance_external_ip == 'True':
        args.preserve_instance_external_ip = True
    else:
        args.preserve_instance_external_ip = False

    if args.preserve_instance_external_ip:

        warnings.warn(
            'You choose to preserve the external IP. If the original instance '
            'has an ephemeral IP, it will be reserved as a static external IP after the '
            'execution.',
            Warning)
        continue_execution = input(
            'Do you still want to preserve the external IP? y/n: ')
        if continue_execution == 'n':
            args.preserve_instance_external_ip = False
    selfLink_executor = SelfLinkExecutor(args.selfLink, args.network, args.subnetwork,
                 args.preserve_instance_external_ip)
    migration_handler = selfLink_executor.build_migration_handler()
    migration_handler.network_migration()