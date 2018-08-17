# Copyright 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

from ironic.common.i18n import _

opts = [
    cfg.StrOpt('region_name',
               deprecated_for_removal=True,
               deprecated_reason=_("Use 'region_name' option in the following "
                                   "sections - '[service_catalog]', "
                                   "'[neutron]', '[glance]', '[cinder]', "
                                   "'[swift]' and '[inspector]' to configure "
                                   "region for those services individually."),
               help=_('The region used for getting endpoints of OpenStack'
                      ' services.')),
]


def register_opts(conf):
    conf.register_opts(opts, group='keystone')