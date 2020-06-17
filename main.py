
import argparse
from vm_network_migration.vm_network_migration import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project_id',
                        help='The project ID of the original VM.')
    parser.add_argument('--zone', help='The zone name of the original VM.')
    parser.add_argument('--original_instance_name',
                        help='The name of the original VM')
    parser.add_argument('--new_instance_name',
                        help='The name of the new VM. It should be'
                             ' different from the original VM')
    parser.add_argument('--network', help='The name of the new network')
    parser.add_argument(
        '--subnetwork',
        default=None,
        help='The name of the subnetwork. For auto mode networks,'
             ' this field is optional')
    parser.add_argument(
        '--preserve_external_ip',
        default=False,
        help='Preserve the external IP address')
    parser.add_argument(
        '--preserve_internal_ip',
        default=False,
        help='Preserve the internal IP address')
    parser.add_argument(
        '--preserve_alias_ip_ranges',
        default=False,
        help='Preserve the alias IP ranges')
    args = parser.parse_args()
    # main(args.project_id, args.zone, args.original_instance_name,
    #      args.new_instance_name, args.network, args.subnetwork)
    main2(args.project_id, args.zone, args.original_instance_name,
          args.new_instance_name, args.network, args.subnetwork,
          args.preserve_external_ip, args.preserve_internal_ip,
          args.preserve_alias_ip_ranges)