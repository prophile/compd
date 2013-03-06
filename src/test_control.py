import control
import mock
import twisted.internet

def test_halt_parse():
    options = control.parse('halt')
    assert options['halt']

def check_showed_usage(responder):
    responder.assert_any_call('Usage: halt')
    responder.assert_any_call('Usage: usage')

def test_usage():
    responder = mock.Mock()
    control.handle('usage', responder)
    check_showed_usage(responder)

def test_halt():
    exit_handler = mock.Mock()
    responder = mock.Mock()
    with mock.patch('twisted.internet.reactor.stop', exit_handler):
        control.handle('halt', responder)
        responder.assert_called_once_with('System going down for halt')
        exit_handler.assert_called_once_with()

def test_unknown():
    responder = mock.Mock()
    control.handle('hnnnng', responder)
    check_showed_usage(responder)

