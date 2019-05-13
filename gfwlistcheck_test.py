import gfwlistcheck


def test_GfwList_check():
    gfwlist = gfwlistcheck.GfwList()
    hosts = [
        ('ftchinese.com', True),
        ('www.qq.com', False),
        ('share.dmhy.org', True),
        ('t66y.com', True),
    ]

    for host, r in hosts:
        assert gfwlist.check(host) == r


if __name__ == '__main__':
    test_GfwList_check()