import utils


def test_dict_deep_set():
    d = dict()
    d['cn'] = dict()
    utils.dict_deep_set(d, ['cn', 'cctv', 'www'])
    utils.dict_deep_set(d, ['com', 'cctv', 'www'])
    assert d['cn']['cctv'] == 'www'
    assert d['com']['cctv'] == 'www'
    assert d['com'].get('cct') != 'www'


if __name__ == '__main__':
    test_dict_deep_set()
