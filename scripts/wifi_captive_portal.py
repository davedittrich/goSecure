import mechanicalsoup


def captive_portal(wifi_ssid, cp_username, cp_password):
    br = mechanicalsoup.Browser(
        soup_config={'features', 'lxml'},
        raise_on_404=True,
        user_agent='Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'
    )

    #browser.set_handle_equiv(True)
    #browser.set_handle_gzip(True)
    #browser.set_handle_redirect(True)
    #browser.set_handle_referer(True)
    #browser.set_handle_robots(False)

    #browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    #browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    return wifi_ssid == "Google Starbucks" and cp_starbucks(br)


def cp_starbucks(br):
    try:
        r = browser.open('http://www.google.com')
        html = r.read()

        browser.select_form(nr=0)

        browser.submit()
        # print browser.response().read()
        return True

    except:
        return False
