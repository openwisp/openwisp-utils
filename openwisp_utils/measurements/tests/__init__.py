_ENABLED_OPENWISP_MODULES_RETURN_VALUE = {
    'openwisp-utils': '1.1.0a',
    'openwisp-users': '1.1.0a',
}
_OS_DETAILS_RETURN_VALUE = {
    'kernel_version': '5.13.0-52-generic',
    'os_version': '#59~20.04.1-Ubuntu SMP Thu Jun 16 21:21:28 UTC 2022',
    'hardware_platform': 'x86_64',
}

_MODULES_UPGRADE_EXPECTED_EVENTS = [
    {
        'category': 'OS Detail',
        'action': 'kernel_version',
        'name': '5.13.0-52-generic',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OS Detail',
        'action': 'os_version',
        'name': '#59~20.04.1-Ubuntu SMP Thu Jun 16 21:21:28 UTC 2022',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OS Detail',
        'action': 'hardware_platform',
        'name': 'x86_64',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OpenWISP Upgraded',
        'action': 'openwisp-utils',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OpenWISP Upgraded',
        'action': 'openwisp-users',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OpenWISP Upgraded',
        'action': 'OpenWISP Version',
        'name': '23.0.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'Openwisp Module',
        'action': 'openwisp-utils',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'Openwisp Module',
        'action': 'openwisp-users',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'Openwisp Module',
        'action': 'OpenWISP Version',
        'name': '23.0.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
]

_HEARTBEAT_EVENTS = [
    {
        'category': 'OS Detail',
        'action': 'kernel_version',
        'name': '5.13.0-52-generic',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OS Detail',
        'action': 'os_version',
        'name': '#59~20.04.1-Ubuntu SMP Thu Jun 16 21:21:28 UTC 2022',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OS Detail',
        'action': 'hardware_platform',
        'name': 'x86_64',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'Openwisp Module',
        'action': 'openwisp-utils',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'Openwisp Module',
        'action': 'openwisp-users',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'Openwisp Module',
        'action': 'OpenWISP Version',
        'name': '23.0.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
]
_NEW_INSTALLATION_EVENTS = [
    {
        'category': 'OS Detail',
        'action': 'kernel_version',
        'name': '5.13.0-52-generic',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OS Detail',
        'action': 'os_version',
        'name': '#59~20.04.1-Ubuntu SMP Thu Jun 16 21:21:28 UTC 2022',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'OS Detail',
        'action': 'hardware_platform',
        'name': 'x86_64',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'New OpenWISP Installation',
        'action': 'openwisp-utils',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'New OpenWISP Installation',
        'action': 'openwisp-users',
        'name': '1.1.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
    {
        'category': 'New OpenWISP Installation',
        'action': 'OpenWISP Version',
        'name': '23.0.0a',
        'value': 1,
        'times': 1,
        'period_start': 1701388800,
        'period_end': 1701388800,
    },
]
