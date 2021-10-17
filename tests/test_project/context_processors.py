import sys


def test_theme_helper(request):
    return {
        'OPENWISP_TEST_MODE': sys.argv[1:2] == ['test'],
    }
