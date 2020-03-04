import logging
import mechanicalsoup

from systemd.journal import JournalHandler


logger = logging.getLogger('goSecure')
journald_handler = JournalHandler()
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] [+] %(message)s'
))
logger.addHandler(journald_handler)


def captive_portal(wifi_ssid, cp_username, cp_password):
    logger.debug('called captive_portal()')
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
    logger.debug('called cp_starbucks()')
    try:
        r = browser.open('http://www.google.com')
        html = r.read()
        browser.select_form(nr=0)
        browser.submit()
        response = browser.response().read()
        for line in response:
            logger.debug(line)
        return True
    except:
        return False
